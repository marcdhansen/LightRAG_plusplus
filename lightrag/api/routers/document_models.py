"""Document-related Pydantic models for LightRAG API.

This module contains all Pydantic models used in document-related routes.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LogEntry(BaseModel):
    """Log entry model for frontend logging."""

    level: str
    message: str
    context: dict = {}


class ScanResponse(BaseModel):
    """Response model for document scanning operation.

    Attributes:
        status: Status of the scanning operation
        message: Optional message with additional details
        track_id: Tracking ID for monitoring scanning progress
    """

    status: Literal["scanning_started"] = Field(
        description="Status of the scanning operation"
    )
    message: str | None = Field(
        default=None, description="Additional details about the scanning operation"
    )
    track_id: str = Field(description="Tracking ID for monitoring scanning progress")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "scanning_started",
                "message": "Scanning process has been initiated in the background",
                "track_id": "scan_20250729_170612_abc123",
            }
        }
    )


class ReprocessResponse(BaseModel):
    """Response model for reprocessing failed documents operation.

    Attributes:
        status: Status of the reprocessing operation
        message: Message describing the operation result
        track_id: Always empty string. Reprocessed documents retain their original track_id.
    """

    status: Literal["reprocessing_started"] = Field(
        description="Status of the reprocessing operation"
    )
    message: str = Field(description="Human-readable message describing the operation")
    track_id: str = Field(
        default="",
        description="Always empty string. Reprocessed documents retain their original track_id from initial upload.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "reprocessing_started",
                "message": "Reprocessing of failed documents has been initiated in background",
                "track_id": "",
            }
        }
    )


class CancelPipelineResponse(BaseModel):
    """Response model for pipeline cancellation operation.

    Attributes:
        status: Status of the cancellation request
        message: Message describing the operation result
    """

    status: Literal["cancellation_requested", "not_busy"] = Field(
        description="Status of the cancellation request"
    )
    message: str = Field(description="Human-readable message describing the operation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "cancellation_requested",
                "message": "Pipeline cancellation has been requested. Documents will be marked as FAILED.",
            }
        }
    )


class InsertTextRequest(BaseModel):
    """Request model for inserting a single text document.

    Attributes:
        text: The text content to be inserted into the RAG system
        file_source: Source of the text (optional)
    """

    text: str = Field(
        min_length=1,
        description="The text to insert",
    )
    file_source: str = Field(default=None, min_length=0, description="File Source")

    @field_validator("text", mode="after")
    @classmethod
    def strip_text_after(cls, text: str) -> str:
        return text.strip()

    @field_validator("file_source", mode="after")
    @classmethod
    def strip_source_after(cls, file_source: str) -> str:
        return file_source.strip()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "This is a sample text to be inserted into the RAG system.",
                "file_source": "Source of the text (optional)",
            }
        }
    )


class InsertTextsRequest(BaseModel):
    """Request model for inserting multiple text documents.

    Attributes:
        texts: List of text contents to be inserted into the RAG system
        file_sources: Sources of the texts (optional)
    """

    texts: list[str] = Field(
        min_length=1,
        description="The texts to insert",
    )
    file_sources: list[str] = Field(
        default=None, min_length=0, description="Sources of the texts"
    )

    @field_validator("texts", mode="after")
    @classmethod
    def strip_texts_after(cls, texts: list[str]) -> list[str]:
        return [text.strip() for text in texts]

    @field_validator("file_sources", mode="after")
    @classmethod
    def strip_sources_after(cls, file_sources: list[str]) -> list[str]:
        return [source.strip() for source in file_sources] if file_sources else []

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "texts": [
                    "This is the first text to insert.",
                    "This is the second text to insert.",
                ],
                "file_sources": ["source1.txt", "source2.txt"],
            }
        }
    )


class InsertResponse(BaseModel):
    """Response model for text insertion operations.

    Attributes:
        status: Status of the insertion operation
        message: Message describing the operation result
        track_ids: List of tracking IDs for the inserted documents
    """

    status: Literal["success", "partial_success"] = Field(
        description="Status of the insertion operation"
    )
    message: str = Field(description="Human-readable message describing the operation")
    track_ids: list[str] = Field(
        default=[], description="List of tracking IDs for inserted documents"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "message": "Document inserted successfully",
                "track_ids": ["insert_20250729_170612_abc123"],
            }
        }
    )


class ClearDocumentsResponse(BaseModel):
    """Response model for clearing documents operation.

    Attributes:
        status: Status of the operation
        message: Human-readable message describing the operation result
    """

    status: Literal["success"] = Field(description="Status of the operation")
    message: str = Field(description="Human-readable message describing the operation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "message": "All documents have been cleared from the database",
            }
        }
    )


class ClearCacheRequest(BaseModel):
    """Request model for clearing cache."""

    cache_type: Literal[
        "entity_extract", "chunk_extract", "keywords_extract", "all"
    ] = Field(description="Type of cache to clear")


class ClearCacheResponse(BaseModel):
    """Response model for clearing cache operation.

    Attributes:
        status: Status of the operation
        message: Human-readable message describing the operation result
    """

    status: Literal["success"] = Field(description="Status of the operation")
    message: str = Field(description="Human-readable message describing the operation")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "message": "Entity extraction cache cleared successfully",
            }
        }
    )


class DeleteDocRequest(BaseModel):
    """Request model for deleting a document.

    Attributes:
        file_name: Name of the file to delete
        track_id: Tracking ID of the document to delete
    """

    file_name: str = Field(description="Name of the file to delete")
    track_id: str | None = Field(
        default=None, description="Tracking ID of the document"
    )

    @field_validator("file_name", mode="after")
    @classmethod
    def strip_filename(cls, v: str) -> str:
        return v.strip()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_name": "example.txt",
                "track_id": "upload_20250729_170612_abc123",
            }
        }
    )


class DeleteEntityRequest(BaseModel):
    """Request model for deleting an entity.

    Attributes:
        entity_name: Name of the entity to delete
    """

    entity_name: str = Field(description="Name of the entity to delete")

    model_config = ConfigDict(
        json_schema_extra={"example": {"entity_name": "ExampleEntity"}}
    )


class DeleteRelationRequest(BaseModel):
    """Request model for deleting a relation.

    Attributes:
        src_id: Source entity ID
        tgt_id: Target entity ID
    """

    src_id: str = Field(description="Source entity ID")
    tgt_id: str = Field(description="Target entity ID")

    model_config = ConfigDict(
        json_schema_extra={"example": {"src_id": "EntityA", "tgt_id": "EntityB"}}
    )


class DocStatusResponse(BaseModel):
    """Response model for document status query.

    Attributes:
        file_name: Name of the file
        status: Current processing status
        success: Whether the operation was successful
        track_id: Tracking ID for the document
        error_message: Error message if any
        completed: Whether processing is completed
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    file_name: str = Field(description="Name of the file")
    status: str = Field(description="Current processing status")
    success: bool = Field(description="Whether the operation was successful")
    track_id: str = Field(description="Tracking ID for the document")
    error_message: str | None = Field(default=None, description="Error message if any")
    completed: bool = Field(description="Whether processing is completed")
    created_at: str | None = Field(default=None, description="Creation timestamp")
    updated_at: str | None = Field(default=None, description="Last update timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_name": "example.txt",
                "status": "completed",
                "success": True,
                "track_id": "upload_20250729_170612_abc123",
                "error_message": None,
                "completed": True,
                "created_at": "2025-07-29T17:06:12Z",
                "updated_at": "2025-07-29T17:06:15Z",
            }
        }
    )


