"""PostgreSQL Vector Storage implementation."""

import asyncio
import datetime
import json
from dataclasses import dataclass, field
from typing import Any
from typing import final

import numpy as np

from lightrag.base import BaseVectorStorage
from lightrag.namespace import NameSpace, is_namespace
from lightrag.utils import logger

from lightrag.kg.postgres.connection import ClientManager, PostgreSQLDB
from lightrag.kg.postgres.constants import (
    PG_MAX_IDENTIFIER_LENGTH,
    SQL_TEMPLATES,
    TABLES,
    _safe_index_name,
    namespace_to_table_name,
)
from lightrag.exceptions import DataMigrationError


@final
@dataclass
class PGVectorStorage(BaseVectorStorage):
    db: PostgreSQLDB | None = field(default=None)

    def __post_init__(self):
        self._validate_embedding_func()
        self._max_batch_size = self.global_config["embedding_batch_num"]
        config = self.global_config.get("vector_db_storage_cls_kwargs", {})
        cosine_threshold = config.get("cosine_better_than_threshold")
        if cosine_threshold is None:
            raise ValueError(
                "cosine_better_than_threshold must be specified in vector_db_storage_cls_kwargs"
            )
        self.cosine_better_than_threshold = cosine_threshold

        self.model_suffix = self._generate_collection_suffix()

        base_table = namespace_to_table_name(self.namespace)
        if not base_table:
            raise ValueError(f"Unknown namespace: {self.namespace}")

        if self.model_suffix:
            self.table_name = f"{base_table}_{self.model_suffix}"
            logger.info(f"PostgreSQL table: {self.table_name}")
        else:
            self.table_name = base_table
            logger.warning(
                f"PostgreSQL table: {self.table_name} missing suffix. Pls add model_name to embedding_func for proper workspace data isolation."
            )

        self.legacy_table_name = base_table

        if len(self.table_name) > PG_MAX_IDENTIFIER_LENGTH:
            raise ValueError(
                f"PostgreSQL table name exceeds {PG_MAX_IDENTIFIER_LENGTH} character limit: '{self.table_name}' "
                f"(length: {len(self.table_name)}). "
                f"Consider using a shorter embedding model name or workspace name."
            )

    @staticmethod
    async def _pg_create_table(
        db: PostgreSQLDB, table_name: str, base_table: str, embedding_dim: int
    ) -> None:
        """Create a new vector table by replacing the table name in DDL template."""
        if base_table not in TABLES:
            raise ValueError(f"No DDL template found for table: {base_table}")

        ddl_template = TABLES[base_table]["ddl"]

        vector_type = "VECTOR"
        if getattr(db, "vector_index_type", None) == "HNSW_HALFVEC":
            vector_type = "HALFVEC"

        ddl = ddl_template.replace(
            "VECTOR(dimension)", f"{vector_type}({embedding_dim})"
        )

        ddl = ddl.replace(base_table, table_name)

        await db.execute(ddl)

        id_index_name = _safe_index_name(table_name, "id")
        try:
            create_id_index_sql = f"CREATE INDEX {id_index_name} ON {table_name}(id)"
            logger.info(
                f"PostgreSQL, Creating index {id_index_name} on table {table_name}"
            )
            await db.execute(create_id_index_sql)
        except Exception as e:
            logger.error(
                f"PostgreSQL, Failed to create index {id_index_name}, Got: {e}"
            )

        workspace_id_index_name = _safe_index_name(table_name, "workspace_id")
        try:
            create_composite_index_sql = (
                f"CREATE INDEX {workspace_id_index_name} ON {table_name}(workspace, id)"
            )
            logger.info(
                f"PostgreSQL, Creating composite index {workspace_id_index_name} on table {table_name}"
            )
            await db.execute(create_composite_index_sql)
        except Exception as e:
            logger.error(
                f"PostgreSQL, Failed to create composite index {workspace_id_index_name}, Got: {e}"
            )

    @staticmethod
    async def _pg_migrate_workspace_data(
        db: PostgreSQLDB,
        legacy_table_name: str,
        new_table_name: str,
        workspace: str,
        expected_count: int,
        _embedding_dim: int,
    ) -> int:
        """Migrate workspace data from legacy table to new table using batch insert."""
        import asyncpg

        migrated_count = 0
        last_id: str | None = None
        batch_size = 500

        while True:
            if workspace:
                if last_id is not None:
                    select_query = f"SELECT * FROM {legacy_table_name} WHERE workspace = $1 AND id > $2 ORDER BY id LIMIT $3"
                    rows = await db.query(
                        select_query, [workspace, last_id, batch_size], multirows=True
                    )
                else:
                    select_query = f"SELECT * FROM {legacy_table_name} WHERE workspace = $1 ORDER BY id LIMIT $2"
                    rows = await db.query(
                        select_query, [workspace, batch_size], multirows=True
                    )
            else:
                if last_id is not None:
                    select_query = f"SELECT * FROM {legacy_table_name} WHERE id > $1 ORDER BY id LIMIT $2"
                    rows = await db.query(
                        select_query, [last_id, batch_size], multirows=True
                    )
                else:
                    select_query = (
                        f"SELECT * FROM {legacy_table_name} ORDER BY id LIMIT $1"
                    )
                    rows = await db.query(select_query, [batch_size], multirows=True)

            if not rows:
                break

            last_id = rows[-1]["id"]

            first_row = dict(rows[0])
            columns = list(first_row.keys())
            columns_str = ", ".join(columns)
            placeholders = ", ".join([f"${i + 1}" for i in range(len(columns))])

            insert_query = f"""
                INSERT INTO {new_table_name} ({columns_str})
                VALUES ({placeholders})
                ON CONFLICT (workspace, id) DO NOTHING
            """

            batch_values = []
            for row in rows:
                row_dict = dict(row)

                if "content_vector" in row_dict:
                    vec = row_dict["content_vector"]
                    if isinstance(vec, str):
                        vec = vec.strip("[]")
                        if vec:
                            row_dict["content_vector"] = np.array(
                                [float(x) for x in vec.split(",")], dtype=np.float32
                            )
                        else:
                            row_dict["content_vector"] = None

                values_tuple = tuple(row_dict[col] for col in columns)
                batch_values.append(values_tuple)

            async def _batch_insert(
                connection: asyncpg.Connection, iq=insert_query, bv=batch_values
            ) -> None:
                await connection.executemany(iq, bv)

            await db._run_with_retry(_batch_insert)

            migrated_count += len(rows)
            workspace_info = f" for workspace '{workspace}'" if workspace else ""
            logger.info(
                f"PostgreSQL: {migrated_count}/{expected_count} records migrated{workspace_info}"
            )

        return migrated_count

    @staticmethod
    async def setup_table(
        db: PostgreSQLDB,
        table_name: str,
        workspace: str,
        embedding_dim: int,
        legacy_table_name: str,
        base_table: str,
    ):
        """Setup PostgreSQL table with migration support from legacy tables."""
        if not workspace:
            raise ValueError("workspace must be provided")

        new_table_exists = await db.check_table_exists(table_name)
        legacy_exists = legacy_table_name and await db.check_table_exists(
            legacy_table_name
        )

        if (new_table_exists and not legacy_exists) or (
            new_table_exists and (table_name.lower() == legacy_table_name.lower())
        ):
            await db._create_vector_index(table_name, embedding_dim)

            workspace_count_query = (
                f"SELECT COUNT(*) as count FROM {table_name} WHERE workspace = $1"
            )
            workspace_count_result = await db.query(workspace_count_query, [workspace])
            workspace_count = (
                workspace_count_result.get("count", 0) if workspace_count_result else 0
            )
            if workspace_count == 0 and not (
                table_name.lower() == legacy_table_name.lower()
            ):
                logger.warning(
                    f"PostgreSQL: workspace data in table '{table_name}' is empty. "
                    f"Ensure it is caused by new workspace setup and not an unexpected embedding model change."
                )

            return

        legacy_count = None
        if not new_table_exists:
            if legacy_exists:
                count_query = f"SELECT COUNT(*) as count FROM {legacy_table_name} WHERE workspace = $1"
                count_result = await db.query(count_query, [workspace])
                legacy_count = count_result.get("count", 0) if count_result else 0

                if legacy_count > 0:
                    legacy_dim = None
                    try:
                        sample_query = f"SELECT content_vector FROM {legacy_table_name} WHERE workspace = $1 LIMIT 1"
                        sample_result = await db.query(sample_query, [workspace])
                        if (
                            sample_result
                            and sample_result.get("content_vector") is not None
                        ):
                            vector_data = sample_result["content_vector"]
                            if isinstance(vector_data, list | tuple):
                                legacy_dim = len(vector_data)
                            elif hasattr(vector_data, "__len__") and not isinstance(
                                vector_data, str
                            ):
                                legacy_dim = len(vector_data)
                            elif isinstance(vector_data, str):
                                vector_list = json.loads(vector_data)
                                legacy_dim = len(vector_list)

                        if legacy_dim and legacy_dim != embedding_dim:
                            logger.error(
                                f"PostgreSQL: Dimension mismatch detected! "
                                f"Legacy table '{legacy_table_name}' has {legacy_dim}d vectors, "
                                f"but new embedding model expects {embedding_dim}d."
                            )
                            raise DataMigrationError(
                                f"Dimension mismatch between legacy table '{legacy_table_name}' "
                                f"and new embedding model. Expected {embedding_dim}d but got {legacy_dim}d."
                            )

                    except DataMigrationError:
                        raise
                    except Exception as e:
                        raise DataMigrationError(
                            f"Could not verify legacy table vector dimension: {e}. "
                            f"Proceeding with caution..."
                        ) from e

            await PGVectorStorage._pg_create_table(
                db, table_name, base_table, embedding_dim
            )
            logger.info(f"PostgreSQL: New table '{table_name}' created successfully")

            if not legacy_exists:
                await db._create_vector_index(table_name, embedding_dim)
                logger.info(
                    "Ensure this new table creation is caused by new workspace setup and not an unexpected embedding model change."
                )
                return

        await db._create_vector_index(table_name, embedding_dim)

        if legacy_exists:
            workspace_info = f" for workspace '{workspace}'"

            f"SELECT COUNT total_count_query =(*) as count FROM {legacy_table_name}"
            total_count_result = await db.query(total_count_query, [])
            total_count = (
                total_count_result.get("count", 0) if total_count_result else 0
            )
            if total_count == 0:
                logger.info(
                    f"PostgreSQL: Empty legacy table '{legacy_table_name}' deleted successfully"
                )
                drop_query = f"DROP TABLE {legacy_table_name}"
                await db.execute(drop_query, None)
                return

            if legacy_count is None:
                count_query = f"SELECT COUNT(*) as count FROM {legacy_table_name} WHERE workspace = $1"
                count_result = await db.query(count_query, [workspace])
                legacy_count = count_result.get("count", 0) if count_result else 0

            if legacy_count == 0:
                logger.info(
                    f"PostgreSQL: No records{workspace_info} found in legacy table. "
                    f"No data migration needed."
                )
                return

            new_count_query = (
                f"SELECT COUNT(*) as count FROM {table_name} WHERE workspace = $1"
            )
            new_count_result = await db.query(new_count_query, [workspace])
            new_table_workspace_count = (
                new_count_result.get("count", 0) if new_count_result else 0
            )

            if new_table_workspace_count > 0:
                logger.warning(
                    f"PostgreSQL: Both new and legacy collection have data. "
                    f"{legacy_count} records in {legacy_table_name} require manual deletion after migration verification."
                )
                return

            logger.info(
                f"PostgreSQL: Found legacy table '{legacy_table_name}' with {legacy_count} records{workspace_info}."
            )
            logger.info(
                f"PostgreSQL: Migrating data from legacy table '{legacy_table_name}' to new table '{table_name}'"
            )

            try:
                migrated_count = await PGVectorStorage._pg_migrate_workspace_data(
                    db,
                    legacy_table_name,
                    table_name,
                    workspace,
                    legacy_count,
                    embedding_dim,
                )
                if migrated_count != legacy_count:
                    logger.warning(
                        "PostgreSQL: Read %s legacy records%s during migration, expected %s.",
                        migrated_count,
                        workspace_info,
                        legacy_count,
                    )

                new_count_result = await db.query(new_count_query, [workspace])
                new_table_count_after = (
                    new_count_result.get("count", 0) if new_count_result else 0
                )
                inserted_count = new_table_count_after - new_table_workspace_count

                if inserted_count != legacy_count:
                    error_msg = (
                        "PostgreSQL: Migration verification failed, "
                        f"expected {legacy_count} inserted records, got {inserted_count}."
                    )
                    logger.error(error_msg)
                    raise DataMigrationError(error_msg)

            except DataMigrationError:
                raise
            except Exception as e:
                logger.error(
                    f"PostgreSQL: Failed to migrate data from legacy table '{legacy_table_name}' to new table '{table_name}': {e}"
                )
                raise DataMigrationError(
                    f"Failed to migrate data from legacy table '{legacy_table_name}' to new table '{table_name}'"
                ) from e

            logger.info(
                f"PostgreSQL: Migration from '{legacy_table_name}' to '{table_name}' completed successfully"
            )
            logger.warning(
                "PostgreSQL: Manual deletion is required after data migration verification."
            )

    async def initialize(self):
        from lightrag.kg.shared_storage import get_data_init_lock

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

            await PGVectorStorage.setup_table(
                self.db,
                self.table_name,
                self.workspace,
                embedding_dim=self.embedding_func.embedding_dim,
                legacy_table_name=self.legacy_table_name,
                base_table=self.legacy_table_name,
            )

    async def finalize(self):
        if self.db is not None:
            await ClientManager.release_client(self.db)
            self.db = None

    def _upsert_chunks(
        self, item: dict[str, Any], current_time: datetime.datetime
    ) -> tuple[str, tuple[Any, ...]]:
        """Prepare upsert data for chunks."""
        try:
            upsert_sql = SQL_TEMPLATES["upsert_chunk"].format(
                table_name=self.table_name
            )
            values: tuple[Any, ...] = (
                self.workspace,
                item["__id__"],
                item["tokens"],
                item["chunk_order_index"],
                item["full_doc_id"],
                item["content"],
                item["__vector__"],
                item["file_path"],
                current_time,
                current_time,
            )
        except Exception as e:
            logger.error(
                f"[{self.workspace}] Error to prepare upsert,\nerror: {e}\nitem: {item}"
            )
            raise

        return upsert_sql, values

    def _upsert_entities(
        self, item: dict[str, Any], current_time: datetime.datetime
    ) -> tuple[str, tuple[Any, ...]]:
        """Prepare upsert data for entities."""
        upsert_sql = SQL_TEMPLATES["upsert_entity"].format(table_name=self.table_name)
        source_id = item["source_id"]
        if isinstance(source_id, str) and "<SEP>" in source_id:
            chunk_ids = source_id.split("<SEP>")
        else:
            chunk_ids = [source_id]

        values: tuple[Any, ...] = (
            self.workspace,
            item["__id__"],
            item["entity_name"],
            item["content"],
            item["__vector__"],
            chunk_ids,
            item.get("file_path", None),
            current_time,
            current_time,
        )
        return upsert_sql, values

    def _upsert_relationships(
        self, item: dict[str, Any], current_time: datetime.datetime
    ) -> tuple[str, tuple[Any, ...]]:
        """Prepare upsert data for relationships."""
        upsert_sql = SQL_TEMPLATES["upsert_relationship"].format(
            table_name=self.table_name
        )
        source_id = item["source_id"]
        if isinstance(source_id, str) and "<SEP>" in source_id:
            chunk_ids = source_id.split("<SEP>")
        else:
            chunk_ids = [source_id]

        values: tuple[Any, ...] = (
            self.workspace,
            item["__id__"],
            item["src_id"],
            item["tgt_id"],
            item["content"],
            item["__vector__"],
            chunk_ids,
            item.get("file_path", None),
            current_time,
            current_time,
        )
        return upsert_sql, values

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        import asyncpg
        from datetime import timezone

        logger.debug(f"[{self.workspace}] Inserting {len(data)} to {self.namespace}")
        if not data:
            return

        current_time = datetime.datetime.now(timezone.utc).replace(tzinfo=None)
        list_data = [
            {
                "__id__": k,
                **dict(v.items()),
            }
            for k, v in data.items()
        ]
        contents = [v["content"] for v in data.values()]
        batches = [
            contents[i : i + self._max_batch_size]
            for i in range(0, len(contents), self._max_batch_size)
        ]

        embedding_tasks = [self.embedding_func(batch) for batch in batches]
        embeddings_list = await asyncio.gather(*embedding_tasks)

        embeddings = np.concatenate(embeddings_list)
        for i, d in enumerate(list_data):
            d["__vector__"] = embeddings[i]

        batch_values: list[tuple[Any, ...]] = []
        upsert_sql = None

        for item in list_data:
            if is_namespace(self.namespace, NameSpace.VECTOR_STORE_CHUNKS):
                upsert_sql, values = self._upsert_chunks(item, current_time)
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_ENTITIES):
                upsert_sql, values = self._upsert_entities(item, current_time)
            elif is_namespace(self.namespace, NameSpace.VECTOR_STORE_RELATIONSHIPS):
                upsert_sql, values = self._upsert_relationships(item, current_time)
            else:
                raise ValueError(f"{self.namespace} is not supported")

            batch_values.append(values)

        if batch_values and upsert_sql:

            async def _batch_upsert(connection: asyncpg.Connection) -> None:
                await connection.executemany(upsert_sql, batch_values)

            await self.db._run_with_retry(_batch_upsert)
            logger.debug(
                f"[{self.workspace}] Batch upserted {len(batch_values)} records to {self.namespace}"
            )

    async def query(
        self, query: str, top_k: int, query_embedding: list[float] = None
    ) -> list[dict[str, Any]]:
        if query_embedding is not None:
            embedding = query_embedding
        else:
            embeddings = await self.embedding_func([query], _priority=5)
            embedding = embeddings[0]

        embedding_string = ",".join(map(str, embedding))

        sql = SQL_TEMPLATES[self.namespace].format(
            embedding_string=embedding_string, table_name=self.table_name
        )
        params = {
            "workspace": self.workspace,
            "closer_than_threshold": 1 - self.cosine_better_than_threshold,
            "top_k": top_k,
        }
        results = await self.db.query(sql, params=list(params.values()), multirows=True)
        return results

    async def index_done_callback(self) -> None:
        pass

    async def delete(self, ids: list[str]) -> None:
        if not ids:
            return

        delete_sql = (
            f"DELETE FROM {self.table_name} WHERE workspace=$1 AND id = ANY($2)"
        )

        try:
            await self.db.execute(delete_sql, {"workspace": self.workspace, "ids": ids})
            logger.debug(
                f"[{self.workspace}] Successfully deleted {len(ids)} vectors from {self.namespace}"
            )
        except Exception as e:
            logger.error(
                f"[{self.workspace}] Error while deleting vectors from {self.namespace}: {e}"
            )

    async def delete_entity(self, entity_name: str) -> None:
        try:
            delete_sql = f"""DELETE FROM {self.table_name}
                            WHERE workspace=$1 AND entity_name=$2"""

            await self.db.execute(
                delete_sql, {"workspace": self.workspace, "entity_name": entity_name}
            )
            logger.debug(
                f"[{self.workspace}] Successfully deleted entity {entity_name}"
            )
        except Exception as e:
            logger.error(f"[{self.workspace}] Error deleting entity {entity_name}: {e}")

    async def delete_entity_relation(self, entity_name: str) -> None:
        try:
            delete_sql = f"""DELETE FROM {self.table_name}
                            WHERE workspace=$1 AND (source_id=$2 OR target_id=$2)"""

            await self.db.execute(
                delete_sql, {"workspace": self.workspace, "entity_name": entity_name}
            )
            logger.debug(
                f"[{self.workspace}] Successfully deleted relations for entity {entity_name}"
            )
        except Exception as e:
            logger.error(
                f"[{self.workspace}] Error deleting relations for entity {entity_name}: {e}"
            )

    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        query = f"SELECT *, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at FROM {self.table_name} WHERE workspace=$1 AND id=$2"
        params = {"workspace": self.workspace, "id": id}

        try:
            result = await self.db.query(query, list(params.values()))
            if result:
                return dict(result)
            return None
        except Exception as e:
            logger.error(
                f"[{self.workspace}] Error retrieving vector data for ID {id}: {e}"
            )
            return None

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        if not ids:
            return []

        ids_str = ",".join([f"'{id}'" for id in ids])
        query = f"SELECT *, EXTRACT(EPOCH FROM create_time)::BIGINT as created_at FROM {self.table_name} WHERE workspace=$1 AND id IN ({ids_str})"
        params = {"workspace": self.workspace}

        try:
            results = await self.db.query(query, list(params.values()), multirows=True)
            if not results:
                return []

            id_map: dict[str, dict[str, Any]] = {}
            for record in results:
                if record is None:
                    continue
                record_dict = dict(record)
                row_id = record_dict.get("id")
                if row_id is not None:
                    id_map[str(row_id)] = record_dict

            ordered_results: list[dict[str, Any] | None] = []
            for requested_id in ids:
                ordered_results.append(id_map.get(str(requested_id)))
            return ordered_results
        except Exception as e:
            logger.error(
                f"[{self.workspace}] Error retrieving vector data for IDs {ids}: {e}"
            )
            return []

    async def get_vectors_by_ids(self, ids: list[str]) -> dict[str, list[float]]:
        if not ids:
            return {}

        ids_str = ",".join([f"'{id}'" for id in ids])
        query = f"SELECT id, content_vector FROM {self.table_name} WHERE workspace=$1 AND id IN ({ids_str})"
        params = {"workspace": self.workspace}

        try:
            results = await self.db.query(query, list(params.values()), multirows=True)
            vectors_dict = {}

            for result in results:
                if result and "content_vector" in result and "id" in result:
                    try:
                        vector_data = result["content_vector"]
                        if isinstance(vector_data, list | tuple):
                            vectors_dict[result["id"]] = list(vector_data)
                        elif isinstance(vector_data, str):
                            parsed = json.loads(vector_data)
                            if isinstance(parsed, list):
                                vectors_dict[result["id"]] = parsed
                        elif hasattr(vector_data, "tolist"):
                            vectors_dict[result["id"]] = vector_data.tolist()
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(
                            f"[{self.workspace}] Failed to parse vector data for ID {result['id']}: {e}"
                        )

            return vectors_dict
        except Exception as e:
            logger.error(
                f"[{self.workspace}] Error retrieving vectors by IDs from {self.namespace}: {e}"
            )
            return {}

    async def drop(self) -> dict[str, str]:
        try:
            drop_sql = SQL_TEMPLATES["drop_specifiy_table_workspace"].format(
                table_name=self.table_name
            )
            await self.db.execute(drop_sql, {"workspace": self.workspace})
            return {"status": "success", "message": "data dropped"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
