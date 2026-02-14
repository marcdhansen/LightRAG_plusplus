"""PostgreSQL storage implementation - backward compatibility re-exports.

This module re-exports all classes and functions from the new modular structure.
The actual implementations have been moved to lightrag/kg/postgres/ directory.

New import paths (recommended):
    from lightrag.kg.postgres import PGKVStorage
    from lightrag.kg.postgres import PGVectorStorage
    from lightrag.kg.postgres import PGGraphStorage
    from lightrag.kg.postgres import PGDocStatusStorage (deprecated, will be removed in a

Old import paths future release):
    from lightrag.kg.postgres_impl import PGKVStorage
    from lightrag.kg.postgres_impl import PGVectorStorage
    from lightrag.kg.postgres_impl import PGGraphStorage
    from lightrag.kg.postgres_impl import PGDocStatusStorage
"""

import warnings
from typing import Any

_DEPRECATED_IMPORTS = {
    "PostgreSQLDB": "lightrag.kg.postgres.PostgreSQLDB",
    "ClientManager": "lightrag.kg.postgres.ClientManager",
    "PGKVStorage": "lightrag.kg.postgres.PGKVStorage",
    "PGVectorStorage": "lightrag.kg.postgres.PGVectorStorage",
    "PGDocStatusStorage": "lightrag.kg.postgres.PGDocStatusStorage",
    "PGGraphStorage": "lightrag.kg.postgres.PGGraphStorage",
    "PGGraphQueryException": "lightrag.kg.postgres.PGGraphQueryException",
    "namespace_to_table_name": "lightrag.kg.postgres.namespace_to_table_name",
    "NAMESPACE_TABLE_MAP": "lightrag.kg.postgres.NAMESPACE_TABLE_MAP",
    "TABLES": "lightrag.kg.postgres.TABLES",
    "SQL_TEMPLATES": "lightrag.kg.postgres.SQL_TEMPLATES",
    "_safe_index_name": "lightrag.kg.postgres._safe_index_name",
    "_dollar_quote": "lightrag.kg.postgres._dollar_quote",
    "PG_MAX_IDENTIFIER_LENGTH": "lightrag.kg.postgres.PG_MAX_IDENTIFIER_LENGTH",
}


def __getattr__(name: str) -> Any:
    """Lazy loading with deprecation warnings for backward compatibility."""
    if name in _DEPRECATED_IMPORTS:
        new_path = _DEPRECATED_IMPORTS[name]
        warnings.warn(
            f"Importing '{name}' from 'lightrag.kg.postgres_impl' is deprecated. "
            f"Please use 'from {new_path} import {name}' instead. "
            f"This module will be removed in a future release.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Actually import the object from the new location
        from lightrag.kg import postgres

        return getattr(postgres, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = list(_DEPRECATED_IMPORTS.keys())
