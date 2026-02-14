"""PostgreSQL Graph Storage implementation using Apache AGE."""

import json
import re
from dataclasses import dataclass
from typing import Any
from typing import final

import asyncpg
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from lightrag.base import BaseGraphStorage
from lightrag.core_types import KnowledgeGraph, KnowledgeGraphEdge, KnowledgeGraphNode
from lightrag.kg.postgres.connection import ClientManager, PostgreSQLDB, _dollar_quote
from lightrag.utils import logger


def _get_shared_storage():
    from lightrag.kg.shared_storage import get_data_init_lock

    return get_data_init_lock


class PGGraphQueryException(Exception):
    """Exception for the AGE queries."""

    def __init__(self, exception: str | dict[str, Any]) -> None:
        if isinstance(exception, dict):
            self.message = exception["message"] if "message" in exception else "unknown"
            self.details = exception["details"] if "details" in exception else "unknown"
        else:
            self.message = exception
            self.details = "unknown"

    def get_message(self) -> str:
        return self.message

    def get_details(self) -> Any:
        return self.details


@final
@dataclass
class PGGraphStorage(BaseGraphStorage):
    def __post_init__(self):
        self.db: PostgreSQLDB | None = None

    def _get_workspace_graph_name(self) -> str:
        """
        Generate graph name based on workspace and namespace for data isolation.
        Rules:
        - If workspace is empty or "default": graph_name = namespace
        - If workspace has other value: graph_name = workspace_namespace

        Args:
            None

        Returns:
            str: The graph name for the current workspace
        """
        workspace = self.workspace
        namespace = self.namespace

        if workspace and workspace.strip() and workspace.strip().lower() != "default":
            safe_workspace = re.sub(r"[^a-zA-Z0-9_]", "_", workspace.strip())
            safe_namespace = re.sub(r"[^a-zA-Z0-9_]", "_", namespace)
            return f"{safe_workspace}_{safe_namespace}"
        else:
            return re.sub(r"[^a-zA-Z0-9_]", "_", namespace)

    @staticmethod
    def _normalize_node_id(node_id: str) -> str:
        """
        Normalize node ID to ensure special characters are properly handled in Cypher queries.

        Args:
            node_id: The original node ID

        Returns:
            Normalized node ID suitable for Cypher queries
        """
        normalized_id = node_id
        normalized_id = normalized_id.replace("\\", "\\\\")
        normalized_id = normalized_id.replace('"', '\\"')
        return normalized_id

    async def initialize(self):
        from lightrag.kg.postgres import ClientManager, PostgreSQLDB

        get_data_init_lock = _get_shared_storage()

        async with get_data_init_lock():
            if self.db is None:
                self.db = await ClientManager.get_client()

            if self.db.workspace:
                logger.info(
                    f"Using PG_WORKSPACE environment variable: '{self.db.workspace}' (overriding '{self.workspace}/{self.namespace}')"
                )
                self.workspace = self.db.workspace
            elif hasattr(self, "workspace") and self.workspace:
                pass
            else:
                self.workspace = "default"

            self.graph_name = self._get_workspace_graph_name()

            logger.info(
                f"[{self.workspace}] PostgreSQL Graph initialized: graph_name='{self.graph_name}'"
            )

            async with self.db.pool.acquire() as connection:
                await PostgreSQLDB.configure_age_extension(connection)

            queries = [
                f"SELECT create_graph('{self.graph_name}')",
                f"SELECT create_vlabel('{self.graph_name}', 'base');",
                f"SELECT create_elabel('{self.graph_name}', 'DIRECTED');",
                f'CREATE INDEX CONCURRENTLY vertex_idx_node_id ON {self.graph_name}."_ag_label_vertex" (ag_catalog.agtype_access_operator(properties, \'"entity_id"\'::agtype))',
                f'CREATE INDEX CONCURRENTLY edge_sid_idx ON {self.graph_name}."_ag_label_edge" (start_id)',
                f'CREATE INDEX CONCURRENTLY edge_eid_idx ON {self.graph_name}."_ag_label_edge" (end_id)',
                f'CREATE INDEX CONCURRENTLY edge_seid_idx ON {self.graph_name}."_ag_label_edge" (start_id,end_id)',
                f'CREATE INDEX CONCURRENTLY directed_p_idx ON {self.graph_name}."DIRECTED" (id)',
                f'CREATE INDEX CONCURRENTLY directed_eid_idx ON {self.graph_name}."DIRECTED" (end_id)',
                f'CREATE INDEX CONCURRENTLY directed_sid_idx ON {self.graph_name}."DIRECTED" (start_id)',
                f'CREATE INDEX CONCURRENTLY directed_seid_idx ON {self.graph_name}."DIRECTED" (start_id,end_id)',
                f'CREATE INDEX CONCURRENTLY entity_p_idx ON {self.graph_name}."base" (id)',
                f'CREATE INDEX CONCURRENTLY entity_idx_node_id ON {self.graph_name}."base" (ag_catalog.agtype_access_operator(properties, \'"entity_id"\'::agtype))',
                f'CREATE INDEX CONCURRENTLY entity_node_id_gin_idx ON {self.graph_name}."base" using gin(properties)',
                f'ALTER TABLE {self.graph_name}."DIRECTED" CLUSTER ON directed_sid_idx',
            ]

            for query in queries:
                await self.db.execute(
                    query,
                    upsert=True,
                    ignore_if_exists=True,
                    with_age=True,
                    graph_name=self.graph_name,
                )

    async def finalize(self):
        from lightrag.kg.postgres import ClientManager

        if self.db is not None:
            await ClientManager.release_client(self.db)
            self.db = None

    async def index_done_callback(self) -> None:
        pass

    @staticmethod
    def _record_to_dict(record: asyncpg.Record) -> dict[str, Any]:
        """
        Convert a record returned from an age query to a dictionary

        Args:
            record (): a record from an age query result

        Returns:
            dict[str, Any]: a dictionary representation of the record where
                the dictionary key is the field name and the value is the
                value converted to a python type
        """

        @staticmethod
        def parse_agtype_string(agtype_str: str) -> tuple[str, str]:
            """
            Parse agtype string precisely, separating JSON content and type identifier

            Args:
                agtype_str: String like '{"json": "content"}::vertex'

            Returns:
                (json_content, type_identifier)
            """
            if not isinstance(agtype_str, str) or "::" not in agtype_str:
                return agtype_str, ""

            last_double_colon = agtype_str.rfind("::")

            if last_double_colon == -1:
                return agtype_str, ""

            json_content = agtype_str[:last_double_colon]
            type_identifier = agtype_str[last_double_colon + 2 :]

            return json_content, type_identifier

        @staticmethod
        def safe_json_parse(json_str: str, context: str = "") -> dict:
            """
            Safe JSON parsing with simplified error logging
            """
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing failed ({context}): {e}")
                logger.error(f"Raw data (first 100 chars): {repr(json_str[:100])}")
                logger.error(f"Error position: line {e.lineno}, column {e.colno}")
                return None

        d = {}

        vertices = {}

        for k in record.keys():
            v = record[k]
            if isinstance(v, str) and "::" in v:
                if v.startswith("[") and v.endswith("]"):
                    json_content, type_id = parse_agtype_string(v)
                    if type_id == "vertex":
                        vertexes = safe_json_parse(
                            json_content, f"vertices array for {k}"
                        )
                        if vertexes:
                            for vertex in vertexes:
                                vertices[vertex["id"]] = vertex.get("properties")
                else:
                    json_content, type_id = parse_agtype_string(v)
                    if type_id == "vertex":
                        vertex = safe_json_parse(json_content, f"single vertex for {k}")
                        if vertex:
                            vertices[vertex["id"]] = vertex.get("properties")

        for k in record.keys():
            v = record[k]
            if isinstance(v, str) and "::" in v:
                if v.startswith("[") and v.endswith("]"):
                    json_content, type_id = parse_agtype_string(v)
                    if type_id == "edge":
                        edges = safe_json_parse(json_content, f"edges array for {k}")
                        if edges:
                            for edge in edges:
                                edge_start = edge.get("start_id")
                                edge_end = edge.get("end_id")
                                d[k] = {
                                    "start_node": vertices.get(edge_start),
                                    "end_node": vertices.get(edge_end),
                                    "edge": edge.get("properties"),
                                }
                else:
                    json_content, type_id = parse_agtype_string(v)
                    if type_id == "edge":
                        edge = safe_json_parse(json_content, f"single edge for {k}")
                        if edge:
                            edge_start = edge.get("start_id")
                            edge_end = edge.get("end_id")
                            d[k] = {
                                "start_node": vertices.get(edge_start),
                                "end_node": vertices.get(edge_end),
                                "edge": edge.get("properties"),
                            }
            else:
                d[k] = v

        return d

    @staticmethod
    def _format_properties(properties: dict[str, Any], _id: str | None = None) -> str:
        """
        Convert a dictionary of properties to a string representation that
        can be used in a cypher query insert/merge statement.

        Args:
            properties (dict[str,str]): a dictionary containing node/edge properties
            _id (Union[str, None]): the id of the node or None if none exists

        Returns:
            str: the properties dictionary as a properly formatted string
        """
        props = []
        for k, v in properties.items():
            prop = f"`{k}`: {json.dumps(v)}"
            props.append(prop)
        if _id is not None and "id" not in properties:
            props.append(
                f"id: {json.dumps(_id)}" if isinstance(_id, str) else f"id: {_id}"
            )
        return "{" + ", ".join(props) + "}"

    async def _query(
        self,
        query: str,
        readonly: bool = True,
        upsert: bool = False,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Query the graph by taking a cypher query, converting it to an
        age compatible query, executing it and converting the result

        Args:
            query (str): a cypher query to be executed

        Returns:
            list[dict[str, Any]]: a list of dictionaries containing the result set
        """
        try:
            if readonly:
                data = await self.db.query(
                    query,
                    list(params.values()) if params else None,
                    multirows=True,
                    with_age=True,
                    graph_name=self.graph_name,
                )
            else:
                data = await self.db.execute(
                    query,
                    upsert=upsert,
                    with_age=True,
                    graph_name=self.graph_name,
                )

        except Exception as e:
            raise PGGraphQueryException(
                {
                    "message": f"Error executing graph query: {query}",
                    "wrapped": query,
                    "detail": repr(e),
                    "error_type": e.__class__.__name__,
                }
            ) from e

        if data is None:
            result = []
        else:
            result = [self._record_to_dict(d) for d in data]

        return result

    async def has_node(self, node_id: str) -> bool:
        query = f"""
            SELECT EXISTS (
              SELECT 1
              FROM {self.graph_name}.base
              WHERE ag_catalog.agtype_access_operator(
                      VARIADIC ARRAY[properties, '"entity_id"'::agtype]
                    ) = (to_json($1::text)::text)::agtype
              LIMIT 1
            ) AS node_exists;
        """

        params = {"node_id": node_id}
        row = (await self._query(query, params=params))[0]
        return bool(row["node_exists"])

    async def has_edge(self, source_node_id: str, target_node_id: str) -> bool:
        query = f"""
            WITH a AS (
              SELECT id AS vid
              FROM {self.graph_name}.base
              WHERE ag_catalog.agtype_access_operator(
                      VARIADIC ARRAY[properties, '"entity_id"'::agtype]
                    ) = (to_json($1::text)::text)::agtype
            ),
            b AS (
              SELECT id AS vid
              FROM {self.graph_name}.base
              WHERE ag_catalog.agtype_access_operator(
                      VARIADIC ARRAY[properties, '"entity_id"'::agtype]
                    ) = (to_json($2::text)::text)::agtype
            )
            SELECT EXISTS (
              SELECT 1
              FROM {self.graph_name}."DIRECTED" d
              JOIN a ON d.start_id = a.vid
              JOIN b ON d.end_id   = b.vid
              LIMIT 1
            )
            OR EXISTS (
              SELECT 1
              FROM {self.graph_name}."DIRECTED" d
              JOIN a ON d.end_id   = a.vid
              JOIN b ON d.start_id = b.vid
              LIMIT 1
            ) AS edge_exists;
        """
        params = {
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
        }
        row = (await self._query(query, params=params))[0]
        return bool(row["edge_exists"])

    async def get_node(self, node_id: str) -> dict[str, str] | None:
        """Get node by its label identifier, return only node properties"""

        result = await self.get_nodes_batch(node_ids=[node_id])
        if result and node_id in result:
            return result[node_id]
        return None

    async def node_degree(self, node_id: str) -> int:
        result = await self.node_degrees_batch(node_ids=[node_id])
        if result and node_id in result:
            return result[node_id]

    async def edge_degree(self, src_id: str, tgt_id: str) -> int:
        result = await self.edge_degrees_batch(edges=[(src_id, tgt_id)])
        if result and (src_id, tgt_id) in result:
            return result[(src_id, tgt_id)]

    async def get_edge(
        self, source_node_id: str, target_node_id: str
    ) -> dict[str, str] | None:
        """Get edge properties between two nodes"""
        result = await self.get_edges_batch(
            [{"src": source_node_id, "tgt": target_node_id}]
        )
        if result and (source_node_id, target_node_id) in result:
            return result[(source_node_id, target_node_id)]
        return None

    async def get_node_edges(self, source_node_id: str) -> list[tuple[str, str]] | None:
        """
        Retrieves all edges (relationships) for a particular node identified by its label.
        :return: list of dictionaries containing edge information
        """
        label = self._normalize_node_id(source_node_id)

        cypher_query = f"""MATCH (n:base {{entity_id: "{label}"}})
                      OPTIONAL MATCH (n)-[]-(connected:base)
                      RETURN n.entity_id AS source_id, connected.entity_id AS connected_id"""

        _dollar_quote = _dollar_quote
        query = f"SELECT * FROM cypher({_dollar_quote(self.graph_name)}, {_dollar_quote(cypher_query)}) AS (source_id text, connected_id text)"

        results = await self._query(query)
        edges = []
        for record in results:
            source_id = record["source_id"]
            connected_id = record["connected_id"]

            if source_id and connected_id:
                edges.append((source_id, connected_id))

        return edges

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((PGGraphQueryException,)),
    )
    async def upsert_node(self, node_id: str, node_data: dict[str, str]) -> None:
        """
        Upsert a node in the Neo4j database.

        Args:
            node_id: The unique identifier for the node (used as label)
            node_data: Dictionary of node properties
        """
        if "entity_id" not in node_data:
            raise ValueError(
                "PostgreSQL: node properties must contain an 'entity_id' field"
            )

        label = self._normalize_node_id(node_id)
        properties = self._format_properties(node_data)

        cypher_query = f"""MERGE (n:base {{entity_id: "{label}"}})
                     SET n += {properties}
                     RETURN n"""

        _dollar_quote = _dollar_quote
        query = f"SELECT * FROM cypher({_dollar_quote(self.graph_name)}, {_dollar_quote(cypher_query)}) AS (n agtype)"

        try:
            await self._query(query, readonly=False, upsert=True)

        except Exception:
            logger.error(
                f"[{self.workspace}] POSTGRES, upsert_node error on node_id: `{node_id}`"
            )
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((PGGraphQueryException,)),
    )
    async def upsert_edge(
        self, source_node_id: str, target_node_id: str, edge_data: dict[str, str]
    ) -> None:
        """
        Upsert an edge and its properties between two nodes identified by their labels.

        Args:
            source_node_id (str): Label of the source node (used as identifier)
            target_node_id (str): Label of the target node (used as identifier)
            edge_data (dict): dictionary of properties to set on the edge
        """
        src_label = self._normalize_node_id(source_node_id)
        tgt_label = self._normalize_node_id(target_node_id)
        edge_properties = self._format_properties(edge_data)

        cypher_query = f"""MATCH (source:base {{entity_id: "{src_label}"}})
                     WITH source
                     MATCH (target:base {{entity_id: "{tgt_label}"}})
                     MERGE (source)-[r:DIRECTED]-(target)
                     SET r += {edge_properties}
                     SET r += {edge_properties}
                     RETURN r"""

        _dollar_quote = _dollar_quote
        query = f"SELECT * FROM cypher({_dollar_quote(self.graph_name)}, {_dollar_quote(cypher_query)}) AS (r agtype)"

        try:
            await self._query(query, readonly=False, upsert=True)

        except Exception:
            logger.error(
                f"[{self.workspace}] POSTGRES, upsert_edge error on edge: `{source_node_id}`-`{target_node_id}`"
            )
            raise

    async def delete_node(self, node_id: str) -> None:
        """
        Delete a node from the graph.

        Args:
            node_id (str): The ID of the node to delete.
        """
        label = self._normalize_node_id(node_id)

        cypher_query = f"""MATCH (n:base {{entity_id: "{label}"}})
                     DETACH DELETE n"""

        _dollar_quote = _dollar_quote
        query = f"SELECT * FROM cypher({_dollar_quote(self.graph_name)}, {_dollar_quote(cypher_query)}) AS (n agtype)"

        try:
            await self._query(query, readonly=False)
        except Exception as e:
            logger.error(f"[{self.workspace}] Error during node deletion: {e}")
            raise

    async def remove_nodes(self, node_ids: list[str]) -> None:
        """
        Remove multiple nodes from the graph.

        Args:
            node_ids (list[str]): A list of node IDs to remove.
        """
        node_ids_normalized = [self._normalize_node_id(node_id) for node_id in node_ids]
        node_id_list = ", ".join([f'"{node_id}"' for node_id in node_ids_normalized])

        cypher_query = f"""MATCH (n:base)
                     WHERE n.entity_id IN [{node_id_list}]
                     DETACH DELETE n"""

        _dollar_quote = _dollar_quote
        query = f"SELECT * FROM cypher({_dollar_quote(self.graph_name)}, {_dollar_quote(cypher_query)}) AS (n agtype)"

        try:
            await self._query(query, readonly=False)
        except Exception as e:
            logger.error(f"[{self.workspace}] Error during node removal: {e}")
            raise

    async def remove_edges(self, edges: list[tuple[str, str]]) -> None:
        """
        Remove multiple edges from the graph.

        Args:
            edges (list[tuple[str, str]]): A list of edges to remove, where each edge is a tuple of (source_node_id, target_node_id).
        """
        for source, target in edges:
            src_label = self._normalize_node_id(source)
            tgt_label = self._normalize_node_id(target)

            cypher_query = f"""MATCH (a:base {{entity_id: "{src_label}"}})-[r]-(b:base {{entity_id: "{tgt_label}"}})
                         DELETE r"""

            _dollar_quote = _dollar_quote
            query = f"SELECT * FROM cypher({_dollar_quote(self.graph_name)}, {_dollar_quote(cypher_query)}) AS (r agtype)"

            try:
                await self._query(query, readonly=False)
                logger.debug(
                    f"[{self.workspace}] Deleted edge from '{source}' to '{target}'"
                )
            except Exception as e:
                logger.error(f"[{self.workspace}] Error during edge deletion: {str(e)}")
                raise

    async def get_nodes_batch(
        self, node_ids: list[str], batch_size: int = 1000
    ) -> dict[str, dict]:
        """
        Retrieve multiple nodes in one query using UNWIND.

        Args:
            node_ids: List of node entity IDs to fetch.
            batch_size: Batch size for the query

        Returns:
            A dictionary mapping each node_id to its node data (or None if not found).
        """
        if not node_ids:
            return {}

        seen: set[str] = set()
        unique_ids: list[str] = []
        lookup: dict[str, str] = {}
        requested: set[str] = set()
        for nid in node_ids:
            if nid not in seen:
                seen.add(nid)
                unique_ids.append(nid)
            requested.add(nid)
            lookup[nid] = nid
            lookup[self._normalize_node_id(nid)] = nid

        nodes_dict = {}

        for i in range(0, len(unique_ids), batch_size):
            batch = unique_ids[i : i + batch_size]

            query = f"""
                WITH input(v, ord) AS (
                  SELECT v, ord
                  FROM unnest($1::text[]) WITH ORDINALITY AS t(v, ord)
                ),
                ids(node_id, ord) AS (
                  SELECT (to_json(v)::text)::agtype AS node_id, ord
                  FROM input
                )
                SELECT i.node_id::text AS node_id,
                       b.properties
                FROM {self.graph_name}.base AS b
                JOIN ids i
                  ON ag_catalog.agtype_access_operator(
                       VARIADIC ARRAY[b.properties, '"entity_id"'::agtype]
                     ) = i.node_id
                ORDER BY i.ord;
            """

            results = await self._query(query, params={"ids": batch})

            for result in results:
                if result["node_id"] and result["properties"]:
                    node_dict = result["properties"]

                    if isinstance(node_dict, str):
                        try:
                            node_dict = json.loads(node_dict)
                        except json.JSONDecodeError:
                            logger.warning(
                                f"[{self.workspace}] Failed to parse node string in batch: {node_dict}"
                            )

                    node_key = result["node_id"]
                    original_key = lookup.get(node_key)
                    if original_key is None:
                        logger.warning(
                            f"[{self.workspace}] Node {node_key} not found in lookup map"
                        )
                        original_key = node_key
                    if original_key in requested:
                        nodes_dict[original_key] = node_dict

        return nodes_dict

    async def node_degrees_batch(
        self, node_ids: list[str], batch_size: int = 500
    ) -> dict[str, int]:
        """
        Retrieve the degree for multiple nodes in a single query using UNWIND.
        Calculates the total degree by counting distinct relationships.
        Uses separate queries for outgoing and incoming edges.

        Args:
            node_ids: List of node labels (entity_id values) to look up.
            batch_size: Batch size for the query

        Returns:
            A dictionary mapping each node_id to its degree (total number of relationships).
            If a node is not found, its degree will be set to 0.
        """
        if not node_ids:
            return {}

        seen: set[str] = set()
        unique_ids: list[str] = []
        lookup: dict[str, str] = {}
        requested: set[str] = set()
        for nid in node_ids:
            if nid not in seen:
                seen.add(nid)
                unique_ids.append(nid)
            requested.add(nid)
            lookup[nid] = nid
            lookup[self._normalize_node_id(nid)] = nid

        out_degrees = {}
        in_degrees = {}

        for i in range(0, len(unique_ids), batch_size):
            batch = unique_ids[i : i + batch_size]

            query = f"""
                    WITH input(v, ord) AS (
                      SELECT v, ord
                      FROM unnest($1::text[]) WITH ORDINALITY AS t(v, ord)
                    ),
                    ids(node_id, ord) AS (
                      SELECT (to_json(v)::text)::agtype AS node_id, ord
                      FROM input
                    ),
                    vids AS (
                      SELECT b.id AS vid, i.node_id, i.ord
                      FROM {self.graph_name}.base AS b
                      JOIN ids i
                        ON ag_catalog.agtype_access_operator(
                             VARIADIC ARRAY[b.properties, '"entity_id"'::agtype]
                           ) = i.node_id
                    ),
                    deg_out AS (
                      SELECT d.start_id AS vid, COUNT(*)::bigint AS out_degree
                      FROM {self.graph_name}."DIRECTED" AS d
                      JOIN vids v ON v.vid = d.start_id
                      GROUP BY d.start_id
                    ),
                    deg_in AS (
                      SELECT d.end_id AS vid, COUNT(*)::bigint AS in_degree
                      FROM {self.graph_name}."DIRECTED" AS d
                      JOIN vids v ON v.vid = d.end_id
                      GROUP BY d.end_id
                    )
                    SELECT v.node_id::text AS node_id,
                           COALESCE(o.out_degree, 0) AS out_degree,
                           COALESCE(n.in_degree, 0)  AS in_degree
                    FROM vids v
                    LEFT JOIN deg_out o ON o.vid = v.vid
                    LEFT JOIN deg_in  n ON n.vid = v.vid
                    ORDER BY v.ord;
                """

            combined_results = await self._query(query, params={"ids": batch})

            for row in combined_results:
                node_id = row["node_id"]
                if not node_id:
                    continue
                node_key = node_id
                original_key = lookup.get(node_key)
                if original_key is None:
                    logger.warning(
                        f"[{self.workspace}] Node {node_key} not found in lookup map"
                    )
                    original_key = node_key
                if original_key in requested:
                    out_degrees[original_key] = int(row.get("out_degree", 0) or 0)
                    in_degrees[original_key] = int(row.get("in_degree", 0) or 0)

        degrees_dict = {}
        for node_id in node_ids:
            out_degree = out_degrees.get(node_id, 0)
            in_degree = in_degrees.get(node_id, 0)
            degrees_dict[node_id] = out_degree + in_degree

        return degrees_dict

    async def edge_degrees_batch(
        self, edges: list[tuple[str, str]]
    ) -> dict[tuple[str, str], int]:
        """
        Calculate the combined degree for each edge (sum of the source and target node degrees)
        in batch using the already implemented node_degrees_batch.

        Args:
            edges: List of (source_node_id, target_node_id) tuples

        Returns:
            Dictionary mapping edge tuples to their combined degrees
        """
        if not edges:
            return {}

        all_nodes = set()
        for src, tgt in edges:
            all_nodes.add(src)
            all_nodes.add(tgt)

        node_degrees = await self.node_degrees_batch(list(all_nodes))

        edge_degrees_dict = {}
        for src, tgt in edges:
            src_degree = node_degrees.get(src, 0)
            tgt_degree = node_degrees.get(tgt, 0)
            edge_degrees_dict[(src, tgt)] = src_degree + tgt_degree

        return edge_degrees_dict

    async def get_edges_batch(
        self, pairs: list[dict[str, str]], batch_size: int = 500
    ) -> dict[tuple[str, str], dict]:
        """
        Retrieve edge properties for multiple (src, tgt) pairs in one query.
        Get forward and backward edges seperately and merge them before return

        Args:
            pairs: List of dictionaries, e.g. [{"src": "node1", "tgt": "node2"}, ...]
            batch_size: Batch size for the query

        Returns:
            A dictionary mapping (src, tgt) tuples to their edge properties.
        """
        if not pairs:
            return {}

        seen = set()
        uniq_pairs: list[dict[str, str]] = []
        for p in pairs:
            s = self._normalize_node_id(p["src"])
            t = self._normalize_node_id(p["tgt"])
            key = (s, t)
            if s and t and key not in seen:
                seen.add(key)
                uniq_pairs.append(p)

        edges_dict: dict[tuple[str, str], dict] = {}

        for i in range(0, len(uniq_pairs), batch_size):
            batch = uniq_pairs[i : i + batch_size]

            pairs_list = [{"src": p["src"], "tgt": p["tgt"]} for p in batch]

            forward_cypher = """
                         UNWIND $pairs AS p
                         WITH p.src AS src_eid, p.tgt AS tgt_eid
                         MATCH (a:base {entity_id: src_eid})
                         MATCH (b:base {entity_id: tgt_eid})
                         MATCH (a)-[r]->(b)
                         RETURN src_eid AS source, tgt_eid AS target, properties(r) AS edge_properties"""
            backward_cypher = """
                         UNWIND $pairs AS p
                         WITH p.src AS src_eid, p.tgt AS tgt_eid
                         MATCH (a:base {entity_id: src_eid})
                         MATCH (b:base {entity_id: tgt_eid})
                         MATCH (a)<-[r]-(b)
                         RETURN src_eid AS source, tgt_eid AS target, properties(r) AS edge_properties"""

            _dollar_quote = _dollar_quote
            sql_fwd = f"""
            SELECT * FROM cypher({_dollar_quote(self.graph_name)}::name,
                                 {_dollar_quote(forward_cypher)}::cstring,
                                 $1::agtype)
              AS (source text, target text, edge_properties agtype)
            """

            sql_bwd = f"""
            SELECT * FROM cypher({_dollar_quote(self.graph_name)}::name,
                                 {_dollar_quote(backward_cypher)}::cstring,
                                 $1::agtype)
              AS (source text, target text, edge_properties agtype)
            """

            pg_params = {
                "params": json.dumps({"pairs": pairs_list}, ensure_ascii=False)
            }

            forward_results = await self._query(sql_fwd, params=pg_params)
            backward_results = await self._query(sql_bwd, params=pg_params)

            for result in forward_results:
                if result["source"] and result["target"] and result["edge_properties"]:
                    edge_props = result["edge_properties"]

                    if isinstance(edge_props, str):
                        try:
                            edge_props = json.loads(edge_props)
                        except json.JSONDecodeError:
                            logger.warning(
                                f"[{self.workspace}]Failed to parse edge properties string: {edge_props}"
                            )
                            continue

                    edges_dict[(result["source"], result["target"])] = edge_props

            for result in backward_results:
                if result["source"] and result["target"] and result["edge_properties"]:
                    edge_props = result["edge_properties"]

                    if isinstance(edge_props, str):
                        try:
                            edge_props = json.loads(edge_props)
                        except json.JSONDecodeError:
                            logger.warning(
                                f"[{self.workspace}] Failed to parse edge properties string: {edge_props}"
                            )
                            continue

                    edges_dict[(result["source"], result["target"])] = edge_props

        return edges_dict

    async def get_nodes_edges_batch(
        self, node_ids: list[str], batch_size: int = 500
    ) -> dict[str, list[tuple[str, str]]]:
        """
        Get all edges (both outgoing and incoming) for multiple nodes in a single batch operation.

        Args:
            node_ids: List of node IDs to get edges for
            batch_size: Batch size for the query

        Returns:
            Dictionary mapping node IDs to lists of (source, target) edge tuples
        """
        if not node_ids:
            return {}

        seen = set()
        unique_ids: list[str] = []
        for nid in node_ids:
            n = self._normalize_node_id(nid)
            if n and n not in seen:
                seen.add(n)
                unique_ids.append(n)

        edges_norm: dict[str, list[tuple[str, str]]] = {n: [] for n in unique_ids}

        for i in range(0, len(unique_ids), batch_size):
            batch = unique_ids[i : i + batch_size]
            formatted_ids = ", ".join([f'"{n}"' for n in batch])

            outgoing_cypher = f"""UNWIND [{formatted_ids}] AS node_id
                         MATCH (n:base {{entity_id: node_id}})
                         OPTIONAL MATCH (n:base)-[]->(connected:base)
                         RETURN node_id, connected.entity_id AS connected_id"""

            incoming_cypher = f"""UNWIND [{formatted_ids}] AS node_id
                         MATCH (n:base {{entity_id: node_id}})
                         OPTIONAL MATCH (n:base)<-[]-(connected:base)
                         RETURN node_id, connected.entity_id AS connected_id"""

            _dollar_quote = _dollar_quote
            outgoing_query = f"SELECT * FROM cypher({_dollar_quote(self.graph_name)}, {_dollar_quote(outgoing_cypher)}) AS (node_id text, connected_id text)"
            incoming_query = f"SELECT * FROM cypher({_dollar_quote(self.graph_name)}, {_dollar_quote(incoming_cypher)}) AS (node_id text, connected_id text)"

            outgoing_results = await self._query(outgoing_query)
            incoming_results = await self._query(incoming_query)

            for result in outgoing_results:
                if result["node_id"] and result["connected_id"]:
                    edges_norm[result["node_id"]].append(
                        (result["node_id"], result["connected_id"])
                    )

            for result in incoming_results:
                if result["node_id"] and result["connected_id"]:
                    edges_norm[result["node_id"]].append(
                        (result["connected_id"], result["node_id"])
                    )

        out: dict[str, list[tuple[str, str]]] = {}
        for orig in node_ids:
            n = self._normalize_node_id(orig)
            out[orig] = edges_norm.get(n, [])

        return out

    async def get_all_labels(self) -> list[str]:
        """
        Get all labels (node IDs) in the graph.

        Returns:
            list[str]: A list of all labels in the graph.
        """
        query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                     MATCH (n:base)
                     WHERE n.entity_id IS NOT NULL
                     RETURN DISTINCT n.entity_id AS label
                     ORDER BY n.entity_id
                   $$) AS (label text)"""

        results = await self._query(query)
        labels = []
        for result in results:
            if result and isinstance(result, dict) and "label" in result:
                labels.append(result["label"])
        return labels

    async def _bfs_subgraph(
        self, node_label: str, max_depth: int, max_nodes: int
    ) -> KnowledgeGraph:
        """
        Implements a true breadth-first search algorithm for subgraph retrieval.
        This method is used as a fallback when the standard Cypher query is too slow
        or when we need to guarantee BFS ordering.

        Args:
            node_label: Label of the starting node
            max_depth: Maximum depth of the subgraph
            max_nodes: Maximum number of nodes to return

        Returns:
            KnowledgeGraph object containing nodes and edges
        """
        from collections import deque

        result = KnowledgeGraph()
        visited_nodes = set()
        visited_node_ids = set()
        visited_edges = set()
        visited_edge_pairs = set()

        label = self._normalize_node_id(node_label)

        cypher_query = f"""MATCH (n:base {{entity_id: "{label}"}})
                    RETURN id(n) as node_id, n"""

        _dollar_quote = _dollar_quote
        query = f"SELECT * FROM cypher({_dollar_quote(self.graph_name)}, {_dollar_quote(cypher_query)}) AS (node_id bigint, n agtype)"

        node_result = await self._query(query)
        if not node_result or not node_result[0].get("n"):
            return result

        start_node_data = node_result[0]["n"]
        entity_id = start_node_data["properties"]["entity_id"]
        internal_id = str(start_node_data["id"])

        start_node = KnowledgeGraphNode(
            id=internal_id,
            labels=[entity_id],
            properties=start_node_data["properties"],
        )

        queue = deque([(start_node, 0)])

        visited_nodes.add(entity_id)
        visited_node_ids.add(internal_id)
        result.nodes.append(start_node)

        result.is_truncated = False

        while queue:
            current_level_nodes = []
            current_depth = None

            if queue:
                current_depth = queue[0][1]

            while queue and queue[0][1] == current_depth:
                node, depth = queue.popleft()
                if depth > max_depth:
                    continue
                current_level_nodes.append(node)

            if not current_level_nodes:
                continue

            if current_depth > max_depth:
                continue

            node_ids = [node.labels[0] for node in current_level_nodes]
            formatted_ids = ", ".join(
                [f'"{self._normalize_node_id(node_id)}"' for node_id in node_ids]
            )

            outgoing_cypher = f"""UNWIND [{formatted_ids}] AS node_id
                MATCH (n:base {{entity_id: node_id}})
                OPTIONAL MATCH (n)-[r]->(neighbor:base)
                RETURN node_id AS current_id,
                       id(n) AS current_internal_id,
                       id(neighbor) AS neighbor_internal_id,
                       neighbor.entity_id AS neighbor_id,
                       id(r) AS edge_id,
                       r,
                       neighbor,
                       true AS is_outgoing"""

            incoming_cypher = f"""UNWIND [{formatted_ids}] AS node_id
                MATCH (n:base {{entity_id: node_id}})
                OPTIONAL MATCH (n)<-[r]-(neighbor:base)
                RETURN node_id AS current_id,
                       id(n) AS current_internal_id,
                       id(neighbor) AS neighbor_internal_id,
                       neighbor.entity_id AS neighbor_id,
                       id(r) AS edge_id,
                       r,
                       neighbor,
                       false AS is_outgoing"""

            outgoing_query = f"SELECT * FROM cypher({_dollar_quote(self.graph_name)}, {_dollar_quote(outgoing_cypher)}) AS (current_id text, current_internal_id bigint, neighbor_internal_id bigint, neighbor_id text, edge_id bigint, r agtype, neighbor agtype, is_outgoing bool)"

            incoming_query = f"SELECT * FROM cypher({_dollar_quote(self.graph_name)}, {_dollar_quote(incoming_cypher)}) AS (current_id text, current_internal_id bigint, neighbor_internal_id bigint, neighbor_id text, edge_id bigint, r agtype, neighbor agtype, is_outgoing bool)"

            outgoing_results = await self._query(outgoing_query)
            incoming_results = await self._query(incoming_query)

            neighbors = outgoing_results + incoming_results

            node_map = {node.labels[0]: node for node in current_level_nodes}

            for record in neighbors:
                if not record.get("neighbor") or not record.get("r"):
                    continue

                current_entity_id = record["current_id"]
                current_node = node_map[current_entity_id]

                neighbor_entity_id = record["neighbor_id"]
                neighbor_internal_id = str(record["neighbor_internal_id"])
                is_outgoing = record["is_outgoing"]

                if is_outgoing:
                    source_id = current_node.id
                    target_id = neighbor_internal_id
                else:
                    source_id = neighbor_internal_id
                    target_id = current_node.id

                if not neighbor_entity_id:
                    continue

                b_node = record["neighbor"]
                rel = record["r"]
                edge_id = str(record["edge_id"])

                neighbor_node = KnowledgeGraphNode(
                    id=neighbor_internal_id,
                    labels=[neighbor_entity_id],
                    properties=b_node["properties"],
                )

                sorted_pair = tuple(sorted([current_entity_id, neighbor_entity_id]))

                edge = KnowledgeGraphEdge(
                    id=edge_id,
                    type=rel["label"],
                    source=source_id,
                    target=target_id,
                    properties=rel["properties"],
                )

                if neighbor_internal_id in visited_node_ids:
                    if (
                        edge_id not in visited_edges
                        and sorted_pair not in visited_edge_pairs
                    ):
                        result.edges.append(edge)
                        visited_edges.add(edge_id)
                        visited_edge_pairs.add(sorted_pair)
                else:
                    if len(visited_node_ids) < max_nodes and current_depth < max_depth:
                        result.nodes.append(neighbor_node)
                        visited_nodes.add(neighbor_entity_id)
                        visited_node_ids.add(neighbor_internal_id)

                        queue.append((neighbor_node, current_depth + 1))

                        if (
                            edge_id not in visited_edges
                            and sorted_pair not in visited_edge_pairs
                        ):
                            result.edges.append(edge)
                            visited_edges.add(edge_id)
                            visited_edge_pairs.add(sorted_pair)
                    else:
                        if current_depth < max_depth:
                            result.is_truncated = True

        return result

    async def get_knowledge_graph(
        self,
        node_label: str,
        max_depth: int = 3,
        max_nodes: int = None,
    ) -> KnowledgeGraph:
        """
        Retrieve a connected subgraph of nodes where the label includes the specified `node_label`.

        Args:
            node_label: Label of the starting node, * means all nodes
            max_depth: Maximum depth of the subgraph, Defaults to 3
            max_nodes: Maximum nodes to return, Defaults to global_config max_graph_nodes

        Returns:
            KnowledgeGraph object containing nodes and edges, with an is_truncated flag
            indicating whether the graph was truncated due to max_nodes limit
        """
        if max_nodes is None:
            max_nodes = self.global_config.get("max_graph_nodes", 1000)
        else:
            max_nodes = min(max_nodes, self.global_config.get("max_graph_nodes", 1000))
        kg = KnowledgeGraph()

        if node_label == "*":
            count_query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                    MATCH (n:base)
                    RETURN count(distinct n) AS total_nodes
                    $$) AS (total_nodes bigint)"""

            count_result = await self._query(count_query)
            total_nodes = count_result[0]["total_nodes"] if count_result else 0
            is_truncated = total_nodes > max_nodes

            query_nodes = f"""SELECT * FROM cypher('{self.graph_name}', $$
                    MATCH (n:base)
                    OPTIONAL MATCH (n)-[r]->()
                    RETURN id(n) as node_id, count(r) as degree
                $$) AS (node_id BIGINT, degree BIGINT)
                ORDER BY degree DESC
                LIMIT {max_nodes}"""
            node_results = await self._query(query_nodes)

            node_ids = [str(result["node_id"]) for result in node_results]

            logger.info(
                f"[{self.workspace}] Total nodes: {total_nodes}, Selected nodes: {len(node_ids)}"
            )

            if node_ids:
                formatted_ids = ", ".join(node_ids)
                query = f"""SELECT * FROM cypher('{self.graph_name}', $$
                        WITH [{formatted_ids}] AS node_ids
                        MATCH (a)
                        WHERE id(a) IN node_ids
                        OPTIONAL MATCH (a)-[r]->(b)
                        WHERE id(b) IN node_ids
                        RETURN a, r, b
                    $$) AS (a agtype, r agtype, b agtype)"""

                results = await self._query(query)

                for row in results:
                    a = row.get("a")
                    r = row.get("r")
                    b = row.get("b")

                    if not a:
                        continue

                    a_props = a.get("properties", {}) if isinstance(a, dict) else {}
                    a_entity_id = a_props.get("entity_id")

                    if a_entity_id:
                        if not any(n.labels == [a_entity_id] for n in kg.nodes):
                            node = KnowledgeGraphNode(
                                id=str(a.get("id")),
                                labels=[a_entity_id],
                                properties=a_props,
                            )
                            kg.nodes.append(node)

                    if b:
                        b_props = b.get("properties", {}) if isinstance(b, dict) else {}
                        b_entity_id = b_props.get("entity_id")

                        if b_entity_id:
                            if not any(n.labels == [b_entity_id] for n in kg.nodes):
                                node = KnowledgeGraphNode(
                                    id=str(b.get("id")),
                                    labels=[b_entity_id],
                                    properties=b_props,
                                )
                                kg.nodes.append(node)

                    if r and a_entity_id and b_entity_id:
                        edge = KnowledgeGraphEdge(
                            id=str(r.get("id")),
                            type=r.get("label"),
                            source=str(a.get("id")),
                            target=str(b.get("id")),
                            properties=r.get("properties", {}),
                        )
                        kg.edges.append(edge)

                kg.is_truncated = is_truncated

            return kg

        label = self._normalize_node_id(node_label)

        cypher_query = f"""MATCH (a:base {{entity_id: "{label}"}})
                    OPTIONAL MATCH path = (a)-[r:DIRECTED*1..{max_depth}]->(b:base)
                    WITH a, r, b
                    WHERE r IS NOT NULL AND b IS NOT NULL
                    RETURN a, r, b
                    LIMIT {max_nodes}"""

        _dollar_quote = _dollar_quote
        query = f"SELECT * FROM cypher({_dollar_quote(self.graph_name)}, {_dollar_quote(cypher_query)}) AS (a agtype, r agtype, b agtype)"

        try:
            results = await self._query(query)
        except PGGraphQueryException:
            logger.warning(
                f"[{self.workspace}] Graph query failed, falling back to BFS"
            )
            return await self._bfs_subgraph(node_label, max_depth, max_nodes)

        nodes_set = set()
        for row in results:
            a = row.get("a")
            r = row.get("r")
            b = row.get("b")

            if not a:
                continue

            a_props = a.get("properties", {}) if isinstance(a, dict) else {}
            a_entity_id = a_props.get("entity_id")

            if a_entity_id and a_entity_id not in nodes_set:
                nodes_set.add(a_entity_id)
                node = KnowledgeGraphNode(
                    id=str(a.get("id")),
                    labels=[a_entity_id],
                    properties=a_props,
                )
                kg.nodes.append(node)

            if b:
                b_props = b.get("properties", {}) if isinstance(b, dict) else {}
                b_entity_id = b_props.get("entity_id")

                if b_entity_id and b_entity_id not in nodes_set:
                    nodes_set.add(b_entity_id)
                    node = KnowledgeGraphNode(
                        id=str(b.get("id")),
                        labels=[b_entity_id],
                        properties=b_props,
                    )
                    kg.nodes.append(node)

            if r:
                if isinstance(r, list):
                    for rel in r:
                        if a_entity_id and b_entity_id:
                            edge = KnowledgeGraphEdge(
                                id=str(rel.get("id")),
                                type=rel.get("label"),
                                source=str(a.get("id")),
                                target=str(b.get("id")),
                                properties=rel.get("properties", {}),
                            )
                            kg.edges.append(edge)
                else:
                    if a_entity_id and b_entity_id:
                        edge = KnowledgeGraphEdge(
                            id=str(r.get("id")),
                            type=r.get("label"),
                            source=str(a.get("id")),
                            target=str(b.get("id")),
                            properties=r.get("properties", {}),
                        )
                        kg.edges.append(edge)

        if len(kg.nodes) >= max_nodes:
            kg.is_truncated = True

        return kg

    async def get_nodes(
        self,
        entity_ids: list[str],
        reindex: bool = False,
        filters: dict | None = None,
    ) -> dict[str, KnowledgeGraphNode]:
        """Get nodes from the graph."""
        if not entity_ids:
            return {}

        nodes_data = await self.get_nodes_batch(entity_ids)
        result = {}
        for entity_id, node_data in nodes_data.items():
            result[entity_id] = KnowledgeGraphNode(
                entity_id=entity_id,
                entity_type=node_data.get("entity_type"),
                description=node_data.get("description"),
                source_id=node_data.get("source_id"),
                created_at=node_data.get("created_at"),
            )
        return result

    async def get_edges(
        self,
        relation_ids: list[tuple[str, str]],
        reindex: bool = False,
        filters: dict | None = None,
    ) -> dict[tuple[str, str], KnowledgeGraphEdge]:
        """Get edges from the graph."""
        if not relation_ids:
            return {}

        pairs = [{"src": src, "tgt": tgt} for src, tgt in relation_ids]
        edges_data = await self.get_edges_batch(pairs)

        result = {}
        for (src, tgt), edge_data in edges_data.items():
            result[(src, tgt)] = KnowledgeGraphEdge(
                src_id=src,
                tgt_id=tgt,
                weight=edge_data.get("weight"),
                description=edge_data.get("description"),
            )
        return result

    async def insert_nodes(
        self,
        nodes: list[KnowledgeGraphNode],
    ) -> None:
        """Insert nodes into the graph"""

        if not nodes:
            return

        for node in nodes:
            node_data = {
                "entity_id": node.entity_id,
                "entity_type": node.entity_type,
                "description": node.description,
                "source_id": node.source_id,
                "created_at": node.created_at,
            }
            await self.upsert_node(node.entity_id, node_data)

    async def insert_edges(
        self,
        edges: list[KnowledgeGraphEdge],
    ) -> None:
        """Insert edges into the graph"""

        if not edges:
            return

        for edge in edges:
            edge_data = {
                "weight": edge.weight,
                "description": edge.description,
            }
            await self.upsert_edge(edge.src_id, edge.tgt_id, edge_data)

    async def delete_nodes(
        self,
        entity_ids: list[str],
    ) -> None:
        """Delete nodes from the graph"""

        if not entity_ids:
            return

        await self.remove_nodes(entity_ids)

    async def delete_edges(
        self,
        relation_ids: list[tuple[str, str]],
    ) -> None:
        """Delete edges from the graph"""

        if not relation_ids:
            return

        await self.remove_edges(relation_ids)

    async def embed_nodes(
        self,
        node_properties: list[str] = ["entity_id", "description"],
        vector_size: int = 1024,
    ) -> None:
        """Embed nodes using LLM to generate vector representations for each node"""
        pass

    async def get_relocate(
        self,
        source_node: str,
        target_node: str,
    ) -> tuple[KnowledgeGraphNode, KnowledgeGraphNode] | None:
        """Get the from and to node for the given source and target node"""

        if not source_node and not target_node:
            return None

        source_data = await self.get_node(source_node)
        target_data = await self.get_node(target_node)

        if not source_data or not target_data:
            return None

        return (
            KnowledgeGraphNode(
                entity_id=source_node,
                entity_type=source_data.get("entity_type"),
                description=source_data.get("description"),
                source_id=source_data.get("source_id"),
                created_at=source_data.get("created_at"),
            ),
            KnowledgeGraphNode(
                entity_id=target_node,
                entity_type=target_data.get("entity_type"),
                description=target_data.get("description"),
                source_id=target_data.get("source_id"),
                created_at=target_data.get("created_at"),
            ),
        )

    async def get_triplets(
        self,
        source_node: str,
        target_node: str,
    ) -> list[tuple[KnowledgeGraphNode, KnowledgeGraphEdge, KnowledgeGraphNode]]:
        """Get all triplets for a given source and target node"""

        if not source_node and not target_node:
            return []

        source_data = await self.get_node(source_node)
        target_data = await self.get_node(target_node)

        if not source_data or not target_data:
            return []

        edge_data = await self.get_edge(source_node, target_node)

        if not edge_data:
            return []

        source_kg_node = KnowledgeGraphNode(
            entity_id=source_node,
            entity_type=source_data.get("entity_type"),
            description=source_data.get("description"),
            source_id=source_data.get("source_id"),
            created_at=source_data.get("created_at"),
        )

        target_kg_node = KnowledgeGraphNode(
            entity_id=target_node,
            entity_type=target_data.get("entity_type"),
            description=target_data.get("description"),
            source_id=target_data.get("source_id"),
            created_at=target_data.get("created_at"),
        )

        kg_edge = KnowledgeGraphEdge(
            src_id=source_node,
            tgt_id=target_node,
            weight=edge_data.get("weight"),
            description=edge_data.get("description"),
        )

        return [(source_kg_node, kg_edge, target_kg_node)]

    async def get_neighbors(
        self,
        entity_id: str,
        depth: int = 1,
        max_nodes: int | None = 100,
    ) -> list[tuple[KnowledgeGraphNode, KnowledgeGraphEdge]]:
        """Get all neighbors for a given node"""

        if not entity_id:
            return []

        edges = await self.get_node_edges(entity_id)

        if not edges:
            return []

        neighbors = []
        neighbor_ids = [tgt for src, tgt in edges if src == entity_id] + [
            src for src, tgt in edges if tgt == entity_id
        ]

        nodes_data = await self.get_nodes_batch(neighbor_ids[:max_nodes])

        for neighbor_id in neighbor_ids[:max_nodes]:
            node_data = nodes_data.get(neighbor_id)
            if node_data:
                neighbor_node = KnowledgeGraphNode(
                    entity_id=neighbor_id,
                    entity_type=node_data.get("entity_type"),
                    description=node_data.get("description"),
                    source_id=node_data.get("source_id"),
                    created_at=node_data.get("created_at"),
                )

                edge = KnowledgeGraphEdge(
                    src_id=entity_id,
                    tgt_id=neighbor_id,
                    weight=1.0,
                    description=None,
                )

                neighbors.append((neighbor_node, edge))

        return neighbors

    async def get_all_nodes(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[KnowledgeGraphNode]:
        """Get all nodes from the graph"""

        labels = await self.get_all_labels()
        nodes_data = await self.get_nodes_batch(labels[offset : offset + limit])

        nodes = []
        for entity_id, node_data in nodes_data.items():
            nodes.append(
                KnowledgeGraphNode(
                    entity_id=entity_id,
                    entity_type=node_data.get("entity_type"),
                    description=node_data.get("description"),
                    source_id=node_data.get("source_id"),
                    created_at=node_data.get("created_at"),
                )
            )

        return nodes

    async def get_all_edges(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[KnowledgeGraphEdge]:
        """Get all edges from the graph"""

        labels = await self.get_all_labels()
        all_edges = []

        for label in labels:
            edges = await self.get_node_edges(label)
            for src, tgt in edges:
                all_edges.append(
                    KnowledgeGraphEdge(
                        src_id=src,
                        tgt_id=tgt,
                        weight=1.0,
                        description=None,
                    )
                )

        return all_edges[offset : offset + limit]

    async def get_node_count(self) -> int:
        """Get the total number of nodes in the graph"""
        labels = await self.get_all_labels()
        return len(labels)

    async def get_edge_count(self) -> int:
        """Get the total number of edges in the graph"""
        labels = await self.get_all_labels()
        total_edges = 0

        for label in labels:
            edges = await self.get_node_edges(label)
            total_edges += len(edges)

        return total_edges

    async def is_empty(self) -> bool:
        """Check if the graph is empty"""
        node_count = await self.get_node_count()
        return node_count == 0

    async def clear(self) -> None:
        """Clear all nodes and edges from the graph"""
        labels = await self.get_all_labels()
        await self.remove_nodes(labels)
