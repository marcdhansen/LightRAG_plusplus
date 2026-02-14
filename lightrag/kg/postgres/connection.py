import asyncio
import configparser
import datetime
import hashlib
import itertools
import json
import os
import re
import ssl
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import numpy as np
import pipmaster as pm
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
)

from lightrag.core_types import KnowledgeGraph, KnowledgeGraphEdge, KnowledgeGraphNode

from lightrag.kg.shared_storage import get_data_init_lock
from lightrag.namespace import NameSpace, is_namespace
from lightrag.utils import logger

if not pm.is_installed("asyncpg"):
    pm.install("asyncpg")
if not pm.is_installed("pgvector"):
    pm.install("pgvector")

import asyncpg  # type: ignore
from asyncpg import Pool  # type: ignore
from dotenv import load_dotenv
from pgvector.asyncpg import register_vector  # type: ignore

load_dotenv(dotenv_path=".env", override=False)

T = TypeVar("T")

PG_MAX_IDENTIFIER_LENGTH = 63


def _safe_index_name(table_name: str, index_suffix: str) -> str:
    """Generate a PostgreSQL-safe index name that won't be truncated."""
    full_name = f"idx_{table_name.lower()}_{index_suffix}"
    if len(full_name.encode("utf-8")) <= PG_MAX_IDENTIFIER_LENGTH:
        return full_name
    hash_input = table_name.lower().encode("utf-8")
    table_hash = hashlib.md5(hash_input).hexdigest()[:12]
    shortened_name = f"idx_{table_hash}_{index_suffix}"
    return shortened_name


def _dollar_quote(s: str, tag_prefix: str = "AGE") -> str:
    """Generate a PostgreSQL dollar-quoted string with a unique tag."""
    s = "" if s is None else str(s)
    for i in itertools.count(1):
        tag = f"{tag_prefix}{i}"
        wrapper = f"${tag}$"
        if wrapper not in s:
            return f"{wrapper}{s}{wrapper}"


