"""Shared PostgreSQL constants."""

import re
from typing import Optional

from lightrag.namespace import NameSpace, is_namespace


def _safe_index_name(table_name: str, index_suffix: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", table_name)
    max_len = 63 - len(index_suffix) - 1
    if len(safe) > max_len:
        safe = safe[:max_len]
    return f"{safe}_{index_suffix}"


NAMESPACE_TABLE_MAP = {
    NameSpace.KV_STORE_FULL_DOCS: "LIGHTRAG_DOC_FULL",
    NameSpace.KV_STORE_TEXT_CHUNKS: "LIGHTRAG_DOC_CHUNKS",
    NameSpace.KV_STORE_FULL_ENTITIES: "LIGHTRAG_FULL_ENTITIES",
    NameSpace.KV_STORE_FULL_RELATIONS: "LIGHTRAG_FULL_RELATIONS",
    NameSpace.KV_STORE_ENTITY_CHUNKS: "LIGHTRAG_ENTITY_CHUNKS",
    NameSpace.KV_STORE_RELATION_CHUNKS: "LIGHTRAG_RELATION_CHUNKS",
    NameSpace.KV_STORE_LLM_RESPONSE_CACHE: "LIGHTRAG_LLM_CACHE",
    NameSpace.VECTOR_STORE_CHUNKS: "LIGHTRAG_VDB_CHUNKS",
    NameSpace.VECTOR_STORE_ENTITIES: "LIGHTRAG_VDB_ENTITY",
    NameSpace.VECTOR_STORE_RELATIONSHIPS: "LIGHTRAG_VDB_RELATION",
    NameSpace.DOC_STATUS: "LIGHTRAG_DOC_STATUS",
}


def namespace_to_table_name(namespace: str) -> Optional[str]:
    for k, v in NAMESPACE_TABLE_MAP.items():
        if is_namespace(namespace, k):
            return v
    return None


TABLES = {
    "LIGHTRAG_DOC_FULL": {
        "ddl": """CREATE TABLE LIGHTRAG_DOC_FULL (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    doc_name VARCHAR(1024),
                    content TEXT,
                    meta JSONB,
                    create_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT LIGHTRAG_DOC_FULL_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_DOC_CHUNKS": {
        "ddl": """CREATE TABLE LIGHTRAG_DOC_CHUNKS (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    full_doc_id VARCHAR(256),
                    chunk_order_index INTEGER,
                    content TEXT,
                    meta JSONB,
                    create_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT LIGHTRAG_DOC_CHUNKS_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_FULL_ENTITIES": {
        "ddl": """CREATE TABLE LIGHTRAG_FULL_ENTITIES (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    entity_id VARCHAR(255),
                    entity_name VARCHAR(512),
                    entity_type VARCHAR(128),
                    description TEXT,
                    source_id VARCHAR(255),
                    source_start_index INTEGER,
                    source_end_index INTEGER,
                    frequency INTEGER,
                    node_attributes JSONB,
                    text_unit_id VARCHAR(255),
                    meta JSONB,
                    create_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT LIGHTRAG_FULL_ENTITIES_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_FULL_RELATIONS": {
        "ddl": """CREATE TABLE LIGHTRAG_FULL_RELATIONS (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    source_id VARCHAR(255),
                    target_id VARCHAR(255),
                    weight FLOAT,
                    frequency INTEGER,
                    relation_name VARCHAR(512),
                    description TEXT,
                    source_start_index INTEGER,
                    source_end_index INTEGER,
                    text_unit_id VARCHAR(255),
                    meta JSONB,
                    create_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT LIGHTRAG_FULL_RELATIONS_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_ENTITY_CHUNKS": {
        "ddl": """CREATE TABLE LIGHTRAG_ENTITY_CHUNKS (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    entity_id VARCHAR(255),
                    chunk_order_index INTEGER,
                    chunk_id VARCHAR(255),
                    meta JSONB,
                    create_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT LIGHTRAG_ENTITY_CHUNKS_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_RELATION_CHUNKS": {
        "ddl": """CREATE TABLE LIGHTRAG_RELATION_CHUNKS (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    relation_id VARCHAR(255),
                    chunk_order_index INTEGER,
                    chunk_id VARCHAR(255),
                    meta JSONB,
                    create_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT LIGHTRAG_RELATION_CHUNKS_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_LLM_CACHE": {
        "ddl": """CREATE TABLE LIGHTRAG_LLM_CACHE (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    content TEXT,
                    meta JSONB,
                    create_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT LIGHTRAG_LLM_CACHE_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_VDB_CHUNKS": {
        "ddl": """CREATE TABLE LIGHTRAG_VDB_CHUNKS (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    doc_name VARCHAR(1024),
                    chunk_order_index INTEGER,
                    content TEXT,
                    content_vector vector,
                    meta JSONB,
                    create_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT LIGHTRAG_VDB_CHUNKS_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_VDB_ENTITY": {
        "ddl": """CREATE TABLE LIGHTRAG_VDB_ENTITY (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    entity_name VARCHAR(512),
                    entity_type VARCHAR(128),
                    description TEXT,
                    source_id VARCHAR(255),
                    source_start_index INTEGER,
                    source_end_index INTEGER,
                    content_vector vector,
                    text_unit_id VARCHAR(255),
                    meta JSONB,
                    create_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT LIGHTRAG_VDB_ENTITY_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_VDB_RELATION": {
        "ddl": """CREATE TABLE LIGHTRAG_VDB_RELATION (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    source_id VARCHAR(255),
                    target_id VARCHAR(255),
                    weight FLOAT,
                    relation_name VARCHAR(512),
                    description TEXT,
                    source_start_index INTEGER,
                    source_end_index INTEGER,
                    content_vector vector,
                    text_unit_id VARCHAR(255),
                    meta JSONB,
                    create_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT LIGHTRAG_VDB_RELATION_PK PRIMARY KEY (workspace, id)
                    )"""
    },
    "LIGHTRAG_DOC_STATUS": {
        "ddl": """CREATE TABLE LIGHTRAG_DOC_STATUS (
                    id VARCHAR(255),
                    workspace VARCHAR(255),
                    doc_id VARCHAR(256),
                    doc_name VARCHAR(1024),
                    status VARCHAR(128),
                    content_md5 VARCHAR(128),
                    error_msg TEXT,
                    meta JSONB,
                    create_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    update_time TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT LIGHTRAG_DOC_STATUS_PK PRIMARY KEY (workspace, id)
                    )"""
    },
}

SQL_TEMPLATES = {
    "create_tables": """
        SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = $1
    """,
    "drop_tables": """
        SELECT $1 as table_name;
    """,
    "insert_full_doc": """
        INSERT INTO {table_name} (id, workspace, doc_name, content, meta, create_time, update_time)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (workspace, id) DO UPDATE SET
            doc_name = EXCLUDED.doc_name,
            content = EXCLUDED.content,
            meta = EXCLUDED.meta,
            update_time = EXCLUDED.update_time
    """,
    "upsert_kv": """
        INSERT INTO {table_name} (id, workspace, content, meta, create_time, update_time)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (workspace, id) DO UPDATE SET
            content = EXCLUDED.content,
            meta = EXCLUDED.meta,
            update_time = EXCLUDED.update_time
    """,
    "upsert_doc_status": """
        INSERT INTO {table_name} (id, workspace, doc_id, doc_name, status, content_md5, error_msg, meta, create_time, update_time)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        ON CONFLICT (workspace, id) DO UPDATE SET
            status = EXCLUDED.status,
            content_md5 = EXCLUDED.content_md5,
            error_msg = EXCLUDED.error_msg,
            meta = EXCLUDED.meta,
            update_time = EXCLUDED.update_time
    """,
    "get_doc_by_id": """
        SELECT * FROM {table_name} WHERE id=$1 AND workspace=$2
    """,
    "get_docs_by_status": """
        SELECT * FROM {table_name} WHERE status=$1 AND workspace=$2
    """,
    "get_all_docs": """
        SELECT * FROM {table_name} WHERE workspace=$1 ORDER BY create_time DESC
    """,
    "delete_doc": """
        DELETE FROM {table_name} WHERE id=$1 AND workspace=$2
    """,
    "delete_docs": """
        DELETE FROM {table_name} WHERE workspace=$1
    """,
    "delete_vector": """
        DELETE FROM {table_name} WHERE workspace=$1
    """,
    "drop_specifiy_table_workspace": """
        DELETE FROM {table_name} WHERE workspace=$1
    """,
}

PG_MAX_IDENTIFIER_LENGTH = 63