class DocsStatusesResponse(BaseModel):
    """Response model for querying multiple document statuses.

    Attributes:
        docs: List of document statuses
        total: Total number of documents
        skip: Number of documents skipped
        limit: Maximum number of documents returned
    """

    docs: list[DocStatusResponse] = Field(description="List of document statuses")
    total: int = Field(description="Total number of documents")
    skip: int = Field(description="Number of documents skipped")
    limit: int = Field(description="Maximum number of documents returned")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "docs": [
                    {
                        "file_name": "example.txt",
                        "status": "completed",
                        "success": True,
                        "track_id": "upload_20250729_170612_abc123",
                        "error_message": None,
                        "completed": True,
                        "created_at": "2025-07-29T17:06:12Z",
                        "updated_at": "2025-07-29T17:06:15Z",
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 10,
            }
        }
    )


class TrackStatusResponse(BaseModel):
    """Response model for tracking document processing status.

    Attributes:
        track_id: Tracking ID for the document
        status: Current status of the document
        chunks_parsed: Number of chunks parsed
        entities_extracted: Number of entities extracted
        relations_extracted: Number of relations extracted
    """

    track_id: str = Field(description="Tracking ID for the document")
    status: str = Field(description="Current status of the document")
    chunks_parsed: int = Field(default=0, description="Number of chunks parsed")
    entities_extracted: int = Field(
        default=0, description="Number of entities extracted"
    )
    relations_extracted: int = Field(
        default=0, description="Number of relations extracted"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "track_id": "upload_20250729_170612_abc123",
                "status": "processing",
                "chunks_parsed": 10,
                "entities_extracted": 5,
                "relations_extracted": 3,
            }
        }
    )