class PostgreSQLDB:
    def __init__(self, config: dict[str, Any], **_kwargs: Any):
        self.host = config["host"]
        self.port = config["port"]
        self.user = config["user"]
        self.password = config["password"]
        self.database = config["database"]
        self.workspace = config["workspace"]
        self.max = int(config["max_connections"])
        self.increment = 1
        self.pool: Pool | None = None

        self.ssl_mode = config.get("ssl_mode")
        self.ssl_cert = config.get("ssl_cert")
        self.ssl_key = config.get("ssl_key")
        self.ssl_root_cert = config.get("ssl_root_cert")
        self.ssl_crl = config.get("ssl_crl")

        self.vector_index_type = config.get("vector_index_type")
        self.hnsw_m = config.get("hnsw_m")
        self.hnsw_ef = config.get("hnsw_ef")
        self.ivfflat_lists = config.get("ivfflat_lists")
        self.vchordrq_build_options = config.get("vchordrq_build_options")
        self.vchordrq_probes = config.get("vchordrq_probes")
        self.vchordrq_epsilon = config.get("vchordrq_epsilon")

        self.server_settings = config.get("server_settings")
        self.statement_cache_size = config.get("statement_cache_size")

        if self.user is None or self.password is None or self.database is None:
            raise ValueError("Missing database user, password, or database")

        self._pool_reconnect_lock = asyncio.Lock()

        self._transient_exceptions = (
            asyncio.TimeoutError,
            TimeoutError,
            ConnectionError,
            OSError,
            asyncpg.exceptions.InterfaceError,
            asyncpg.exceptions.TooManyConnectionsError,
            asyncpg.exceptions.CannotConnectNowError,
            asyncpg.exceptions.PostgresConnectionError,
            asyncpg.exceptions.ConnectionDoesNotExistError,
            asyncpg.exceptions.ConnectionFailureError,
        )

        self.connection_retry_attempts = config["connection_retry_attempts"]
        self.connection_retry_backoff = config["connection_retry_backoff"]
        self.connection_retry_backoff_max = max(
            self.connection_retry_backoff,
            config["connection_retry_backoff_max"],
        )
        self.pool_close_timeout = config["pool_close_timeout"]
        logger.info(
            "PostgreSQL, Retry config: attempts=%s, backoff=%.1fs, backoff_max=%.1fs, pool_close_timeout=%.1fs",
            self.connection_retry_attempts,
            self.connection_retry_backoff,
            self.connection_retry_backoff_max,
            self.pool_close_timeout,
        )

    def _create_ssl_context(self) -> ssl.SSLContext | None:
        """Create SSL context based on configuration parameters."""
        if not self.ssl_mode:
            return None

        ssl_mode = self.ssl_mode.lower()

        if ssl_mode in ["disable", "allow", "prefer", "require"]:
            if ssl_mode == "disable":
                return None
            elif ssl_mode in ["require", "prefer", "allow"]:
                return None

        if ssl_mode in ["verify-ca", "verify-full"]:
            try:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

                if ssl_mode == "verify-ca":
                    context.check_hostname = False
                elif ssl_mode == "verify-full":
                    context.check_hostname = True

                if self.ssl_root_cert:
                    if os.path.exists(self.ssl_root_cert):
                        context.load_verify_locations(cafile=self.ssl_root_cert)
                        logger.info(
                            f"PostgreSQL, Loaded SSL root certificate: {self.ssl_root_cert}"
                        )
                    else:
                        logger.warning(
                            f"PostgreSQL, SSL root certificate file not found: {self.ssl_root_cert}"
                        )

                if self.ssl_cert and self.ssl_key:
                    if os.path.exists(self.ssl_cert) and os.path.exists(self.ssl_key):
                        context.load_cert_chain(self.ssl_cert, self.ssl_key)
                        logger.info(
                            f"PostgreSQL, Loaded SSL client certificate: {self.ssl_cert}"
                        )
                    else:
                        logger.warning(
                            "PostgreSQL, SSL client certificate or key file not found"
                        )

                if self.ssl_crl:
                    if os.path.exists(self.ssl_crl):
                        context.load_verify_locations(crlfile=self.ssl_crl)
                        logger.info(f"PostgreSQL, Loaded SSL CRL: {self.ssl_crl}")
                    else:
                        logger.warning(
                            f"PostgreSQL, SSL CRL file not found: {self.ssl_crl}"
                        )

                return context

            except Exception as e:
                logger.error(f"PostgreSQL, Failed to create SSL context: {e}")
                raise ValueError(f"SSL configuration error: {e}") from e

        logger.warning(f"PostgreSQL, Unknown SSL mode: {ssl_mode}, SSL disabled")
        return None

    async def initdb(self):
        connection_params = {
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "host": self.host,
            "port": self.port,
            "min_size": 1,
            "max_size": self.max,
        }

        if self.statement_cache_size is not None:
            connection_params["statement_cache_size"] = int(self.statement_cache_size)
            logger.info(
                f"PostgreSQL, statement LRU cache size set as: {self.statement_cache_size}"
            )

        ssl_context = self._create_ssl_context()
        if ssl_context is not None:
            connection_params["ssl"] = ssl_context
            logger.info("PostgreSQL, SSL configuration applied")
        elif self.ssl_mode:
            if self.ssl_mode.lower() in ["require", "prefer"]:
                connection_params["ssl"] = True
            elif self.ssl_mode.lower() == "disable":
                connection_params["ssl"] = False
            logger.info(f"PostgreSQL, SSL mode set to: {self.ssl_mode}")

        if self.server_settings:
            try:
                settings = {}
                pairs = self.server_settings.split("&")
                for pair in pairs:
                    if "=" in pair:
                        key, value = pair.split("=", 1)
                        settings[key] = value
                if settings:
                    connection_params["server_settings"] = settings
                    logger.info(f"PostgreSQL, Server settings applied: {settings}")
            except Exception as e:
                logger.warning(
                    f"PostgreSQL, Failed to parse server_settings: {self.server_settings}, error: {e}"
                )

        wait_strategy = (
            wait_exponential(
                multiplier=self.connection_retry_backoff,
                min=self.connection_retry_backoff,
                max=self.connection_retry_backoff_max,
            )
            if self.connection_retry_backoff > 0
            else wait_fixed(0)
        )

        async def _init_connection(connection: asyncpg.Connection) -> None:
            await register_vector(connection)

        async def _create_pool_once() -> None:
            bootstrap_conn = await asyncpg.connect(
                user=self.user,
                password=self.password,
                database=self.database,
                host=self.host,
                port=self.port,
                ssl=connection_params.get("ssl"),
            )
            try:
                await self.configure_vector_extension(bootstrap_conn)
            finally:
                await bootstrap_conn.close()

            pool = await asyncpg.create_pool(
                **connection_params,
                init=_init_connection,
            )
            self.pool = pool

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self.connection_retry_attempts),
                retry=retry_if_exception_type(self._transient_exceptions),
                wait=wait_strategy,
                before_sleep=self._before_sleep,
                reraise=True,
            ):
                with attempt:
                    await _create_pool_once()

            ssl_status = "with SSL" if connection_params.get("ssl") else "without SSL"
            logger.info(
                f"PostgreSQL, Connected to database at {self.host}:{self.port}/{self.database} {ssl_status}"
            )
        except Exception as e:
            logger.error(
                f"PostgreSQL, Failed to connect database at {self.host}:{self.port}/{self.database}, Got:{e}"
            )
            raise

    async def _ensure_pool(self) -> None:
        """Ensure the connection pool is initialised."""
        if self.pool is None:
            async with self._pool_reconnect_lock:
                if self.pool is None:
                    await self.initdb()

    async def _reset_pool(self) -> None:
        async with self._pool_reconnect_lock:
            if self.pool is not None:
                try:
                    await asyncio.wait_for(
                        self.pool.close(), timeout=self.pool_close_timeout
                    )
                except asyncio.TimeoutError:
                    logger.error(
                        "PostgreSQL, Timed out closing connection pool after %.2fs",
                        self.pool_close_timeout,
                    )
                except Exception as close_error:
                    logger.warning(
                        f"PostgreSQL, Failed to close existing connection pool cleanly: {close_error!r}"
                    )
            self.pool = None

    async def _before_sleep(self, retry_state: RetryCallState) -> None:
        """Hook invoked by tenacity before sleeping between retries."""
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        logger.warning(
            "PostgreSQL transient connection issue on attempt %s/%s: %r",
            retry_state.attempt_number,
            self.connection_retry_attempts,
            exc,
        )
        await self._reset_pool()

    async def _run_with_retry(
        self,
        operation: Callable[[asyncpg.Connection], Awaitable[T]],
        *,
        with_age: bool = False,
        graph_name: str | None = None,
    ) -> T:
        """Execute a database operation with automatic retry for transient failures."""
        wait_strategy = (
            wait_exponential(
                multiplier=self.connection_retry_backoff,
                min=self.connection_retry_backoff,
                max=self.connection_retry_backoff_max,
            )
            if self.connection_retry_backoff > 0
            else wait_fixed(0)
        )

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.connection_retry_attempts),
            retry=retry_if_exception_type(self._transient_exceptions),
            wait=wait_strategy,
            before_sleep=self._before_sleep,
            reraise=True,
        ):
            with attempt:
                await self._ensure_pool()
                assert self.pool is not None
                async with self.pool.acquire() as connection:
                    if with_age and graph_name:
                        await self.configure_age(connection, graph_name)
                    elif with_age and not graph_name:
                        raise ValueError("Graph name is required when with_age is True")
                    if self.vector_index_type == "VCHORDRQ":
                        await self.configure_vchordrq(connection)
                    return await operation(connection)

    @staticmethod
    async def configure_vector_extension(connection: asyncpg.Connection) -> None:
        """Create VECTOR extension if it doesn't exist for vector similarity operations."""
        try:
            await connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
            logger.info("PostgreSQL, VECTOR extension enabled")
        except Exception as e:
            logger.warning(f"Could not create VECTOR extension: {e}")

    @staticmethod
    async def configure_age_extension(connection: asyncpg.Connection) -> None:
        """Create AGE extension if it doesn't exist for graph operations."""
        try:
            await connection.execute("CREATE EXTENSION IF NOT EXISTS AGE CASCADE")
            logger.info("PostgreSQL, AGE extension enabled")
        except Exception as e:
            logger.warning(f"Could not create AGE extension: {e}")

    @staticmethod
    async def configure_age(connection: asyncpg.Connection, graph_name: str) -> None:
        """Set the Apache AGE environment and creates a graph if it does not exist."""
        try:
            await connection.execute('SET search_path = ag_catalog, "$user", public')
            await connection.execute(f"select create_graph('{graph_name}')")
        except (
            asyncpg.exceptions.InvalidSchemaNameError,
            asyncpg.exceptions.UniqueViolationError,
        ):
            pass

    async def configure_vchordrq(self, connection: asyncpg.Connection) -> None:
        """Configure VCHORDRQ extension for vector similarity search."""
        if self.vchordrq_probes and str(self.vchordrq_probes).strip():
            await connection.execute(f"SET vchordrq.probes TO '{self.vchordrq_probes}'")
            logger.debug(f"PostgreSQL, VCHORDRQ probes set to: {self.vchordrq_probes}")

        if self.vchordrq_epsilon is not None:
            await connection.execute(f"SET vchordrq.epsilon TO {self.vchordrq_epsilon}")
            logger.debug(
                f"PostgreSQL, VCHORDRQ epsilon set to: {self.vchordrq_epsilon}"
            )

    async def _migrate_llm_cache_schema(self):
        """Migrate LLM cache schema: add new columns and remove deprecated mode field"""
        try:
            check_columns_sql = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'lightrag_llm_cache'
            AND column_name IN ('chunk_id', 'cache_type', 'queryparam', 'mode')
            """

            existing_columns = await self.query(check_columns_sql, multirows=True)
            existing_column_names = (
                {col["column_name"] for col in existing_columns}
                if existing_columns
                else set()
            )

            if "chunk_id" not in existing_column_names:
                logger.info("Adding chunk_id column to LIGHTRAG_LLM_CACHE table")
                add_chunk_id_sql = """
                ALTER TABLE LIGHTRAG_LLM_CACHE
                ADD COLUMN chunk_id VARCHAR(255) NULL
                """
                await self.execute(add_chunk_id_sql)
                logger.info(
                    "Successfully added chunk_id column to LIGHTRAG_LLM_CACHE table"
                )
            else:
                logger.info(
                    "chunk_id column already exists in LIGHTRAG_LLM_CACHE table"
                )

            if "cache_type" not in existing_column_names:
                logger.info("Adding cache_type column to LIGHTRAG_LLM_CACHE table")
                add_cache_type_sql = """
                ALTER TABLE LIGHTRAG_LLM_CACHE
                ADD COLUMN cache_type VARCHAR(32) NULL
                """
                await self.execute(add_cache_type_sql)
                logger.info(
                    "Successfully added cache_type column to LIGHTRAG_LLM_CACHE table"
                )

                logger.info(
                    "Migrating existing LLM cache data to populate cache_type field (optimized)"
                )
                optimized_update_sql = """
                UPDATE LIGHTRAG_LLM_CACHE
                SET cache_type = CASE
                    WHEN id ~ '^[^:]+:[^:]+:' THEN split_part(id, ':', 2)
                    ELSE 'extract'
                END
                WHERE cache_type IS NULL
                """
                await self.execute(optimized_update_sql)
                logger.info("Successfully migrated existing LLM cache data")
            else:
                logger.info(
                    "cache_type column already exists in LIGHTRAG_LLM_CACHE table"
                )

            if "queryparam" not in existing_column_names:
                logger.info("Adding queryparam column to LIGHTRAG_LLM_CACHE table")
                add_queryparam_sql = """
                ALTER TABLE LIGHTRAG_LLM_CACHE
                ADD COLUMN queryparam JSONB NULL
                """
                await self.execute(add_queryparam_sql)
                logger.info(
                    "Successfully added queryparam column to LIGHTRAG_LLM_CACHE table"
                )
            else:
                logger.info(
                    "queryparam column already exists in LIGHTRAG_LLM_CACHE table"
                )

            if "mode" in existing_column_names:
                logger.info(
                    "Removing deprecated mode column from LIGHTRAG_LLM_CACHE table"
                )

                drop_pk_sql = """
                ALTER TABLE LIGHTRAG_LLM_CACHE
                DROP CONSTRAINT IF EXISTS LIGHTRAG_LLM_CACHE_PK
                """
                await self.execute(drop_pk_sql)
                logger.info("Dropped old primary key constraint")

                drop_mode_sql = """
                ALTER TABLE LIGHTRAG_LLM_CACHE
                DROP COLUMN mode
                """
                await self.execute(drop_mode_sql)
                logger.info(
                    "Successfully removed mode column from LIGHTRAG_LLM_CACHE table"
                )

                add_pk_sql = """
                ALTER TABLE LIGHTRAG_LLM_CACHE
                ADD CONSTRAINT LIGHTRAG_LLM_CACHE_PK PRIMARY KEY (workspace, id)
                """
                await self.execute(add_pk_sql)
                logger.info("Created new primary key constraint (workspace, id)")
            else:
                logger.info("mode column does not exist in LIGHTRAG_LLM_CACHE table")

        except Exception as e:
            logger.warning(f"Failed to migrate LLM cache schema: {e}")

    async def _migrate_timestamp_columns(self):
        """Migrate timestamp columns in tables to timezone-free types."""
        tables_to_migrate = {
            "LIGHTRAG_VDB_ENTITY": ["create_time", "update_time"],
            "LIGHTRAG_VDB_RELATION": ["create_time", "update_time"],
            "LIGHTRAG_DOC_CHUNKS": ["create_time", "update_time"],
            "LIGHTRAG_DOC_STATUS": ["created_at", "updated_at"],
        }

        try:
            existing_tables = {}
            for table_name, columns in tables_to_migrate.items():
                if await self.check_table_exists(table_name):
                    existing_tables[table_name] = columns
                else:
                    logger.debug(
                        f"Table {table_name} does not exist, skipping timestamp migration"
                    )

            if not existing_tables:
                logger.debug("No tables found for timestamp migration")
                return

            tables_to_migrate = existing_tables

            table_names_lower = [t.lower() for t in tables_to_migrate.keys()]
            all_column_names = list(
                {col for cols in tables_to_migrate.values() for col in cols}
            )

            check_all_columns_sql = """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_name = ANY($1)
            AND column_name = ANY($2)
            """

            all_columns_result = await self.query(
                check_all_columns_sql,
                [table_names_lower, all_column_names],
                multirows=True,
            )

            column_types = {}
            if all_columns_result:
                column_types = {
                    (row["table_name"].upper(), row["column_name"]): row["data_type"]
                    for row in all_columns_result
                }

            for table_name, columns in tables_to_migrate.items():
                for column_name in columns:
                    try:
                        data_type = column_types.get((table_name, column_name))

                        if not data_type:
                            logger.warning(
                                f"Column {table_name}.{column_name} does not exist, skipping migration"
                            )
                            continue

                        if data_type == "timestamp without time zone":
                            logger.debug(
                                f"Column {table_name}.{column_name} is already timezone-free, no migration needed"
                            )
                            continue

                        logger.info(
                            f"Migrating {table_name}.{column_name} from {data_type} to TIMESTAMP(0) type"
                        )
                        migration_sql = f"""
                        ALTER TABLE {table_name}
                        ALTER COLUMN {column_name} TYPE TIMESTAMP(0),
                        ALTER COLUMN {column_name} SET DEFAULT CURRENT_TIMESTAMP
                        """

                        await self.execute(migration_sql)
                        logger.info(
                            f"Successfully migrated {table_name}.{column_name} to timezone-free type"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to migrate {table_name}.{column_name}: {e}"
                        )
        except Exception as e:
            logger.error(f"Failed to batch check timestamp columns: {e}")

    async def _migrate_doc_chunks_to_vdb_chunks(self):
        """Migrate data from LIGHTRAG_DOC_CHUNKS to LIGHTRAG_VDB_CHUNKS."""
        try:
            vdb_chunks_exists = await self.check_table_exists("LIGHTRAG_VDB_CHUNKS")
            doc_chunks_exists = await self.check_table_exists("LIGHTRAG_DOC_CHUNKS")

            if not vdb_chunks_exists:
                logger.debug(
                    "Skipping migration: LIGHTRAG_VDB_CHUNKS table does not exist"
                )
                return

            if not doc_chunks_exists:
                logger.debug(
                    "Skipping migration: LIGHTRAG_DOC_CHUNKS table does not exist"
                )
                return

            vdb_chunks_count_sql = "SELECT COUNT(1) as count FROM LIGHTRAG_VDB_CHUNKS"
            vdb_chunks_count_result = await self.query(vdb_chunks_count_sql)
            if vdb_chunks_count_result and vdb_chunks_count_result["count"] > 0:
                logger.info(
                    "Skipping migration: LIGHTRAG_VDB_CHUNKS already contains data."
                )
                return

            check_column_sql = """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'lightrag_doc_chunks' AND column_name = 'content_vector'
            """
            column_exists = await self.query(check_column_sql)
            if not column_exists:
                logger.info(
                    "Skipping migration: `content_vector` not found in LIGHTRAG_DOC_CHUNKS"
                )
                return

            doc_chunks_count_sql = "SELECT COUNT(1) as count FROM LIGHTRAG_DOC_CHUNKS"
            doc_chunks_count_result = await self.query(doc_chunks_count_sql)
            if not doc_chunks_count_result or doc_chunks_count_result["count"] == 0:
                logger.info("Skipping migration: LIGHTRAG_DOC_CHUNKS is empty.")
                return

            logger.info(
                "Starting data migration from LIGHTRAG_DOC_CHUNKS to LIGHTRAG_VDB_CHUNKS..."
            )
            migration_sql = """
            INSERT INTO LIGHTRAG_VDB_CHUNKS (
                id, workspace, full_doc_id, chunk_order_index, tokens, content,
                content_vector, file_path, create_time, update_time
            )
            SELECT
                id, workspace, full_doc_id, chunk_order_index, tokens, content,
                content_vector, file_path, create_time, update_time
            FROM LIGHTRAG_DOC_CHUNKS
            ON CONFLICT (workspace, id) DO NOTHING;
            """
            await self.execute(migration_sql)
            logger.info("Data migration to LIGHTRAG_VDB_CHUNKS completed successfully.")

        except Exception as e:
            logger.error(f"Failed during data migration to LIGHTRAG_VDB_CHUNKS: {e}")

    async def _check_llm_cache_needs_migration(self):
        """Check if LLM cache data needs migration."""
        try:
            check_sql = """
            SELECT 1 FROM LIGHTRAG_LLM_CACHE
            WHERE id NOT LIKE '%:%'
            LIMIT 1
            """
            result = await self.query(check_sql)
            return result is not None

        except Exception as e:
            logger.warning(f"Failed to check LLM cache migration status: {e}")
            return False

    async def _migrate_llm_cache_to_flattened_keys(self):
        """Migrate old format cache keys to flattened format."""
        try:
            check_sql = """
            SELECT COUNT(*) as count FROM LIGHTRAG_LLM_CACHE
            WHERE id NOT LIKE '%:%'
            """
            result = await self.query(check_sql)

            if not result or result["count"] == 0:
                logger.info("No old format LLM cache data found, skipping migration")
                return

            old_count = result["count"]
            logger.info(f"Found {old_count} old format cache records")

            conflict_check_sql = """
            WITH new_ids AS (
                SELECT
                    workspace,
                    mode,
                    id as old_id,
                    mode || ':' ||
                    CASE WHEN mode = 'default' THEN 'extract' ELSE 'unknown' END || ':' ||
                    md5(original_prompt) as new_id
                FROM LIGHTRAG_LLM_CACHE
                WHERE id NOT LIKE '%:%'
            )
            SELECT COUNT(*) as conflicts
            FROM new_ids n1
            JOIN LIGHTRAG_LLM_CACHE existing
            ON existing.workspace = n1.workspace
            AND existing.mode = n1.mode
            AND existing.id = n1.new_id
            WHERE existing.id LIKE '%:%'
            """

            conflict_result = await self.query(conflict_check_sql)
            if conflict_result and conflict_result["conflicts"] > 0:
                logger.warning(
                    f"Found {conflict_result['conflicts']} potential ID conflicts with existing records"
                )

            logger.info("Starting optimized LLM cache migration...")
            migration_sql = """
            UPDATE LIGHTRAG_LLM_CACHE
            SET
                id = mode || ':' ||
                     CASE WHEN mode = 'default' THEN 'extract' ELSE 'unknown' END || ':' ||
                     md5(original_prompt),
                cache_type = CASE WHEN mode = 'default' THEN 'extract' ELSE 'unknown' END,
                update_time = CURRENT_TIMESTAMP
            WHERE id NOT LIKE '%:%'
            """
            await self.execute(migration_sql)
            logger.info("LLM cache migration completed successfully.")

        except Exception as e:
            logger.warning(f"Failed to migrate LLM cache: {e}")

    async def check_tables(self):
        """Check and initialize database tables."""
        tables = [
            "LIGHTRAG_VDB_ENTITY",
            "LIGHTRAG_VDB_RELATION",
            "LIGHTRAG_DOC_CHUNKS",
            "LIGHTRAG_DOC_STATUS",
            "LIGHTRAG_LLM_CACHE",
            "LIGHTRAG_VDB_CHUNKS",
        ]

        async def _check_and_create_table(table_name: str, sql: str):
            try:
                if not await self.check_table_exists(table_name):
                    await self.execute(sql)
                    logger.info(f"PostgreSQL, Table {table_name} created")
                else:
                    logger.debug(f"PostgreSQL, Table {table_name} already exists")
            except Exception as e:
                logger.error(f"PostgreSQL, Failed to create table {table_name}: {e}")
                raise

        for table in tables:
            if table == "LIGHTRAG_VDB_ENTITY":
                await _check_and_create_table(
                    table,
                    """CREATE TABLE IF NOT EXISTS LIGHTRAG_VDB_ENTITY (
                        id VARCHAR(65535),
                        workspace VARCHAR(65535),
                        entity_data JSONB,
                        create_time TIMESTAMP(0),
                        update_time TIMESTAMP(0),
                        PRIMARY KEY (workspace, id)
                    )""",
                )
            elif table == "LIGHTRAG_VDB_RELATION":
                await _check_and_create_table(
                    table,
                    """CREATE TABLE IF NOT EXISTS LIGHTRAG_VDB_RELATION (
                        id VARCHAR(65535),
                        workspace VARCHAR(65535),
                        relation_data JSONB,
                        create_time TIMESTAMP(0),
                        update_time TIMESTAMP(0),
                        PRIMARY KEY (workspace, id)
                    )""",
                )
            elif table == "LIGHTRAG_DOC_CHUNKS":
                await _check_and_create_table(
                    table,
                    """CREATE TABLE IF NOT EXISTS LIGHTRAG_DOC_CHUNKS (
                        id VARCHAR(65535),
                        workspace VARCHAR(65535),
                        full_doc_id VARCHAR(65535),
                        chunk_order_index BIGINT,
                        tokens BIGINT,
                        content TEXT,
                        file_path VARCHAR(65535),
                        create_time TIMESTAMP(0),
                        update_time TIMESTAMP(0),
                        PRIMARY KEY (workspace, id)
                    )""",
                )
            elif table == "LIGHTRAG_DOC_STATUS":
                await _check_and_create_table(
                    table,
                    """CREATE TABLE IF NOT EXISTS LIGHTRAG_DOC_STATUS (
                        id VARCHAR(65535),
                        workspace VARCHAR(65535),
                        doc_name VARCHAR(65535),
                        doc_status VARCHAR(32),
                        chunk_size BIGINT,
                        tokens BIGINT,
                        created_at TIMESTAMP(0),
                        updated_at TIMESTAMP(0),
                        completed_at TIMESTAMP(0),
                        error_msg TEXT,
                        PRIMARY KEY (workspace, id)
                    )""",
                )
            elif table == "LIGHTRAG_LLM_CACHE":
                await _check_and_create_table(
                    table,
                    """CREATE TABLE IF NOT EXISTS LIGHTRAG_LLM_CACHE (
                        id VARCHAR(65535),
                        workspace VARCHAR(65535),
                        original_prompt TEXT,
                        return_value TEXT,
                        cache_type VARCHAR(32),
                        chunk_id VARCHAR(255),
                        queryparam JSONB,
                        create_time TIMESTAMP(0),
                        update_time TIMESTAMP(0),
                        PRIMARY KEY (workspace, id)
                    )""",
                )
            elif table == "LIGHTRAG_VDB_CHUNKS":
                await _check_and_create_table(
                    table,
                    """CREATE TABLE IF NOT EXISTS LIGHTRAG_VDB_CHUNKS (
                        id VARCHAR(65535),
                        workspace VARCHAR(65535),
                        full_doc_id VARCHAR(65535),
                        chunk_order_index BIGINT,
                        tokens BIGINT,
                        content TEXT,
                        content_vector vector,
                        file_path VARCHAR(65535),
                        create_time TIMESTAMP(0),
                        update_time TIMESTAMP(0),
                        PRIMARY KEY (workspace, id)
                    )""",
                )

        async def _create_table_index(
            table_name: str, index_name: str, columns: str, if_not_exists: bool = True
        ):
            sql = f"CREATE INDEX {if_not_exists and 'IF NOT EXISTS ' or ''}{index_name} ON {table_name} ({columns})"
            try:
                await self.execute(sql)
            except Exception as e:
                logger.debug(f"PostgreSQL, Error creating index {index_name}: {e}")

        await _create_table_index(
            "LIGHTRAG_VDB_ENTITY",
            _safe_index_name("LIGHTRAG_VDB_ENTITY", "workspace"),
            "workspace",
        )
        await _create_table_index(
            "LIGHTRAG_VDB_RELATION",
            _safe_index_name("LIGHTRAG_VDB_RELATION", "workspace"),
            "workspace",
        )
        await _create_table_index(
            "LIGHTRAG_DOC_CHUNKS",
            _safe_index_name("LIGHTRAG_DOC_CHUNKS", "workspace_full_doc"),
            "workspace, full_doc_id",
        )
        await _create_table_index(
            "LIGHTRAG_DOC_STATUS",
            _safe_index_name("LIGHTRAG_DOC_STATUS", "workspace_status"),
            "workspace, doc_status",
        )
        await _create_table_index(
            "LIGHTRAG_LLM_CACHE",
            _safe_index_name("LIGHTRAG_LLM_CACHE", "workspace"),
            "workspace",
        )
        await _create_table_index(
            "LIGHTRAG_LLM_CACHE",
            _safe_index_name("LIGHTRAG_LLM_CACHE", "workspace_original_prompt"),
            "workspace, original_prompt",
        )
        await _create_table_index(
            "LIGHTRAG_VDB_CHUNKS",
            _safe_index_name("LIGHTRAG_VDB_CHUNKS", "workspace_full_doc"),
            "workspace, full_doc_id",
        )

        vector_column = "content_vector"
        vector_index_name = _safe_index_name(
            "LIGHTRAG_VDB_CHUNKS",
            f"hnsw_{self.vector_index_type.lower()}"
            if self.vector_index_type
            else "hnsw_cosine",
        )
        index_type = self.vector_index_type or "HNSW"

        if index_type == "HNSW":
            await _create_table_index(
                "LIGHTRAG_VDB_CHUNKS",
                vector_index_name,
                f"{vector_column} vector_cosine_ops)",
                if_not_exists=False,
            )
            sql = f"CREATE INDEX IF NOT EXISTS {vector_index_name} ON LIGHTRAG_VDB_CHUNKS USING hnsw ({vector_column} vector_cosine_ops) WITH (m = {self.hnsw_m}, ef_construction = {self.hnsw_ef})"
            try:
                await self.execute(sql)
            except Exception as e:
                logger.debug(f"PostgreSQL, Error creating HNSW index: {e}")

        elif index_type == "IVFFlat":
            sql = f"CREATE INDEX IF NOT EXISTS {vector_index_name} ON LIGHTRAG_VDB_CHUNKS USING ivfflat ({vector_column} vector_cosine_ops) WITH (lists = {self.ivfflat_lists})"
            try:
                await self.execute(sql)
            except Exception as e:
                logger.debug(f"PostgreSQL, Error creating IVFFlat index: {e}")

        elif index_type == "VCHORDRQ":
            sql = f"CREATE INDEX IF NOT EXISTS {vector_index_name} ON LIGHTRAG_VDB_CHUNKS USING vchordrq ({vector_column})"
            try:
                await self.execute(sql)
            except Exception as e:
                logger.debug(f"PostgreSQL, Error creating VCHORDRQ index: {e}")

        try:
            await self._migrate_llm_cache_schema()
        except Exception as e:
            logger.warning(f"PostgreSQL, Failed to migrate LLM cache schema: {e}")

        try:
            await self._migrate_timestamp_columns()
        except Exception as e:
            logger.warning(f"PostgreSQL, Failed to migrate timestamp columns: {e}")

        try:
            await self._migrate_doc_chunks_to_vdb_chunks()
        except Exception as e:
            logger.warning(f"PostgreSQL, Failed to migrate doc chunks: {e}")

        try:
            if await self._check_llm_cache_needs_migration():
                await self._migrate_llm_cache_to_flattened_keys()
        except Exception as e:
            logger.warning(f"PostgreSQL, Failed to migrate LLM cache: {e}")

    async def query(
        self,
        sql: str,
        params: list[Any] | dict[str, Any] | None = None,
        multirows: bool = False,
    ) -> dict[str, Any] | list[dict[str, Any]] | None:
        """Execute a query and return the result."""
        await self._ensure_pool()
        assert self.pool is not None
        async with self.pool.acquire() as connection:
            if params is None:
                params = []
            elif isinstance(params, dict):
                params = list(params.values())

            try:
                if multirows:
                    rows = await connection.fetch(sql, *params)
                    return [dict(row) for row in rows]
                else:
                    row = await connection.fetchrow(sql, *params)
                    return dict(row) if row else None
            except Exception as e:
                logger.error(
                    f"PostgreSQL database,\nsql:{sql},\nparams:{params},\nerror:{e}"
                )
                raise

    async def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        sql = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = $1
        ) AS exists
        """
        result = await self.query(sql, [table_name.lower()])
        return result["exists"] if result else False

    async def execute(self, sql: str, data: dict[str, Any] | None = None) -> str:
        """Execute a SQL statement."""
        await self._ensure_pool()
        assert self.pool is not None
        async with self.pool.acquire() as connection:
            try:
                if data is None:
                    return await connection.execute(sql)
                else:
                    return await connection.execute(sql, *data.values())
            except Exception as e:
                logger.error(
                    f"PostgreSQL database,\nsql:{sql},\ndata:{data},\nerror:{e}"
                )
                raise


