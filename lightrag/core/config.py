"""LightRAG configuration dataclass."""

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from lightrag.ace.config import ACEConfig
from lightrag.base import OllamaServerInfos, StoragesStatus
from lightrag.constants import (
    DEFAULT_CHUNK_TOP_K,
    DEFAULT_COSINE_THRESHOLD,
    DEFAULT_EMBEDDING_TIMEOUT,
    DEFAULT_ENTITY_TYPES,
    DEFAULT_FILE_PATH_MORE_PLACEHOLDER,
    DEFAULT_FORCE_LLM_SUMMARY_ON_MERGE,
    DEFAULT_KG_CHUNK_PICK_METHOD,
    DEFAULT_LLM_TIMEOUT,
    DEFAULT_MAX_ASYNC,
    DEFAULT_MAX_ENTITY_TOKENS,
    DEFAULT_MAX_FILE_PATHS,
    DEFAULT_MAX_GLEANING,
    DEFAULT_MAX_GRAPH_NODES,
    DEFAULT_MAX_PARALLEL_INSERT,
    DEFAULT_MAX_RELATION_TOKENS,
    DEFAULT_MAX_SOURCE_IDS_PER_ENTITY,
    DEFAULT_MAX_SOURCE_IDS_PER_RELATION,
    DEFAULT_MAX_TOTAL_TOKENS,
    DEFAULT_MIN_RERANK_SCORE,
    DEFAULT_RELATED_CHUNK_NUMBER,
    DEFAULT_SOURCE_IDS_LIMIT_METHOD,
    DEFAULT_SUMMARY_CONTEXT_SIZE,
    DEFAULT_SUMMARY_LANGUAGE,
    DEFAULT_SUMMARY_LENGTH_RECOMMENDED,
    DEFAULT_SUMMARY_MAX_TOKENS,
    DEFAULT_TOP_K,
)
from lightrag.utils import (
    EmbeddingFunc,
    TiktokenTokenizer,
    Tokenizer,
    get_env_value,
    normalize_source_ids_limit_method,
    parse_model_size,
)


