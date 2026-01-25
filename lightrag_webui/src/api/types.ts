/**
 * Retrieval mode for LightRAG
 */
export type QueryMode = 'naive' | 'local' | 'global' | 'hybrid' | 'mix' | 'bypass'

/**
 * Message format for chat history
 */
export type Message = {
    role: 'user' | 'assistant' | 'system'
    content: string
    thinkingContent?: string
    displayContent?: string
    thinkingTime?: number | null
}

/**
 * Request parameters for text query
 */
export type QueryRequest = {
    query: string
    mode: QueryMode
    only_need_context?: boolean
    only_need_prompt?: boolean
    response_type?: string
    stream?: boolean
    top_k?: number
    chunk_top_k?: number
    max_entity_tokens?: number
    max_relation_tokens?: number
    max_total_tokens?: number
    conversation_history?: Message[]
    history_turns?: number
    user_prompt?: string
    enable_rerank?: boolean
    include_references?: boolean
    include_chunk_content?: boolean
}

/**
 * Reference item in query response
 */
export type ReferenceItem = {
    reference_id: string
    file_path: string
    content?: string[]
}

/**
 * Response for text query
 */
export type QueryResponse = {
    response: string
    references?: ReferenceItem[]
}

/**
 * Node in knowledge graph
 */
export type LightragNodeType = {
    id: string
    labels: string[]
    properties: Record<string, any>
}

/**
 * Edge in knowledge graph
 */
export type LightragEdgeType = {
    id: string
    source: string
    target: string
    type: string
    properties: Record<string, any>
}

/**
 * Knowledge graph structure
 */
export type LightragGraphType = {
    nodes: LightragNodeType[]
    edges: LightragEdgeType[]
}

/**
 * System status Information
 */
export type LightragStatus = {
    status: 'healthy'
    working_directory: string
    input_directory: string
    configuration: {
        llm_binding: string
        llm_binding_host: string
        llm_model: string
        embedding_binding: string
        embedding_binding_host: string
        embedding_model: string
        kv_storage: string
        doc_status_storage: string
        graph_storage: string
        vector_storage: string
        workspace?: string
        max_graph_nodes?: string
        enable_rerank?: boolean
        rerank_binding?: string | null
        rerank_model?: string | null
        rerank_binding_host?: string | null
        summary_language: string
        force_llm_summary_on_merge: boolean
        max_parallel_insert: number
        max_async: number
        embedding_func_max_async: number
        embedding_batch_num: number
        cosine_threshold: number
        min_rerank_score: number
        related_chunk_number: number
    }
    update_status?: Record<string, any>
    core_version?: string
    api_version?: string
    auth_mode?: 'enabled' | 'disabled'
    pipeline_busy: boolean
    keyed_locks?: {
        process_id: number
        cleanup_performed: {
            mp_cleaned: number
            async_cleaned: number
        }
        current_status: {
            total_mp_locks: number
            pending_mp_cleanup: number
            total_async_locks: number
            pending_async_cleanup: number
        }
    }
    webui_title?: string
    webui_description?: string
}

/**
 * Scan progress information
 */
export type LightragDocumentsScanProgress = {
    is_scanning: boolean
    current_file: string
    indexed_count: number
    total_files: number
    progress: number
}

/**
 * Document processing status
 */
export type DocStatus = 'pending' | 'processing' | 'preprocessed' | 'processed' | 'failed'

/**
 * Individual document status response
 */
export type DocStatusResponse = {
    id: string
    content_summary: string
    content_length: number
    status: DocStatus
    created_at: string
    updated_at: string
    track_id?: string
    chunks_count?: number
    error_msg?: string
    metadata?: Record<string, any>
    file_path: string
}

/**
 * Collection of documents by status
 */
export type DocsStatusesResponse = {
    statuses: Record<DocStatus, DocStatusResponse[]>
}

/**
 * Request for paginated documents
 */
export type DocumentsRequest = {
    status_filter?: DocStatus | null
    page: number
    page_size: number
    sort_field: 'created_at' | 'updated_at' | 'id' | 'file_path'
    sort_direction: 'asc' | 'desc'
}

/**
 * Pagination metadata
 */
export type PaginationInfo = {
    page: number
    page_size: number
    total_count: number
    total_pages: number
    has_next: boolean
    has_prev: boolean
}

/**
 * Paginated document list response
 */
export type PaginatedDocsResponse = {
    documents: DocStatusResponse[]
    pagination: PaginationInfo
    status_counts: Record<string, number>
}

/**
 * Auth status response from server
 */
export type AuthStatusResponse = {
    auth_configured: boolean
    access_token?: string
    token_type?: string
    auth_mode?: 'enabled' | 'disabled'
    message?: string
    core_version?: string
    api_version?: string
    webui_title?: string
    webui_description?: string
}

/**
 * Login response from server
 */
export type LoginResponse = {
    access_token: string
    token_type: string
    auth_mode?: 'enabled' | 'disabled'
    message?: string
    core_version?: string
    api_version?: string
    webui_title?: string
    webui_description?: string
}

// Misc Responses
export type EntityUpdateResponse = {
    status: string
    message: string
    data: Record<string, any>
}

export type DocActionResponse = {
    status: 'success' | 'partial_success' | 'failure' | 'duplicated'
    message: string
    track_id?: string
}

export type DeleteDocResponse = {
    status: string
    message: string
}

export type ScanResponse = {
    status: 'scanning_started'
    message: string
    track_id: string
}

export type ReprocessFailedResponse = {
    status: 'reprocessing_started'
    message: string
    track_id: string
}

export type TrackStatusResponse = {
    track_id: string
    documents: DocStatusResponse[]
    total_count: number
    status_summary: Record<string, number>
}

export type StatusCountsResponse = {
    status_counts: Record<string, number>
}

export type PipelineStatusResponse = {
    autoscanned: boolean
    busy: boolean
    job_name: string
    job_start?: string
    docs: number
    batchs: number
    cur_batch: number
    request_pending: boolean
    latest_message: string
    update_status?: Record<string, any>
    log_level?: number
}

export const InvalidApiKeyError = 'Invalid API Key'
export const RequireApiKeError = 'API Key required'