class ClientManager:
    _instances: dict[str, Any] = {"db": None, "ref_count": 0}
    _lock = asyncio.Lock()

    @staticmethod
    def get_config() -> dict[str, Any]:
        config = configparser.ConfigParser()
        config.read("config.ini", "utf-8")

        return {
            "host": os.environ.get(
                "POSTGRES_HOST",
                config.get("postgres", "host", fallback="localhost"),
            ),
            "port": os.environ.get(
                "POSTGRES_PORT", config.get("postgres", "port", fallback=5432)
            ),
            "user": os.environ.get(
                "POSTGRES_USER", config.get("postgres", "user", fallback="postgres")
            ),
            "password": os.environ.get(
                "POSTGRES_PASSWORD",
                config.get("postgres", "password", fallback=None),
            ),
            "database": os.environ.get(
                "POSTGRES_DATABASE",
                config.get("postgres", "database", fallback="postgres"),
            ),
            "workspace": os.environ.get(
                "POSTGRES_WORKSPACE",
                config.get("postgres", "workspace", fallback=None),
            ),
            "max_connections": os.environ.get(
                "POSTGRES_MAX_CONNECTIONS",
                config.get("postgres", "max_connections", fallback=50),
            ),
            "ssl_mode": os.environ.get(
                "POSTGRES_SSL_MODE",
                config.get("postgres", "ssl_mode", fallback=None),
            ),
            "ssl_cert": os.environ.get(
                "POSTGRES_SSL_CERT",
                config.get("postgres", "ssl_cert", fallback=None),
            ),
            "ssl_key": os.environ.get(
                "POSTGRES_SSL_KEY",
                config.get("postgres", "ssl_key", fallback=None),
            ),
            "ssl_root_cert": os.environ.get(
                "POSTGRES_SSL_ROOT_CERT",
                config.get("postgres", "ssl_root_cert", fallback=None),
            ),
            "ssl_crl": os.environ.get(
                "POSTGRES_SSL_CRL",
                config.get("postgres", "ssl_crl", fallback=None),
            ),
            "vector_index_type": os.environ.get(
                "POSTGRES_VECTOR_INDEX_TYPE",
                config.get("postgres", "vector_index_type", fallback="HNSW"),
            ),
            "hnsw_m": int(
                os.environ.get(
                    "POSTGRES_HNSW_M",
                    config.get("postgres", "hnsw_m", fallback="16"),
                )
            ),
            "hnsw_ef": int(
                os.environ.get(
                    "POSTGRES_HNSW_EF",
                    config.get("postgres", "hnsw_ef", fallback="64"),
                )
            ),
            "ivfflat_lists": int(
                os.environ.get(
                    "POSTGRES_IVFFLAT_LISTS",
                    config.get("postgres", "ivfflat_lists", fallback="100"),
                )
            ),
            "vchordrq_build_options": os.environ.get(
                "POSTGRES_VCHORDRQ_BUILD_OPTIONS",
                config.get("postgres", "vchordrq_build_options", fallback=""),
            ),
            "vchordrq_probes": os.environ.get(
                "POSTGRES_VCHORDRQ_PROBES",
                config.get("postgres", "vchordrq_probes", fallback=""),
            ),
            "vchordrq_epsilon": float(
                os.environ.get(
                    "POSTGRES_VCHORDRQ_EPSILON",
                    config.get("postgres", "vchordrq_epsilon", fallback="1.9"),
                )
            ),
            "server_settings": os.environ.get(
                "POSTGRES_SERVER_SETTINGS",
                config.get("postgres", "server_options", fallback=None),
            ),
            "statement_cache_size": os.environ.get(
                "POSTGRES_STATEMENT_CACHE_SIZE",
                config.get("postgres", "statement_cache_size", fallback=None),
            ),
            "connection_retry_attempts": min(
                100,
                int(
                    os.environ.get(
                        "POSTGRES_CONNECTION_RETRIES",
                        config.get("postgres", "connection_retries", fallback=10),
                    )
                ),
            ),
            "connection_retry_backoff": min(
                300.0,
                float(
                    os.environ.get(
                        "POSTGRES_CONNECTION_RETRY_BACKOFF",
                        config.get(
                            "postgres", "connection_retry_backoff", fallback=3.0
                        ),
                    )
                ),
            ),
            "connection_retry_backoff_max": min(
                600.0,
                float(
                    os.environ.get(
                        "POSTGRES_CONNECTION_RETRY_BACKOFF_MAX",
                        config.get(
                            "postgres",
                            "connection_retry_backoff_max",
                            fallback=30.0,
                        ),
                    )
                ),
            ),
            "pool_close_timeout": min(
                30.0,
                float(
                    os.environ.get(
                        "POSTGRES_POOL_CLOSE_TIMEOUT",
                        config.get("postgres", "pool_close_timeout", fallback=5.0),
                    )
                ),
            ),
        }

    @classmethod
    async def get_client(cls) -> PostgreSQLDB:
        async with cls._lock:
            if cls._instances["db"] is None:
                config = ClientManager.get_config()
                db = PostgreSQLDB(config)
                await db.initdb()
                await db.check_tables()
                cls._instances["db"] = db
                cls._instances["ref_count"] = 0
            cls._instances["ref_count"] += 1
            return cls._instances["db"]

    @classmethod
    async def release_client(cls, db: PostgreSQLDB):
        async with cls._lock:
            if db is not None:
                if db is cls._instances["db"]:
                    cls._instances["ref_count"] -= 1
                    if cls._instances["ref_count"] == 0:
                        await db.pool.close()
                        logger.info("Closed PostgreSQL database connection pool")
                        cls._instances["db"] = None
                else:
                    await db.pool.close()
