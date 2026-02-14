"""PostgreSQL storage implementation - backward compatibility re-exports.

This module re-exports all classes and functions from the new modular structure.
The actual implementations have been moved to lightrag/kg/postgres/ directory.

New import paths (recommended):
    from lightrag.kg.postgres import PGKVStorage
    from lightrag.kg.postgres import PGVectorStorage
    from lightrag.kg.postgres import PGGraphStorage
    from lightrag.kg.postgres import PGDocStatusStorage

Old import paths (still work for backward compatibility):
    from lightrag.kg.postgres_impl import PGKVStorage
    from lightrag.kg.postgres_impl import PGVectorStorage
    from lightrag.kg.postgres_impl import PGGraphStorage
    from lightrag.kg.postgres_impl import PGDocStatusStorage
"""

from lightrag.kg.postgres import (
    ClientManager,
    NAMESPACE_TABLE_MAP,
    PG_MAX_IDENTIFIER_LENGTH,
    PGDocStatusStorage,
    PGGraphStorage,
    PGGraphQueryException,
    PGKVStorage,
    PGVectorStorage,
    PostgreSQLDB,
    SQL_TEMPLATES,
    TABLES,
    _dollar_quote,
    _safe_index_name,
    namespace_to_table_name,
)

__all__ = [
    "PostgreSQLDB",
    "ClientManager",
    "PGKVStorage",
    "PGVectorStorage",
    "PGDocStatusStorage",
    "PGGraphStorage",
    "PGGraphQueryException",
    "namespace_to_table_name",
    "NAMESPACE_TABLE_MAP",
    "TABLES",
    "SQL_TEMPLATES",
    "_safe_index_name",
    "_dollar_quote",
    "PG_MAX_IDENTIFIER_LENGTH",
]