class DocumentsRequest(BaseModel):
    """Request model for listing documents.

    Attributes:
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        status: Optional filter by status
    """

    skip: int = Field(default=0, ge=0, description="Number of documents to skip")
    limit: int = Field(
        default=10, ge=1, le=100, description="Maximum documents to return"
    )
    status: str | None = Field(default=None, description="Filter by status")

    model_config = ConfigDict(
        json_schema_extra={"example": {"skip": 0, "limit": 10, "status": "completed"}}
    )


class PaginationInfo(BaseModel):
    """Pagination information.

    Attributes:
        skip: Number of items skipped
        limit: Maximum items per page
        total: Total number of items
    """

    skip: int = Field(description="Number of items skipped")
    limit: int = Field(description="Maximum items per page")
    total: int = Field(description="Total number of items")


class PaginatedDocsResponse(BaseModel):
    """Paginated response for documents.

    Attributes:
        data: List of documents
        pagination: Pagination information
    """

    data: list[dict[str, Any]] = Field(description="List of documents")
    pagination: PaginationInfo = Field(description="Pagination information")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "data": [{"id": "1", "name": "doc1.txt"}],
                "pagination": {"skip": 0, "limit": 10, "total": 1},
            }
        }
    )


class StatusCountsResponse(BaseModel):
    """Response model for document status counts.

    Attributes:
        pending: Number of pending documents
        processing: Number of processing documents
        completed: Number of completed documents
        failed: Number of failed documents
        total: Total number of documents
    """

    pending: int = Field(description="Number of pending documents")
    processing: int = Field(description="Number of processing documents")
    completed: int = Field(description="Number of completed documents")
    failed: int = Field(description="Number of failed documents")
    total: int = Field(description="Total number of documents")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pending": 5,
                "processing": 2,
                "completed": 100,
                "failed": 3,
                "total": 110,
            }
        }
    )


class PipelineStatusResponse(BaseModel):
    """Response model for pipeline status.

    Attributes:
        is_busy: Whether the pipeline is currently busy processing
        current_track_id: Current track ID being processed
        total_pending: Total number of pending documents
        current_status: Current status of each document
    """

    is_busy: bool = Field(description="Whether the pipeline is busy")
    current_track_id: str | None = Field(
        default=None, description="Current track ID being processed"
    )
    total_pending: int = Field(description="Total number of pending documents")
    current_status: dict[str, Any] = Field(
        default={}, description="Current status of each document"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_busy": True,
                "current_track_id": "upload_20250729_170612_abc123",
                "total_pending": 5,
                "current_status": {"doc1.txt": "processing"},
            }
        }
    )


class LogLevelUpdateRequest(BaseModel):
    """Request model for updating pipeline log level.

    Attributes:
        log_level: New log level (10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL)
    """

    log_level: int = Field(
        ...,
        description="New log level (10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL)",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: int) -> int:
        if v not in [0, 10, 20, 30, 40, 50]:
            raise ValueError(
                "Log level must be one of: 0 (NOTSET), 10 (DEBUG), 20 (INFO), 30 (WARNING), 40 (ERROR), 50 (CRITICAL)"
            )
        return v

    model_config = ConfigDict(
        extra="allow"
    )  # Allow additional fields from the pipeline status
