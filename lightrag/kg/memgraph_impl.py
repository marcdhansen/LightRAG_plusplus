import asyncio
import configparser
import os
import random
import time
from dataclasses import dataclass
from typing import Any, final

import numpy as np
import pipmaster as pm

from ..base import BaseGraphStorage, BaseVectorStorage
from ..core_types import KnowledgeGraph, KnowledgeGraphEdge, KnowledgeGraphNode
from ..kg.shared_storage import get_data_init_lock
from ..utils import compute_mdhash_id, logger

if not pm.is_installed("neo4j"):
    pm.install("neo4j")
from dotenv import load_dotenv
from neo4j import (
    AsyncGraphDatabase,
    AsyncManagedTransaction,
)
from neo4j.exceptions import (
    ResultFailedError,
    TransientError,
)

# use the .env that is inside the current folder
load_dotenv(dotenv_path=".env", override=False)

MAX_GRAPH_NODES = int(os.getenv("MAX_GRAPH_NODES", 1000))

config = configparser.ConfigParser()
config.read("config.ini", "utf-8")


@final
@dataclass
class MemgraphStorage(BaseGraphStorage):
    def __init__(self, namespace, global_config, embedding_func, workspace=None):
        # Priority: 1) MEMGRAPH_WORKSPACE env 2) user arg 3) default 'base'
        memgraph_workspace = os.environ.get("MEMGRAPH_WORKSPACE")
        original_workspace = workspace  # Save original value for logging
        if memgraph_workspace and memgraph_workspace.strip():
            workspace = memgraph_workspace

        if not workspace or not str(workspace).strip():
            workspace = "base"

        super().__init__(
            namespace=namespace,
            workspace=workspace,
            global_config=global_config,
            embedding_func=embedding_func,
        )

        # Log after super().__init__() to ensure self.workspace is initialized
        if memgraph_workspace and memgraph_workspace.strip():
            logger.info(
                f"Using MEMGRAPH_WORKSPACE environment variable: '{memgraph_workspace}' (overriding '{original_workspace}/{namespace}')"
            )

        self._driver = None

    def _get_workspace_label(self) -> str:
        """Return workspace label (guaranteed non-empty during initialization)"""
        return self.workspace

    async def initialize(self):
        async with get_data_init_lock():
            URI = os.environ.get(
                "MEMGRAPH_URI",
                config.get("memgraph", "uri", fallback="bolt://localhost:7687"),
            )
            USERNAME = os.environ.get(
                "MEMGRAPH_USERNAME", config.get("memgraph", "username", fallback="")
            )
            PASSWORD = os.environ.get(
                "MEMGRAPH_PASSWORD", config.get("memgraph", "password", fallback="")
            )
            DATABASE = os.environ.get(
                "MEMGRAPH_DATABASE",
                config.get("memgraph", "database", fallback="memgraph"),
            )

            self._driver = AsyncGraphDatabase.driver(
                URI,
                auth=(USERNAME, PASSWORD),
                max_connection_lifetime=600,  # 10 minutes (shorter than default 1hr to recycle connections)
                keep_alive=True,
                connection_timeout=60.0,
            )
            self._DATABASE = DATABASE
            try:
                async with self._driver.session(database=DATABASE) as session:
                    # Create index for base nodes on entity_id if it doesn't exist
                    try:
                        workspace_label = self._get_workspace_label()
                        await session.run(
                            f"""CREATE INDEX ON :{workspace_label}(entity_id)"""
                        )
                        logger.info(
                            f"[{self.workspace}] Created index on :{workspace_label}(entity_id) in Memgraph."
                        )
                    except Exception as e:
                        # Index may already exist, which is not an error
                        logger.warning(
                            f"[{self.workspace}] Index creation on :{workspace_label}(entity_id) may have failed or already exists: {e}"
                        )
                    await session.run("RETURN 1")
                    logger.info(f"[{self.workspace}] Connected to Memgraph at {URI}")
            except Exception as e:
                logger.error(
                    f"[{self.workspace}] Failed to connect to Memgraph at {URI}: {e}"
                )
                raise

    async def finalize(self):
        if self._driver is not None:
            await self._driver.close()
            self._driver = None

    async def __aexit__(self, exc_type, exc, tb):
        await self.finalize()

    async def index_done_callback(self):
        # Memgraph handles persistence automatically
        pass

    async def has_node(self, node_id: str) -> bool:
        """
        Check if a node exists in the graph.

        Args:
            node_id: The ID of the node to check.

        Returns:
            bool: True if the node exists, False otherwise.

        Raises:
            Exception: If there is an error checking the node existence.
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )
        async with self._driver.session(
            database=self._DATABASE, default_access_mode="READ"
        ) as session:
            result = None
            try:
                workspace_label = self._get_workspace_label()
                query = f"MATCH (n:`{workspace_label}` {{entity_id: $entity_id}}) RETURN count(n) > 0 AS node_exists"
                result = await session.run(query, entity_id=node_id)
                single_result = await result.single()
                await result.consume()  # Ensure result is fully consumed
                return (
                    single_result["node_exists"] if single_result is not None else False
                )
            except Exception as e:
                logger.error(
                    f"[{self.workspace}] Error checking node existence for {node_id}: {str(e)}"
                )
                if result is not None:
                    await (
                        result.consume()
                    )  # Ensure the result is consumed even on error
                raise

    async def has_edge(self, source_node_id: str, target_node_id: str) -> bool:
        """
        Check if an edge exists between two nodes in the graph.

        Args:
            source_node_id: The ID of the source node.
            target_node_id: The ID of the target node.

        Returns:
            bool: True if the edge exists, False otherwise.

        Raises:
            Exception: If there is an error checking the edge existence.
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )
        async with self._driver.session(
            database=self._DATABASE, default_access_mode="READ"
        ) as session:
            result = None
            try:
                workspace_label = self._get_workspace_label()
                query = (
                    f"MATCH (a:`{workspace_label}` {{entity_id: $source_entity_id}})-[r]-(b:`{workspace_label}` {{entity_id: $target_entity_id}}) "
                    "RETURN COUNT(r) > 0 AS edgeExists"
                )
                result = await session.run(
                    query,
                    source_entity_id=source_node_id,
                    target_entity_id=target_node_id,
                )  # type: ignore
                single_result = await result.single()
                await result.consume()  # Ensure result is fully consumed
                return (
                    single_result["edgeExists"] if single_result is not None else False
                )
            except Exception as e:
                logger.error(
                    f"[{self.workspace}] Error checking edge existence between {source_node_id} and {target_node_id}: {str(e)}"
                )
                if result is not None:
                    await (
                        result.consume()
                    )  # Ensure the result is consumed even on error
                raise

    async def get_node(self, node_id: str) -> dict[str, str] | None:
        """Get node by its label identifier, return only node properties

        Args:
            node_id: The node label to look up

        Returns:
            dict: Node properties if found
            None: If node not found

        Raises:
            Exception: If there is an error executing the query
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )
        async with self._driver.session(
            database=self._DATABASE, default_access_mode="READ"
        ) as session:
            try:
                workspace_label = self._get_workspace_label()
                query = (
                    f"MATCH (n:`{workspace_label}` {{entity_id: $entity_id}}) RETURN n"
                )
                result = await session.run(query, entity_id=node_id)
                try:
                    records = await result.fetch(
                        2
                    )  # Get 2 records for duplication check

                    if len(records) > 1:
                        logger.warning(
                            f"[{self.workspace}] Multiple nodes found with label '{node_id}'. Using first node."
                        )
                    if records:
                        node = records[0]["n"]
                        node_dict = dict(node)
                        # Remove workspace label from labels list if it exists
                        if "labels" in node_dict:
                            node_dict["labels"] = [
                                label
                                for label in node_dict["labels"]
                                if label != workspace_label
                            ]
                        return node_dict
                    return None
                finally:
                    await result.consume()  # Ensure result is fully consumed
            except Exception as e:
                logger.error(
                    f"[{self.workspace}] Error getting node for {node_id}: {str(e)}"
                )
                raise

    async def node_degree(self, node_id: str) -> int:
        """Get the degree (number of relationships) of a node with the given label.
        If multiple nodes have the same label, returns the degree of the first node.
        If no node is found, returns 0.

        Args:
            node_id: The label of the node

        Returns:
            int: The number of relationships the node has, or 0 if no node found

        Raises:
            Exception: If there is an error executing the query
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )
        async with self._driver.session(
            database=self._DATABASE, default_access_mode="READ"
        ) as session:
            try:
                workspace_label = self._get_workspace_label()
                query = f"""
                    MATCH (n:`{workspace_label}` {{entity_id: $entity_id}})
                    OPTIONAL MATCH (n)-[r]-()
                    RETURN COUNT(r) AS degree
                """
                result = await session.run(query, entity_id=node_id)
                try:
                    record = await result.single()

                    if not record:
                        logger.warning(
                            f"[{self.workspace}] No node found with label '{node_id}'"
                        )
                        return 0

                    degree = record["degree"]
                    return degree
                finally:
                    await result.consume()  # Ensure result is fully consumed
            except Exception as e:
                logger.error(
                    f"[{self.workspace}] Error getting node degree for {node_id}: {str(e)}"
                )
                raise

    async def get_all_labels(self) -> list[str]:
        """
        Get all existing node labels in the database
        Returns:
            ["Person", "Company", ...]  # Alphabetically sorted label list

        Raises:
            Exception: If there is an error executing the query
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )
        async with self._driver.session(
            database=self._DATABASE, default_access_mode="READ"
        ) as session:
            result = None
            try:
                workspace_label = self._get_workspace_label()
                query = f"""
                MATCH (n:`{workspace_label}`)
                WHERE n.entity_id IS NOT NULL
                RETURN DISTINCT n.entity_id AS label
                ORDER BY label
                """
                result = await session.run(query)
                labels = []
                async for record in result:
                    labels.append(record["label"])
                await result.consume()
                return labels
            except Exception as e:
                logger.error(f"[{self.workspace}] Error getting all labels: {str(e)}")
                if result is not None:
                    await (
                        result.consume()
                    )  # Ensure the result is consumed even on error
                raise

    async def get_node_edges(self, source_node_id: str) -> list[tuple[str, str]] | None:
        """Retrieves all edges (relationships) for a particular node identified by its label.

        Args:
            source_node_id: Label of the node to get edges for

        Returns:
            list[tuple[str, str]]: List of (source_label, target_label) tuples representing edges
            None: If no edges found

        Raises:
            Exception: If there is an error executing the query
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )
        try:
            async with self._driver.session(
                database=self._DATABASE, default_access_mode="READ"
            ) as session:
                results = None
                try:
                    workspace_label = self._get_workspace_label()
                    query = f"""MATCH (n:`{workspace_label}` {{entity_id: $entity_id}})
                            OPTIONAL MATCH (n)-[r]-(connected:`{workspace_label}`)
                            WHERE connected.entity_id IS NOT NULL
                            RETURN n, r, connected"""
                    results = await session.run(query, entity_id=source_node_id)

                    edges = []
                    async for record in results:
                        source_node = record["n"]
                        connected_node = record["connected"]

                        # Skip if either node is None
                        if not source_node or not connected_node:
                            continue

                        source_label = (
                            source_node.get("entity_id")
                            if source_node.get("entity_id")
                            else None
                        )
                        target_label = (
                            connected_node.get("entity_id")
                            if connected_node.get("entity_id")
                            else None
                        )

                        if source_label and target_label:
                            edges.append((source_label, target_label))

                    await results.consume()  # Ensure results are consumed
                    return edges
                except Exception as e:
                    logger.error(
                        f"[{self.workspace}] Error getting edges for node {source_node_id}: {str(e)}"
                    )
                    if results is not None:
                        await (
                            results.consume()
                        )  # Ensure results are consumed even on error
                    raise
        except Exception as e:
            logger.error(
                f"[{self.workspace}] Error in get_node_edges for {source_node_id}: {str(e)}"
            )
            raise

    async def get_edge(
        self, source_node_id: str, target_node_id: str
    ) -> dict[str, str] | None:
        """Get edge properties between two nodes.

        Args:
            source_node_id: Label of the source node
            target_node_id: Label of the target node

        Returns:
            dict: Edge properties if found, default properties if not found or on error

        Raises:
            Exception: If there is an error executing the query
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )
        async with self._driver.session(
            database=self._DATABASE, default_access_mode="READ"
        ) as session:
            result = None
            try:
                workspace_label = self._get_workspace_label()
                query = f"""
                MATCH (start:`{workspace_label}` {{entity_id: $source_entity_id}})-[r]-(end:`{workspace_label}` {{entity_id: $target_entity_id}})
                RETURN properties(r) as edge_properties
                """
                result = await session.run(
                    query,
                    source_entity_id=source_node_id,
                    target_entity_id=target_node_id,
                )
                records = await result.fetch(2)
                await result.consume()
                if records:
                    edge_result = dict(records[0]["edge_properties"])
                    for key, default_value in {
                        "weight": 1.0,
                        "source_id": None,
                        "description": None,
                        "keywords": None,
                    }.items():
                        if key not in edge_result:
                            edge_result[key] = default_value
                            logger.warning(
                                f"[{self.workspace}] Edge between {source_node_id} and {target_node_id} is missing property: {key}. Using default value: {default_value}"
                            )
                    return edge_result
                return None
            except Exception as e:
                logger.error(
                    f"[{self.workspace}] Error getting edge between {source_node_id} and {target_node_id}: {str(e)}"
                )
                if result is not None:
                    await (
                        result.consume()
                    )  # Ensure the result is consumed even on error
                raise

    async def get_unified_neighbor_search(
        self,
        query_embedding: list[float],
        top_k: int,
        vector_index_name: str,
        cosine_threshold: float,
    ) -> list[dict]:
        """
        Unified search: Vector Search -> Get Node Properties -> Get Degrees
        Executed in a single Cypher traversal.
        """
        if self._driver is None:
            raise RuntimeError("Memgraph driver is not initialized.")

        # Try to guess index name if not provided or if simple label
        potential_index_names = [
            vector_index_name,
            f"{vector_index_name}_idx",
            f"{vector_index_name}_idx_conf",
        ]

        async with self._driver.session(
            database=self._DATABASE, default_access_mode="READ"
        ) as session:
            workspace_label = self._get_workspace_label()

            # Try each index name candidate
            last_exception = None
            for idx_name in potential_index_names:
                try:
                    # Cypher query for unified retrieval
                    # 1. Vector Search
                    # 2. Match corresponding Graph Node (by entity_id)
                    # 3. Calculate Degree (count relationships)
                    query = f"""
                    CALL vector_search.search($index_name, $top_k, $embedding)
                    YIELD node as v_node, similarity
                    WHERE similarity >= $threshold
                    WITH v_node, similarity
                    MATCH (g_node:`{workspace_label}` {{entity_id: v_node.entity_name}})
                    OPTIONAL MATCH (g_node)-[r]-()
                    WITH g_node, similarity, count(r) as degree
                    RETURN g_node, degree, similarity
                    ORDER BY similarity DESC
                    """

                    result = await session.run(
                        query,
                        index_name=idx_name,
                        top_k=top_k,
                        embedding=query_embedding,
                        threshold=cosine_threshold,
                    )

                    nodes = []
                    async for record in result:
                        g_node = record["g_node"]
                        degree = record["degree"]
                        # similarity = record["similarity"] # Currently not used in downstream output format but useful for debug

                        node_props = dict(g_node)
                        # Clean up labels
                        if "labels" in node_props:
                            node_props["labels"] = [
                                label
                                for label in node_props["labels"]
                                if label != workspace_label
                            ]

                        # Add computed rank/degree to match operate.py expectation
                        node_props["rank"] = degree

                        nodes.append(node_props)

                    await result.consume()
                    return nodes

                except Exception as e:
                    last_exception = e
                    continue  # Try next index name

            # If we exhausted all indices or failed
            logger.warning(
                f"[{self.workspace}] Unified neighbor search failed with specialized indices. Error: {last_exception}"
            )
            return []

    async def get_unified_edge_search(
        self,
        query_embedding: list[float],
        top_k: int,
        vector_index_name: str,
        cosine_threshold: float,
    ) -> list[dict]:
        """
        Unified search: Vector Search (Relations) -> Get Edge Properties
        """
        if self._driver is None:
            raise RuntimeError("Memgraph driver is not initialized.")

        potential_index_names = [
            vector_index_name,
            f"{vector_index_name}_idx",
            f"{vector_index_name}_idx_conf",
        ]

        async with self._driver.session(
            database=self._DATABASE, default_access_mode="READ"
        ) as session:
            workspace_label = self._get_workspace_label()

            last_exception = None
            for idx_name in potential_index_names:
                try:
                    query = f"""
                    CALL vector_search.search($index_name, $top_k, $embedding)
                    YIELD node as v_node, similarity
                    WHERE similarity >= $threshold
                    WITH v_node, similarity
                    MATCH (src:`{workspace_label}` {{entity_id: v_node.src_id}})-[r]-(tgt:`{workspace_label}` {{entity_id: v_node.tgt_id}})
                    RETURN r, src, tgt, similarity
                    ORDER BY similarity DESC
                    """

                    result = await session.run(
                        query,
                        index_name=idx_name,
                        top_k=top_k,
                        embedding=query_embedding,
                        threshold=cosine_threshold,
                    )

                    edges = []
                    async for record in result:
                        edge = record["r"]
                        src = record["src"]
                        tgt = record["tgt"]

                        edge_props = dict(edge)

                        # Ensure we return valid relation data structure
                        if "weight" not in edge_props:
                            edge_props["weight"] = 1.0

                        combined = {
                            "src_id": src["entity_id"],
                            "tgt_id": tgt["entity_id"],
                            "created_at": edge_props.get("created_at"),
                            **edge_props,
                        }
                        edges.append(combined)

                    await result.consume()
                    return edges

                except Exception as e:
                    last_exception = e
                    continue

            logger.warning(
                f"[{self.workspace}] Unified edge search failed: {last_exception}"
            )
            return []

    async def upsert_node(self, node_id: str, node_data: dict[str, str]) -> None:
        """
        Upsert a node in the Memgraph database with manual transaction-level retry logic for transient errors.

        Args:
            node_id: The unique identifier for the node (used as label)
            node_data: Dictionary of node properties
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )
        properties = node_data
        entity_type = properties["entity_type"]
        if "entity_id" not in properties:
            raise ValueError(
                "Memgraph: node properties must contain an 'entity_id' field"
            )

        # Manual transaction-level retry following official Memgraph documentation
        max_retries = 100
        initial_wait_time = 0.2
        backoff_factor = 1.1
        jitter_factor = 0.1

        workspace_label = self._get_workspace_label()

        async def execute_upsert(tx: AsyncManagedTransaction):
            query = f"""
            MERGE (n:`{workspace_label}` {{entity_id: $entity_id}})
            SET n += $properties
            SET n:`{entity_type}`
            """
            result = await tx.run(query, entity_id=node_id, properties=properties)
            await result.consume()  # Ensure result is fully consumed

        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"[{self.workspace}] Attempting node upsert, attempt {attempt + 1}/{max_retries}"
                )
                async with self._driver.session(database=self._DATABASE) as session:
                    await session.execute_write(execute_upsert)
                    break  # Success - exit retry loop

            except (TransientError, ResultFailedError) as e:
                # Check if the root cause is a TransientError
                root_cause = e
                while hasattr(root_cause, "__cause__") and root_cause.__cause__:
                    root_cause = root_cause.__cause__

                # Check if this is a transient error that should be retried
                is_transient = (
                    isinstance(root_cause, TransientError)
                    or isinstance(e, TransientError)
                    or "TransientError" in str(e)
                    or "Cannot resolve conflicting transactions" in str(e)
                )

                if is_transient:
                    if attempt < max_retries - 1:
                        # Calculate wait time with exponential backoff and jitter
                        jitter = random.uniform(0, jitter_factor) * initial_wait_time
                        wait_time = (
                            initial_wait_time * (backoff_factor**attempt) + jitter
                        )
                        logger.warning(
                            f"[{self.workspace}] Node upsert failed. Attempt #{attempt + 1} retrying in {wait_time:.3f} seconds... Error: {str(e)}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"[{self.workspace}] Memgraph transient error during node upsert after {max_retries} retries: {str(e)}"
                        )
                        raise
                else:
                    # Non-transient error, don't retry
                    logger.error(
                        f"[{self.workspace}] Non-transient error during node upsert: {str(e)}"
                    )
                    raise
            except Exception as e:
                logger.error(
                    f"[{self.workspace}] Unexpected error during node upsert: {str(e)}"
                )
                raise

    async def upsert_edge(
        self, source_node_id: str, target_node_id: str, edge_data: dict[str, str]
    ) -> None:
        """
        Upsert an edge and its properties between two nodes identified by their labels with manual transaction-level retry logic for transient errors.
        Ensures both source and target nodes exist and are unique before creating the edge.
        Uses entity_id property to uniquely identify nodes.

        Args:
            source_node_id (str): Label of the source node (used as identifier)
            target_node_id (str): Label of the target node (used as identifier)
            edge_data (dict): Dictionary of properties to set on the edge

        Raises:
            Exception: If there is an error executing the query
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )

        edge_properties = edge_data

        # Manual transaction-level retry following official Memgraph documentation
        max_retries = 100
        initial_wait_time = 0.2
        backoff_factor = 1.1
        jitter_factor = 0.1

        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"[{self.workspace}] Attempting edge upsert, attempt {attempt + 1}/{max_retries}"
                )
                async with self._driver.session(database=self._DATABASE) as session:

                    async def execute_upsert(tx: AsyncManagedTransaction):
                        workspace_label = self._get_workspace_label()
                        query = f"""
                        MATCH (source:`{workspace_label}` {{entity_id: $source_entity_id}})
                        WITH source
                        MATCH (target:`{workspace_label}` {{entity_id: $target_entity_id}})
                        MERGE (source)-[r:DIRECTED]-(target)
                        SET r += $properties
                        RETURN r, source, target
                        """
                        result = await tx.run(
                            query,
                            source_entity_id=source_node_id,
                            target_entity_id=target_node_id,
                            properties=edge_properties,
                        )
                        try:
                            await result.fetch(2)
                        finally:
                            await result.consume()  # Ensure result is consumed

                    await session.execute_write(execute_upsert)
                    break  # Success - exit retry loop

            except (TransientError, ResultFailedError) as e:
                # Check if the root cause is a TransientError
                root_cause = e
                while hasattr(root_cause, "__cause__") and root_cause.__cause__:
                    root_cause = root_cause.__cause__

                # Check if this is a transient error that should be retried
                is_transient = (
                    isinstance(root_cause, TransientError)
                    or isinstance(e, TransientError)
                    or "TransientError" in str(e)
                    or "Cannot resolve conflicting transactions" in str(e)
                )

                if is_transient:
                    if attempt < max_retries - 1:
                        # Calculate wait time with exponential backoff and jitter
                        jitter = random.uniform(0, jitter_factor) * initial_wait_time
                        wait_time = (
                            initial_wait_time * (backoff_factor**attempt) + jitter
                        )
                        logger.warning(
                            f"[{self.workspace}] Edge upsert failed. Attempt #{attempt + 1} retrying in {wait_time:.3f} seconds... Error: {str(e)}"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"[{self.workspace}] Memgraph transient error during edge upsert after {max_retries} retries: {str(e)}"
                        )
                        raise
                else:
                    # Non-transient error, don't retry
                    logger.error(
                        f"[{self.workspace}] Non-transient error during edge upsert: {str(e)}"
                    )
                    raise
            except Exception as e:
                logger.error(
                    f"[{self.workspace}] Unexpected error during edge upsert: {str(e)}"
                )
                raise

    async def delete_node(self, node_id: str) -> None:
        """Delete a node with the specified label

        Args:
            node_id: The label of the node to delete

        Raises:
            Exception: If there is an error executing the query
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )

        async def _do_delete(tx: AsyncManagedTransaction):
            workspace_label = self._get_workspace_label()
            query = f"""
            MATCH (n:`{workspace_label}` {{entity_id: $entity_id}})
            DETACH DELETE n
            """
            result = await tx.run(query, entity_id=node_id)
            logger.debug(f"[{self.workspace}] Deleted node with label {node_id}")
            await result.consume()

        try:
            async with self._driver.session(database=self._DATABASE) as session:
                await session.execute_write(_do_delete)
        except Exception as e:
            logger.error(f"[{self.workspace}] Error during node deletion: {str(e)}")
            raise

    async def remove_nodes(self, nodes: list[str]):
        """Delete multiple nodes

        Args:
            nodes: List of node labels to be deleted
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )
        for node in nodes:
            await self.delete_node(node)

    async def remove_edges(self, edges: list[tuple[str, str]]):
        """Delete multiple edges

        Args:
            edges: List of edges to be deleted, each edge is a (source, target) tuple

        Raises:
            Exception: If there is an error executing the query
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )
        workspace_label = self._get_workspace_label()
        for source, target in edges:

            async def _do_delete_edge(
                tx: AsyncManagedTransaction, s=source, t=target, wl=workspace_label
            ):
                query = f"""
                MATCH (source:`{wl}` {{entity_id: $source_entity_id}})-[r]-(target:`{wl}` {{entity_id: $target_entity_id}})
                DELETE r
                """
                result = await tx.run(query, source_entity_id=s, target_entity_id=t)
                logger.debug(f"[{self.workspace}] Deleted edge from '{s}' to '{t}'")
                await result.consume()  # Ensure result is fully consumed

            try:
                async with self._driver.session(database=self._DATABASE) as session:
                    await session.execute_write(_do_delete_edge)
            except Exception as e:
                logger.error(f"[{self.workspace}] Error during edge deletion: {str(e)}")
                raise

    async def drop(self) -> dict[str, str]:
        """Drop all data from the current workspace and clean up resources

        This method will delete all nodes and relationships in the Memgraph database.

        Returns:
            dict[str, str]: Operation status and message
            - On success: {"status": "success", "message": "data dropped"}
            - On failure: {"status": "error", "message": "<error details>"}

        Raises:
            Exception: If there is an error executing the query
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )
        try:
            async with self._driver.session(database=self._DATABASE) as session:
                workspace_label = self._get_workspace_label()
                query = f"MATCH (n:`{workspace_label}`) DETACH DELETE n"
                result = await session.run(query)
                await result.consume()
                logger.info(
                    f"[{self.workspace}] Dropped workspace {workspace_label} from Memgraph database {self._DATABASE}"
                )
                return {"status": "success", "message": "workspace data dropped"}
        except Exception as e:
            logger.error(
                f"[{self.workspace}] Error dropping workspace {workspace_label} from Memgraph database {self._DATABASE}: {e}"
            )
            return {"status": "error", "message": str(e)}

    async def edge_degree(self, src_id: str, tgt_id: str) -> int:
        """Get the total degree (sum of relationships) of two nodes.

        Args:
            src_id: Label of the source node
            tgt_id: Label of the target node

        Returns:
            int: Sum of the degrees of both nodes
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )
        src_degree = await self.node_degree(src_id)
        trg_degree = await self.node_degree(tgt_id)

        # Convert None to 0 for addition
        src_degree = 0 if src_degree is None else src_degree
        trg_degree = 0 if trg_degree is None else trg_degree

        degrees = int(src_degree) + int(trg_degree)
        return degrees

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
            max_nodes: Maximum nodes to return by BFS, Defaults to 1000

        Returns:
            KnowledgeGraph object containing nodes and edges, with an is_truncated flag
            indicating whether the graph was truncated due to max_nodes limit
        """
        # Get max_nodes from global_config if not provided
        if max_nodes is None:
            max_nodes = self.global_config.get("max_graph_nodes", 1000)
        else:
            # Limit max_nodes to not exceed global_config max_graph_nodes
            max_nodes = min(max_nodes, self.global_config.get("max_graph_nodes", 1000))

        workspace_label = self._get_workspace_label()
        result = KnowledgeGraph()
        seen_nodes = set()
        seen_edges = set()

        async with self._driver.session(
            database=self._DATABASE, default_access_mode="READ"
        ) as session:
            try:
                if node_label == "*":
                    # First check total node count to determine if graph is truncated
                    count_query = (
                        f"MATCH (n:`{workspace_label}`) RETURN count(n) as total"
                    )
                    count_result = None
                    try:
                        count_result = await session.run(count_query)
                        count_record = await count_result.single()

                        if count_record and count_record["total"] > max_nodes:
                            result.is_truncated = True
                            logger.info(
                                f"Graph truncated: {count_record['total']} nodes found, limited to {max_nodes}"
                            )
                    finally:
                        if count_result:
                            await count_result.consume()

                    # Run main query to get nodes with highest degree
                    main_query = f"""
                    MATCH (n:`{workspace_label}`)
                    OPTIONAL MATCH (n)-[r]-()
                    WITH n, COALESCE(count(r), 0) AS degree
                    ORDER BY degree DESC
                    LIMIT $max_nodes
                    WITH collect({{node: n}}) AS filtered_nodes
                    UNWIND filtered_nodes AS node_info
                    WITH collect(node_info.node) AS kept_nodes, filtered_nodes
                    OPTIONAL MATCH (a)-[r]-(b)
                    WHERE a IN kept_nodes AND b IN kept_nodes
                    RETURN filtered_nodes AS node_info,
                        collect(DISTINCT r) AS relationships
                    """
                    result_set = None
                    try:
                        result_set = await session.run(
                            main_query,
                            {"max_nodes": max_nodes},
                        )
                        record = await result_set.single()
                    finally:
                        if result_set:
                            await result_set.consume()

                else:
                    # Run subgraph query for specific node_label
                    subgraph_query = f"""
                    MATCH (start:`{workspace_label}`)
                    WHERE start.entity_id = $entity_id

                    MATCH path = (start)-[*BFS 0..{max_depth}]-(end:`{workspace_label}`)
                    WHERE ALL(n IN nodes(path) WHERE '{workspace_label}' IN labels(n))
                    WITH collect(DISTINCT end) + start AS all_nodes_unlimited
                    WITH
                    CASE
                        WHEN size(all_nodes_unlimited) <= $max_nodes THEN all_nodes_unlimited
                        ELSE all_nodes_unlimited[0..$max_nodes]
                    END AS limited_nodes,
                    size(all_nodes_unlimited) > $max_nodes AS is_truncated

                    UNWIND limited_nodes AS n
                    MATCH (n)-[r]-(m)
                    WHERE m IN limited_nodes
                    WITH collect(DISTINCT n) AS limited_nodes, collect(DISTINCT r) AS relationships, is_truncated

                    RETURN
                    [node IN limited_nodes | {{node: node}}] AS node_info,
                    relationships,
                    is_truncated
                    """

                    result_set = None
                    try:
                        result_set = await session.run(
                            subgraph_query,
                            {
                                "entity_id": node_label,
                                "max_nodes": max_nodes,
                            },
                        )
                        record = await result_set.single()

                        # If no record found, return empty KnowledgeGraph
                        if not record:
                            logger.debug(
                                f"[{self.workspace}] No nodes found for entity_id: {node_label}"
                            )
                            return result

                        # Check if the result was truncated
                        if record.get("is_truncated"):
                            result.is_truncated = True
                            logger.info(
                                f"[{self.workspace}] Graph truncated: breadth-first search limited to {max_nodes} nodes"
                            )

                    finally:
                        if result_set:
                            await result_set.consume()

                if record:
                    for node_info in record["node_info"]:
                        node = node_info["node"]
                        node_id = node.element_id
                        if node_id not in seen_nodes:
                            result.nodes.append(
                                KnowledgeGraphNode(
                                    id=f"{node_id}",
                                    labels=[node.get("entity_id")],
                                    properties=dict(node),
                                )
                            )
                            seen_nodes.add(node_id)

                    for rel in record["relationships"]:
                        edge_id = rel.element_id
                        if edge_id not in seen_edges:
                            start = rel.start_node
                            end = rel.end_node
                            result.edges.append(
                                KnowledgeGraphEdge(
                                    id=f"{edge_id}",
                                    type=rel.type,
                                    source=f"{start.element_id}",
                                    target=f"{end.element_id}",
                                    properties=dict(rel),
                                )
                            )
                            seen_edges.add(edge_id)

                    logger.info(
                        f"[{self.workspace}] Subgraph query successful | Node count: {len(result.nodes)} | Edge count: {len(result.edges)}"
                    )

            except Exception as e:
                logger.warning(
                    f"[{self.workspace}] Memgraph error during subgraph query: {str(e)}"
                )

        return result

    async def get_all_nodes(self) -> list[dict]:
        """Get all nodes in the graph.

        Returns:
            A list of all nodes, where each node is a dictionary of its properties
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )
        workspace_label = self._get_workspace_label()
        async with self._driver.session(
            database=self._DATABASE, default_access_mode="READ"
        ) as session:
            query = f"""
            MATCH (n:`{workspace_label}`)
            RETURN n
            """
            result = await session.run(query)
            nodes = []
            async for record in result:
                node = record["n"]
                node_dict = dict(node)
                # Add node id (entity_id) to the dictionary for easier access
                node_dict["id"] = node_dict.get("entity_id")
                nodes.append(node_dict)
            await result.consume()
            return nodes

    async def get_all_edges(self) -> list[dict]:
        """Get all edges in the graph.

        Returns:
            A list of all edges, where each edge is a dictionary of its properties
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )
        workspace_label = self._get_workspace_label()
        async with self._driver.session(
            database=self._DATABASE, default_access_mode="READ"
        ) as session:
            query = f"""
            MATCH (a:`{workspace_label}`)-[r]-(b:`{workspace_label}`)
            RETURN DISTINCT a.entity_id AS source, b.entity_id AS target, properties(r) AS properties
            """
            result = await session.run(query)
            edges = []
            async for record in result:
                edge_properties = record["properties"]
                edge_properties["source"] = record["source"]
                edge_properties["target"] = record["target"]
                edges.append(edge_properties)
            await result.consume()
            return edges

    async def get_popular_labels(self, limit: int = 300) -> list[str]:
        """Get popular labels by node degree (most connected entities)

        Args:
            limit: Maximum number of labels to return

        Returns:
            List of labels sorted by degree (highest first)
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )

        result = None
        try:
            workspace_label = self._get_workspace_label()
            async with self._driver.session(
                database=self._DATABASE, default_access_mode="READ"
            ) as session:
                query = f"""
                MATCH (n:`{workspace_label}`)
                WHERE n.entity_id IS NOT NULL
                OPTIONAL MATCH (n)-[r]-()
                WITH n.entity_id AS label, count(r) AS degree
                ORDER BY degree DESC, label ASC
                LIMIT {limit}
                RETURN label
                """
                result = await session.run(query)
                labels = []
                async for record in result:
                    labels.append(record["label"])
                await result.consume()

                logger.debug(
                    f"[{self.workspace}] Retrieved {len(labels)} popular labels (limit: {limit})"
                )
                return labels
        except Exception as e:
            logger.error(f"[{self.workspace}] Error getting popular labels: {str(e)}")
            if result is not None:
                await result.consume()
            return []

    async def search_labels(self, query: str, limit: int = 50) -> list[str]:
        """Search labels with fuzzy matching

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of matching labels sorted by relevance
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )

        query_lower = query.lower().strip()

        if not query_lower:
            return []

        result = None
        try:
            workspace_label = self._get_workspace_label()
            async with self._driver.session(
                database=self._DATABASE, default_access_mode="READ"
            ) as session:
                cypher_query = f"""
                MATCH (n:`{workspace_label}`)
                WHERE n.entity_id IS NOT NULL
                WITH n.entity_id AS label, toLower(n.entity_id) AS label_lower
                WHERE label_lower CONTAINS $query_lower
                WITH label, label_lower,
                     CASE
                         WHEN label_lower = $query_lower THEN 1000
                         WHEN label_lower STARTS WITH $query_lower THEN 500
                         ELSE 100 - size(label)
                     END AS score
                ORDER BY score DESC, label ASC
                LIMIT {limit}
                RETURN label
                """

                result = await session.run(cypher_query, query_lower=query_lower)
                labels = []
                async for record in result:
                    labels.append(record["label"])
                await result.consume()

                logger.debug(
                    f"[{self.workspace}] Search query '{query}' returned {len(labels)} results (limit: {limit})"
                )
                return labels
        except Exception as e:
            logger.error(f"[{self.workspace}] Error searching labels: {str(e)}")
            if result is not None:
                await result.consume()
            return []

    # Community Detection Methods

    async def detect_communities(
        self, algorithm: str = "louvain", weight_property: str = "weight"
    ) -> dict[str, int]:
        """
        Detect communities in the knowledge graph using MAGE algorithms.

        Args:
            algorithm: Community detection algorithm ('louvain' or 'leiden')
            weight_property: Property name to use as edge weight

        Returns:
            Dict mapping node IDs to community IDs

        Raises:
            RuntimeError: If driver is not initialized
            Exception: If community detection fails
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )

        workspace_label = self._get_workspace_label()

        try:
            async with self._driver.session(
                database=self._DATABASE, default_access_mode="WRITE"
            ) as session:
                communities = {}

                # Choose MAGE procedure based on algorithm
                if algorithm.lower() == "louvain":
                    query = f"""
                    CALL louvain.projection('{workspace_label}', '{weight_property}')
                    YIELD node, community_id
                    RETURN node.id AS node_id, community_id
                    """
                    result = await session.run(query)

                elif algorithm.lower() == "leiden":
                    query = f"""
                    CALL leiden.projection('{workspace_label}', '{weight_property}')
                    YIELD node, community_id
                    RETURN node.id AS node_id, community_id
                    """
                    result = await session.run(query)

                else:
                    raise ValueError(
                        f"Unsupported algorithm: {algorithm}. Use 'louvain' or 'leiden'"
                    )

                async for record in result:
                    node_id = record["node_id"]
                    community_id = record["community_id"]
                    communities[node_id] = community_id

                await result.consume()

                logger.info(
                    f"[{self.workspace}] Detected {len(set(communities.values()))} communities "
                    f"in {len(communities)} nodes using {algorithm} algorithm"
                )

                return communities

        except Exception as e:
            logger.error(f"[{self.workspace}] Community detection failed: {str(e)}")
            raise

    async def assign_community_ids(
        self, communities: dict[str, int], algorithm: str = "louvain"
    ) -> int:
        """
        Assign community IDs to nodes as properties for efficient filtering.

        Args:
            communities: Dict mapping node IDs to community IDs
            algorithm: Algorithm name for property naming

        Returns:
            Number of nodes updated

        Raises:
            RuntimeError: If driver is not initialized
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )

        if not communities:
            logger.warning(f"[{self.workspace}] No communities to assign")
            return 0

        workspace_label = self._get_workspace_label()
        community_property = f"{algorithm}_community"

        try:
            async with self._driver.session(
                database=self._DATABASE, default_access_mode="WRITE"
            ) as session:
                # Use UNWIND for efficient batch updates
                query = f"""
                UNWIND $updates AS update
                MATCH (n:{workspace_label} {{id: update.node_id}})
                SET n.{community_property} = update.community_id
                RETURN count(*) AS updated_count
                """

                # Convert to list of dicts for UNWIND
                updates = [
                    {"node_id": node_id, "community_id": community_id}
                    for node_id, community_id in communities.items()
                ]

                result = await session.run(query, updates=updates)
                record = await result.single()
                updated_count = record["updated_count"] if record else 0
                await result.consume()

                logger.info(
                    f"[{self.workspace}] Assigned {algorithm} community IDs to {updated_count} nodes "
                    f"using property '{community_property}'"
                )

                return updated_count

        except Exception as e:
            logger.error(f"[{self.workspace}] Failed to assign community IDs: {str(e)}")
            raise

    async def get_node_communities(
        self, node_ids: list[str], algorithm: str = "louvain"
    ) -> dict[str, int]:
        """
        Get community IDs for specific nodes.

        Args:
            node_ids: List of node IDs to get communities for
            algorithm: Algorithm used for community detection

        Returns:
            Dict mapping node IDs to community IDs
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )

        if not node_ids:
            return {}

        workspace_label = self._get_workspace_label()
        community_property = f"{algorithm}_community"

        try:
            async with self._driver.session(
                database=self._DATABASE, default_access_mode="READ"
            ) as session:
                query = f"""
                MATCH (n:{workspace_label})
                WHERE n.id IN $node_ids AND n.{community_property} IS NOT NULL
                RETURN n.id AS node_id, n.{community_property} AS community_id
                """

                result = await session.run(query, node_ids=node_ids)

                communities = {}
                async for record in result:
                    node_id = record["node_id"]
                    community_id = record["community_id"]
                    communities[node_id] = community_id

                await result.consume()

                return communities

        except Exception as e:
            logger.error(f"[{self.workspace}] Failed to get node communities: {str(e)}")
            return {}

    async def filter_by_community(
        self,
        query: str,
        community_ids: list[int] = None,
        algorithm: str = "louvain",
        top_k: int = 10,
    ) -> list[str]:
        """
        Execute graph query with optional community filtering for improved performance.

        Args:
            query: Graph query pattern (e.g., entity description)
            community_ids: List of community IDs to restrict search to. If None, search all.
            algorithm: Algorithm used for community detection
            top_k: Maximum number of results to return

        Returns:
            List of matching entity labels
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )

        workspace_label = self._get_workspace_label()
        community_property = f"{algorithm}_community"

        try:
            async with self._driver.session(
                database=self._DATABASE, default_access_mode="READ"
            ) as session:
                # Base query for fuzzy matching
                base_query = f"""
                MATCH (n:{workspace_label})
                WHERE n.labels CONTAINS $query
                """

                # Add community filtering if specified
                if community_ids:
                    base_query += f"AND n.{community_property} IN $community_ids\n"

                base_query += """
                RETURN DISTINCT n.labels
                LIMIT $top_k
                """

                params = {"query": query, "top_k": top_k}
                if community_ids:
                    params["community_ids"] = community_ids

                result = await session.run(base_query, **params)

                labels = []
                async for record in result:
                    labels.append(record["labels"])
                await result.consume()

                filter_info = (
                    f"restricted to communities {community_ids}"
                    if community_ids
                    else "unrestricted"
                )
                logger.debug(
                    f"[{self.workspace}] Community-filtered search '{query}' ({filter_info}) "
                    f"returned {len(labels)} results"
                )

                return labels

        except Exception as e:
            logger.error(
                f"[{self.workspace}] Error in community-filtered search: {str(e)}"
            )
            return []

    async def search_labels_with_community_filter(
        self,
        query: str,
        limit: int = 50,
        community_ids: list[int] = None,
        algorithm: str = "louvain",
    ) -> list[str]:
        """
        Search labels with fuzzy matching and optional community filtering.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            community_ids: Optional list of community IDs to restrict search to
            algorithm: Community detection algorithm used ('louvain' or 'leiden')

        Returns:
            List of matching labels sorted by relevance
        """
        if self._driver is None:
            raise RuntimeError(
                "Memgraph driver is not initialized. Call 'await initialize()' first."
            )

        query_lower = query.lower().strip()

        if not query_lower:
            return []

        workspace_label = self._get_workspace_label()
        community_property = f"{algorithm}_community"

        result = None
        try:
            async with self._driver.session(
                database=self._DATABASE, default_access_mode="READ"
            ) as session:
                # Build query with optional community filtering
                base_query = f"""
                MATCH (n:`{workspace_label}`)
                WHERE n.entity_id IS NOT NULL
                """

                # Add community filtering if specified
                if community_ids:
                    base_query += f"AND n.{community_property} IN $community_ids\n"

                base_query += f"""
                WITH n.entity_id AS label, toLower(n.entity_id) AS label_lower
                WHERE label_lower CONTAINS $query_lower
                WITH label, label_lower,
                     CASE
                         WHEN label_lower = $query_lower THEN 1000
                         WHEN label_lower STARTS WITH $query_lower THEN 500
                         ELSE 100 - size(label)
                     END AS score
                ORDER BY score DESC, label ASC
                LIMIT {limit}
                RETURN label
                """

                # Prepare parameters
                params = {"query_lower": query_lower}
                if community_ids:
                    params["community_ids"] = community_ids

                result = await session.run(base_query, **params)
                labels = []
                async for record in result:
                    labels.append(record["label"])
                await result.consume()

                filter_info = (
                    f"restricted to communities {community_ids}"
                    if community_ids
                    else "unrestricted"
                )
                logger.debug(
                    f"[{self.workspace}] Community-filtered search '{query}' ({filter_info}) "
                    f"returned {len(labels)} results (limit: {limit})"
                )
                return labels

        except Exception as e:
            logger.error(
                f"[{self.workspace}] Error in community-filtered search: {str(e)}"
            )
            if result is not None:
                await result.consume()
            return []


@final
@dataclass
class MemgraphVectorStorage(BaseVectorStorage):
    def __post_init__(self):
        self._validate_embedding_func()
        self._driver = None
        self._DATABASE = None

        # Priority: 1) MEMGRAPH_WORKSPACE env 2) workspace arg
        memgraph_workspace = os.environ.get("MEMGRAPH_WORKSPACE")
        if memgraph_workspace and memgraph_workspace.strip():
            self.workspace = memgraph_workspace

        if not self.workspace or not str(self.workspace).strip():
            self.workspace = "base"

        # Unique label for this vector storage namespace in this workspace
        # Labels in Memgraph/Neo4j cannot contain hyphens without backticks
        self.label = f"VDB_{self.workspace}_{self.namespace}"
        self._max_batch_size = self.global_config.get("embedding_batch_num", 32)

        # Consistent with NanoVectorDBStorage behavior
        kwargs = self.global_config.get("vector_db_storage_cls_kwargs", {})
        cosine_threshold = kwargs.get("cosine_better_than_threshold")
        if cosine_threshold is None:
            self.cosine_better_than_threshold = 0.2
        else:
            self.cosine_better_than_threshold = cosine_threshold

    async def initialize(self):
        async with get_data_init_lock():
            URI = os.environ.get(
                "MEMGRAPH_URI",
                config.get("memgraph", "uri", fallback="bolt://localhost:7687"),
            )
            USERNAME = os.environ.get(
                "MEMGRAPH_USERNAME", config.get("memgraph", "username", fallback="")
            )
            PASSWORD = os.environ.get(
                "MEMGRAPH_PASSWORD", config.get("memgraph", "password", fallback="")
            )
            DATABASE = os.environ.get(
                "MEMGRAPH_DATABASE",
                config.get("memgraph", "database", fallback="memgraph"),
            )

            self._driver = AsyncGraphDatabase.driver(
                URI,
                auth=(USERNAME, PASSWORD),
                max_connection_lifetime=600,
                keep_alive=True,
                connection_timeout=60.0,
            )
            self._DATABASE = DATABASE

            try:
                async with self._driver.session(database=DATABASE) as session:
                    # Check if index already exists to avoid errors
                    index_exists = False
                    try:
                        indexes = await session.run("SHOW INDEX INFO")
                        async for record in indexes:
                            # Index names might be user defined or auto-generated.
                            # We check if an index exists on our label for the 'vector' property.
                            if (
                                record.get("label") == self.label
                                and record.get("property") == "vector"
                            ):
                                index_exists = True
                                logger.info(
                                    f"[{self.workspace}] Vector index already exists on :`{self.label}`(vector)."
                                )
                                break
                    except Exception as e:
                        logger.debug(f"[{self.workspace}] Could not list indexes: {e}")

                    created = index_exists

                    if not created:
                        # Attempt 1: Native syntax (Memgraph 3.0+)
                        try:
                            await session.run(
                                f"CREATE INDEX ON :`{self.label}`(vector) FOR VECTOR"
                            )
                            logger.info(
                                f"[{self.workspace}] Created native vector index on :`{self.label}`(vector)."
                            )
                            created = True
                        except Exception:
                            pass

                    if not created:
                        # Attempt 1.7: Memgraph 3.x Community syntax with WITH CONFIG
                        try:
                            dim = 768
                            if hasattr(self.embedding_func, "embedding_dim"):
                                dim = self.embedding_func.embedding_dim

                            query = f"""
                            CREATE VECTOR INDEX `{self.label}_idx_conf` ON :`{self.label}`(vector)
                            WITH CONFIG {{
                                "dimension": {dim},
                                "capacity": 1000000,
                                "metric": "cos"
                            }}
                            """
                            logger.info(
                                f"[{self.workspace}] Attempting Memgraph CREATE VECTOR INDEX ... WITH CONFIG for {self.label}"
                            )
                            await session.run(query)
                            logger.info(
                                f"[{self.workspace}] Created Memgraph HNSW index via WITH CONFIG."
                            )
                            created = True
                        except Exception as e:
                            if "already exists" in str(e).lower():
                                created = True
                            else:
                                logger.debug(
                                    f"[{self.workspace}] Memgraph WITH CONFIG index creation failed: {e}"
                                )

                    if not created:
                        # Attempt 1.6: MAGE procedure
                        try:
                            dim = 768
                            if hasattr(self.embedding_func, "embedding_dim"):
                                dim = self.embedding_func.embedding_dim

                            logger.info(
                                f"[{self.workspace}] Attempting MAGE vector_search.create_index for {self.label}"
                            )

                            await session.run(
                                "CALL vector_search.create_index($label, 'vector', $dim, 1000000, 'COSINE', 'FLOAT32')",
                                label=self.label,
                                dim=dim,
                            )
                            logger.info(
                                f"[{self.workspace}] Created MAGE HNSW index on :`{self.label}`(vector)."
                            )
                            created = True
                        except Exception as e:
                            if "already exists" in str(e).lower():
                                created = True
                            logger.warning(
                                f"[{self.workspace}] MAGE create_index failed: {e}"
                            )

                    if not created:
                        try:
                            # Attempt 2: Standard index (fallback for brute force)
                            await session.run(
                                f"CREATE INDEX ON :`{self.label}`(vector)"
                            )
                            logger.info(
                                f"[{self.workspace}] Created standard index on :`{self.label}`(vector) as fallback."
                            )
                        except Exception:
                            pass

                    await session.run("RETURN 1")
                    logger.info(
                        f"[{self.workspace}] Connected to Memgraph at {URI} for vector storage {self.namespace}"
                    )
            except Exception as e:
                logger.error(
                    f"[{self.workspace}] Failed to connect to Memgraph at {URI} for vector storage: {e}"
                )
                raise

    async def finalize(self):
        if self._driver is not None:
            await self._driver.close()
            self._driver = None

    async def index_done_callback(self):
        pass

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        if not data:
            return

        current_time = int(time.time())

        # Check which records need embedding
        records_to_embed = []
        for doc_id, node_data in data.items():
            if "embedding" not in node_data or node_data["embedding"] is None:
                records_to_embed.append(
                    {"id": doc_id, "content": node_data.get("content", "")}
                )

        # Compute missing embeddings in batches
        if records_to_embed:
            contents = [r["content"] for r in records_to_embed]
            batches = [
                contents[i : i + self._max_batch_size]
                for i in range(0, len(contents), self._max_batch_size)
            ]
            embedding_tasks = [self.embedding_func(batch) for batch in batches]
            embeddings_list = await asyncio.gather(*embedding_tasks)
            embeddings = np.concatenate(embeddings_list)

            for i, r in enumerate(records_to_embed):
                data[r["id"]]["embedding"] = embeddings[i]

        # Prepare records for UNWIND
        params_list = []
        for doc_id, node_data in data.items():
            embedding = node_data.get("embedding")
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()

            record = {
                "id": doc_id,
                "content": node_data.get("content", ""),
                "vector": embedding,
                "created_at": current_time,
            }
            # Add meta fields
            for field in self.meta_fields:
                if field in node_data:
                    record[field] = node_data[field]
            params_list.append(record)

        async with self._driver.session(database=self._DATABASE) as session:
            query = f"""
            UNWIND $records AS record
            MERGE (n:`{self.label}` {{id: record.id}})
            SET n += record
            """
            await session.run(query, records=params_list)

        logger.debug(
            f"[{self.workspace}] Upserted {len(params_list)} vectors to {self.label}"
        )

    async def query(
        self, query: str, top_k: int, query_embedding: list[float] = None
    ) -> list[dict[str, Any]]:
        # Use provided embedding or compute it
        if query_embedding is not None:
            embedding = query_embedding
        else:
            embedding_result = await self.embedding_func([query])
            embedding = embedding_result[0]

        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()

        async with self._driver.session(
            database=self._DATABASE, default_access_mode="READ"
        ) as session:
            # Attempt 1: MAGE vector_search (fastest if index exists)
            # Try finding the index by iterating potential names or just standard convention
            # We updated creation to try using `self.label` as the index name if possible,
            # but usually index names must be unique.
            # Let's try the primary label name first.

            potential_index_names = [
                self.label,
                f"{self.label}_idx",
                f"{self.label}_idx_conf",
            ]

            search_success = False
            records = []

            for index_name in potential_index_names:
                search_query = f"""
                CALL vector_search.search('{index_name}', $limit, $embedding)
                YIELD node, similarity
                RETURN node, similarity
                """
                try:
                    result = await session.run(
                        search_query, embedding=embedding, limit=top_k
                    )
                    async for record in result:
                        if record["similarity"] < self.cosine_better_than_threshold:
                            continue
                        node_dict = dict(record["node"])
                        if "vector" in node_dict:
                            del node_dict["vector"]
                        records.append(
                            {
                                **node_dict,
                                "id": node_dict.get("id"),
                                "distance": record["similarity"],
                            }
                        )
                    await result.consume()
                    if records:
                        search_success = True
                        break  # Found results using this index
                    # If query ran but no results, maybe empty index? or index exists but no match.
                    # If index doesn't exist, it usually raises error.
                    # We continue if no error? No, if successful execution, we stop trying other names?
                    # Actually if index name doesn't exist, Memgraph raises error. So we catch exception and continue.
                    search_success = True  # Query executed without error
                    break
                except Exception:
                    continue  # Try next index name

            if search_success and records:
                return records

            # Attempt 2: Brute force fallback using cosine_similarity function (slow!)
            logger.warning(
                f"[{self.workspace}] Native vector search failed for {self.label}. Using slow brute-force fallback."
            )
            fallback_query = f"""
            MATCH (n:`{self.label}`)
            WHERE n.vector IS NOT NULL
            WITH n, vector_search.cosine_similarity(n.vector, $embedding) AS sim
            WHERE sim >= $threshold
            RETURN n, sim
            ORDER BY sim DESC
            LIMIT $limit
            """
            result = await session.run(
                fallback_query,
                embedding=embedding,
                limit=top_k,
                threshold=self.cosine_better_than_threshold,
            )
            records = []
            async for record in result:
                node_dict = dict(record["n"])
                if "vector" in node_dict:
                    del node_dict["vector"]
                records.append(
                    {**node_dict, "id": node_dict.get("id"), "distance": record["sim"]}
                )
            await result.consume()
            return records

    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        async with self._driver.session(
            database=self._DATABASE, default_access_mode="READ"
        ) as session:
            query = f"MATCH (n:`{self.label}` {{id: $id}}) RETURN n"
            result = await session.run(query, id=id)
            record = await result.single()
            if record:
                node_dict = dict(record["n"])
                if "vector" in node_dict:
                    del node_dict["vector"]
                node_dict["id"] = node_dict.get(
                    "id"
                )  # Ensure id is present top-level if needed
                return node_dict
            return None

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        if not ids:
            return []
        async with self._driver.session(
            database=self._DATABASE, default_access_mode="READ"
        ) as session:
            query = f"MATCH (n:`{self.label}`) WHERE n.id IN $ids RETURN n"
            result = await session.run(query, ids=ids)
            records = []
            async for record in result:
                node_dict = dict(record["n"])
                if "vector" in node_dict:
                    del node_dict["vector"]
                node_dict["id"] = node_dict.get("id")
                records.append(node_dict)
            return records

    async def get_vectors_by_ids(self, ids: list[str]) -> dict[str, list[float]]:
        if not ids:
            return {}
        async with self._driver.session(
            database=self._DATABASE, default_access_mode="READ"
        ) as session:
            query = f"MATCH (n:`{self.label}`) WHERE n.id IN $ids RETURN n.id as id, n.vector as vector"
            result = await session.run(query, ids=ids)
            return {
                record["id"]: record["vector"]
                async for record in result
                if record["vector"]
            }

    async def delete(self, ids: list[str]):
        if not ids:
            return
        async with self._driver.session(database=self._DATABASE) as session:
            await session.run(
                f"MATCH (n:`{self.label}`) WHERE n.id IN $ids DETACH DELETE n", ids=ids
            )

    async def drop(self) -> dict[str, str]:
        async with self._driver.session(database=self._DATABASE) as session:
            # Drop data
            await session.run(f"MATCH (n:`{self.label}`) DETACH DELETE n")

            # Drop indexes
            potential_indexes = [
                f"{self.label}_idx_conf",  # The one created by WITH CONFIG
                f"{self.label}_idx",
                self.label,  # unlikely but possible if native used label as index name
            ]
            for idx_name in potential_indexes:
                try:
                    await session.run(f"DROP VECTOR INDEX `{idx_name}` IF EXISTS")
                except Exception:
                    try:
                        await session.run(f"DROP INDEX ON :`{self.label}`(vector)")
                    except Exception:
                        pass

        logger.info(
            f"[{self.workspace}] Dropped all vectors and indexes in {self.label}"
        )
        return {"status": "success"}

    async def delete_entity(self, entity_name: str) -> None:
        entity_id = compute_mdhash_id(entity_name, prefix="ent-")
        await self.delete([entity_id])

    async def delete_entity_relation(self, entity_name: str) -> None:
        async with self._driver.session(database=self._DATABASE) as session:
            await session.run(
                f"MATCH (n:`{self.label}`) WHERE n.src_id = $name OR n.tgt_id = $name DETACH DELETE n",
                name=entity_name,
            )