@dataclass
class LightRAGConfig:
    """LightRAG: Simple and Fast Retrieval-Augmented Generation."""

    working_dir: str = field(default="./rag_storage")

    kv_storage: str = field(default="JsonKVStorage")
    vector_storage: str = field(default="NanoVectorDBStorage")
    graph_storage: str = field(default="NetworkXStorage")
    doc_status_storage: str = field(default="JsonDocStatusStorage")
    keyword_storage_backend: str = field(default="NanoKeywordStorage")

    workspace: str = field(default_factory=lambda: os.getenv("WORKSPACE", ""))

    log_level: int | None = field(default=None)
    log_file_path: str | None = field(default=None)

    top_k: int = field(default=get_env_value("TOP_K", DEFAULT_TOP_K, int))

    chunk_top_k: int = field(
        default=get_env_value("CHUNK_TOP_K", DEFAULT_CHUNK_TOP_K, int)
    )

    max_entity_tokens: int = field(
        default=get_env_value("MAX_ENTITY_TOKENS", DEFAULT_MAX_ENTITY_TOKENS, int)
    )

    max_relation_tokens: int = field(
        default=get_env_value("MAX_RELATION_TOKENS", DEFAULT_MAX_RELATION_TOKENS, int)
    )

    max_total_tokens: int = field(
        default=get_env_value("MAX_TOTAL_TOKENS", DEFAULT_MAX_TOTAL_TOKENS, int)
    )

    cosine_threshold: int = field(
        default=get_env_value("COSINE_THRESHOLD", DEFAULT_COSINE_THRESHOLD, int)
    )

    related_chunk_number: int = field(
        default=get_env_value("RELATED_CHUNK_NUMBER", DEFAULT_RELATED_CHUNK_NUMBER, int)
    )

    kg_chunk_pick_method: str = field(
        default=get_env_value("KG_CHUNK_PICK_METHOD", DEFAULT_KG_CHUNK_PICK_METHOD, str)
    )

    entity_extract_max_gleaning: int = field(
        default=get_env_value("MAX_GLEANING", DEFAULT_MAX_GLEANING, int)
    )

    force_llm_summary_on_merge: int = field(
        default=get_env_value(
            "FORCE_LLM_SUMMARY_ON_MERGE", DEFAULT_FORCE_LLM_SUMMARY_ON_MERGE, int
        )
    )

    extraction_format: str = field(
        default=get_env_value("EXTRACTION_FORMAT", "standard", str)
    )

    lite_extraction: bool = field(
        default=get_env_value("LITE_EXTRACTION", "false", str).lower() == "true"
    )

    chunk_token_size: int = field(default=int(os.getenv("CHUNK_SIZE", 1200)))

    chunk_overlap_token_size: int = field(
        default=int(os.getenv("CHUNK_OVERLAP_SIZE", 100))
    )

    tokenizer: Tokenizer | None = field(default=None)

    tiktoken_model_name: str = field(default="gpt-4o-mini")

    chunking_func: Callable[
        [
            Tokenizer,
            str,
            str | None,
            bool,
            int,
            int,
        ],
        list[dict[str, Any]] | list[dict[str, Any]],
    ] = field(default=None)

    embedding_func: EmbeddingFunc | None = field(default=None)

    embedding_token_limit: int | None = field(default=None, init=False)

    embedding_batch_num: int = field(default=int(os.getenv("EMBEDDING_BATCH_NUM", 10)))

    embedding_func_max_async: int = field(
        default=int(os.getenv("EMBEDDING_FUNC_MAX_ASYNC", 8))
    )

    embedding_cache_config: dict[str, Any] = field(
        default_factory=lambda: {
            "enabled": False,
            "similarity_threshold": 0.95,
            "use_llm_check": False,
        }
    )

    default_embedding_timeout: int = field(
        default=int(os.getenv("EMBEDDING_TIMEOUT", DEFAULT_EMBEDDING_TIMEOUT))
    )

    llm_model_func: Callable[..., object] | None = field(default=None)

    llm_model_name: str = field(default="gpt-4o-mini")

    summary_max_tokens: int = field(
        default=int(os.getenv("SUMMARY_MAX_TOKENS", DEFAULT_SUMMARY_MAX_TOKENS))
    )

    summary_context_size: int = field(
        default=int(os.getenv("SUMMARY_CONTEXT_SIZE", DEFAULT_SUMMARY_CONTEXT_SIZE))
    )

    summary_length_recommended: int = field(
        default=int(
            os.getenv("SUMMARY_LENGTH_RECOMMENDED", DEFAULT_SUMMARY_LENGTH_RECOMMENDED)
        )
    )

    llm_model_max_async: int = field(
        default=int(os.getenv("MAX_ASYNC", DEFAULT_MAX_ASYNC))
    )

    llm_model_kwargs: dict[str, Any] = field(default_factory=dict)

    default_llm_timeout: int = field(
        default=int(os.getenv("LLM_TIMEOUT", DEFAULT_LLM_TIMEOUT))
    )

    reflection_llm_model_name: str | None = field(default=None)

    reflection_llm_model_func: Callable[..., object] | None = field(default=None)

    reflection_llm_model_kwargs: dict[str, Any] = field(default_factory=dict)

    rerank_model_func: Callable[..., object] | None = field(default=None)

    min_rerank_score: float = field(
        default=get_env_value("MIN_RERANK_SCORE", DEFAULT_MIN_RERANK_SCORE, float)
    )

    vector_db_storage_cls_kwargs: dict[str, Any] = field(default_factory=dict)

    enable_llm_cache: bool = field(default=True)

    enable_llm_cache_for_entity_extract: bool = field(default=True)

    max_parallel_insert: int = field(
        default=int(os.getenv("MAX_PARALLEL_INSERT", DEFAULT_MAX_PARALLEL_INSERT))
    )

    max_graph_nodes: int = field(
        default=get_env_value("MAX_GRAPH_NODES", DEFAULT_MAX_GRAPH_NODES, int)
    )

    max_source_ids_per_entity: int = field(
        default=get_env_value(
            "MAX_SOURCE_IDS_PER_ENTITY", DEFAULT_MAX_SOURCE_IDS_PER_ENTITY, int
        )
    )

    max_source_ids_per_relation: int = field(
        default=get_env_value(
            "MAX_SOURCE_IDS_PER_RELATION",
            DEFAULT_MAX_SOURCE_IDS_PER_RELATION,
            int,
        )
    )

    source_ids_limit_method: str = field(
        default_factory=lambda: normalize_source_ids_limit_method(
            get_env_value(
                "SOURCE_IDS_LIMIT_METHOD",
                DEFAULT_SOURCE_IDS_LIMIT_METHOD,
                str,
            )
        )
    )

    max_file_paths: int = field(
        default=get_env_value("MAX_FILE_PATHS", DEFAULT_MAX_FILE_PATHS, int)
    )

    file_path_more_placeholder: str = field(default=DEFAULT_FILE_PATH_MORE_PLACEHOLDER)

    addon_params: dict[str, Any] = field(
        default_factory=lambda: {
            "language": get_env_value(
                "SUMMARY_LANGUAGE", DEFAULT_SUMMARY_LANGUAGE, str
            ),
            "entity_types": get_env_value("ENTITY_TYPES", DEFAULT_ENTITY_TYPES, list),
        }
    )

    auto_manage_storages_states: bool = field(default=False)

    cosine_better_than_threshold: float = field(
        default=float(os.getenv("COSINE_THRESHOLD", 0.2))
    )

    ollama_server_infos: OllamaServerInfos | None = field(default=None)

    enable_ace: bool = field(default=False)

    ace_config: ACEConfig | None = field(default=None)

    ace_allow_small_reflector: bool = field(default=False)

    _storages_status: StoragesStatus = field(default=StoragesStatus.NOT_CREATED)
