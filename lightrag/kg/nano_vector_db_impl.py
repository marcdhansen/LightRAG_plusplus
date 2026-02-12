import asyncio
import base64
import os
import time
import zlib
from dataclasses import dataclass
from typing import Any, final

import numpy as np
from nano_vectordb import NanoVectorDB

from lightrag.base import BaseKeywordStorage, BaseVectorStorage
from lightrag.utils import (
    compute_mdhash_id,
    logger,
)

from .shared_storage import (
    get_namespace_lock,
    get_update_flag,
    set_all_update_flags,
)


@final
@dataclass
class NanoVectorDBStorage(BaseVectorStorage):
    def __post_init__(self):
        self._validate_embedding_func()
        # Initialize basic attributes
        self._client = None
        self._storage_lock = None
        self.storage_updated = None

        # Use global config value if specified, otherwise use default
        kwargs = self.global_config.get("vector_db_storage_cls_kwargs", {})
        cosine_threshold = kwargs.get("cosine_better_than_threshold")
        if cosine_threshold is None:
            raise ValueError(
                "cosine_better_than_threshold must be specified in vector_db_storage_cls_kwargs"
            )
        self.cosine_better_than_threshold = cosine_threshold

        working_dir = self.global_config["working_dir"]
        if self.workspace:
            # Include workspace in the file path for data isolation
            workspace_dir = os.path.join(working_dir, self.workspace)
            self.final_namespace = f"{self.workspace}_{self.namespace}"
        else:
            # Default behavior when workspace is empty
            self.final_namespace = self.namespace
            self.workspace = ""
            workspace_dir = working_dir

        os.makedirs(workspace_dir, exist_ok=True)
        self._client_file_name = os.path.join(
            workspace_dir, f"vdb_{self.namespace}.json"
        )

        self._max_batch_size = self.global_config["embedding_batch_num"]

        self._client = NanoVectorDB(
            self.embedding_func.embedding_dim,
            storage_file=self._client_file_name,
        )

    async def initialize(self):
        """Initialize storage data"""
        # Get the update flag for cross-process update notification
        self.storage_updated = await get_update_flag(
            self.namespace, workspace=self.workspace
        )
        # Get the storage lock for use in other methods
        self._storage_lock = get_namespace_lock(
            self.namespace, workspace=self.workspace
        )

    async def _get_client(self):
        """Check if the storage should be reloaded"""
        # Acquire lock to prevent concurrent read and write
        async with self._storage_lock:
            # Check if data needs to be reloaded
            if self.storage_updated.value:
                logger.info(
                    f"[{self.workspace}] Process {os.getpid()} reloading {self.namespace} due to update by another process"
                )
                # Reload data
                self._client = NanoVectorDB(
                    self.embedding_func.embedding_dim,
                    storage_file=self._client_file_name,
                )
                # Reset update flag
                self.storage_updated.value = False

            return self._client

    async def upsert(self, data: dict[str, dict[str, Any]]) -> None:
        """
        Importance notes:
        1. Changes will be persisted to disk during the next index_done_callback
        2. Only one process should updating the storage at a time before index_done_callback,
           KG-storage-log should be used to avoid data corruption
        """
        # logger.debug(f"[{self.workspace}] Inserting {len(data)} to {self.namespace}")
        if not data:
            return

        current_time = int(time.time())
        list_data = [
            {
                "__id__": k,
                "__created_at__": current_time,
                **{k1: v1 for k1, v1 in v.items() if k1 in self.meta_fields},
            }
            for k, v in data.items()
        ]
        contents = [v["content"] for v in data.values()]
        batches = [
            contents[i : i + self._max_batch_size]
            for i in range(0, len(contents), self._max_batch_size)
        ]

        # Execute embedding outside of lock to avoid long lock times
        embedding_tasks = [self.embedding_func(batch) for batch in batches]
        embeddings_list = await asyncio.gather(*embedding_tasks)

        embeddings = np.concatenate(embeddings_list)
        if len(embeddings) == len(list_data):
            for i, d in enumerate(list_data):
                # Compress vector using Float16 + zlib + Base64 for storage optimization
                vector_f16 = embeddings[i].astype(np.float16)
                compressed_vector = zlib.compress(vector_f16.tobytes())
                encoded_vector = base64.b64encode(compressed_vector).decode("utf-8")
                d["vector"] = encoded_vector
                d["__vector__"] = embeddings[i]
            client = await self._get_client()
            results = client.upsert(datas=list_data)
            return results
        else:
            # sometimes the embedding is not returned correctly. just log it.
            logger.error(
                f"[{self.workspace}] embedding is not 1-1 with data, {len(embeddings)} != {len(list_data)}"
            )

    async def query(
        self, query: str, top_k: int, query_embedding: list[float] = None
    ) -> list[dict[str, Any]]:
        # Enhanced query preprocessing for better matching
        original_query = query.strip()
        normalized_query = original_query.lower()  # Case normalization

        # Generate multiple query variants for better recall
        query_variants = [original_query]

        # For short proper names, try case variations to improve matching
        if len(original_query.split()) <= 3 and original_query.isalpha():
            query_variants.extend(
                [
                    normalized_query,
                    original_query.upper(),  # Case variation
                    original_query.capitalize(),  # Capitalized variation
                ]
            )

        best_results = []
        all_raw_results = []

        # Try each query variant and keep the best results
        for attempt_query in query_variants:
            embedding = await self.embedding_func([attempt_query], self.model_name)
            if embedding.size == 0:
                continue

            client = await self._get_client()
            raw_results = client.query(
                query=embedding[0],
                top_k=top_k,
                better_than_threshold=self.cosine_better_than_threshold,
            )

            all_raw_results.extend(raw_results)

            # Enhanced debugging for each query variant
            variant_matches = len(
                [dp for dp in raw_results if dp["__metrics__"] <= 0.3]
            )  # Good matches
            verbose_debug(
                f"[VECTOR] Query variant '{attempt_query}': {variant_matches} good matches"
            )

        if not all_raw_results:
            verbose_debug(f"[VECTOR] No results found for any query variant")
            return []

        # Apply adaptive threshold logic based on query characteristics
        base_threshold = max(0.1, self.cosine_better_than_threshold)

        # More permissive threshold for short, specific queries
        adaptive_threshold = base_threshold
        if len(original_query.split()) <= 2:  # Very short queries
            adaptive_threshold = max(0.05, self.cosine_better_than_threshold)
        elif len(original_query.split()) <= 4:  # Short queries
            adaptive_threshold = max(0.08, self.cosine_better_than_threshold)

        # Quality filtering with enhanced scoring
        filtered_results = []
        for dp in all_raw_results:
            distance = dp["__metrics__"]

            # Adaptive threshold application
            effective_threshold = adaptive_threshold

            # Quality scoring with distance normalization
            quality_score = max(0.0, 1.0 - distance)  # Higher is better

            # Multifactor quality assessment
            length_factor = 1.0
            if len(original_query.split()) <= 2:  # Bonus for very specific queries
                length_factor = 1.2
            elif len(original_query.split()) <= 4:  # Small bonus for short queries
                length_factor = 1.1
            elif len(original_query.split()) <= 6:  # Medium bonus
                length_factor = 1.05
            else:
                length_factor = 1.0

            final_quality_score = quality_score * length_factor

            if distance <= effective_threshold and final_quality_score >= 0.3:
                filtered_results.append(
                    {
                        **{k: v for k, v in dp.items() if k != "vector"},
                        "id": dp["__id__"],
                        "distance": distance,
                        "created_at": dp.get("__created_at__"),
                        "quality_score": final_quality_score,
                        "query_variant": attempt_query,
                        "adaptive_threshold": effective_threshold,
                    }
                )

        # Enhanced vector search debugging
        from lightrag.utils import verbose_debug

        # Comprehensive query analysis logging
        total_variants = len(query_variants)
        successful_variants = len(
            set(r.get("query_variant", original_query) for r in filtered_results)
        )

        verbose_debug(f"[VECTOR] Comprehensive Query Analysis:")
        verbose_debug(f"  • Original query: '{original_query}'")
        verbose_debug(f"  • Query variants tested: {total_variants}")
        verbose_debug(f"  • Successful variants: {successful_variants}")
        verbose_debug(f"  • Threshold used: {adaptive_threshold:.3f}")
        verbose_debug(
            f"  • Raw results: {len(all_raw_results)}, Filtered: {len(filtered_results)}"
        )

        # Log top results with enhanced information
        for i, result in enumerate(filtered_results[:3]):
            quality_score = result.get("quality_score", 0.0)
            query_used = result.get("query_variant", original_query)
            threshold_used = result.get("adaptive_threshold", adaptive_threshold)
            verbose_debug(
                f"[VECTOR] Top Match {i + 1}: id={result.get('id', 'unknown')}, distance={result.get('distance', 'unknown'):.3f}, quality={quality_score:.3f}, query='{query_used}', threshold={threshold_used:.3f}"
            )

        return filtered_results

    @property
    async def client_storage(self):
        client = await self._get_client()
        return client._NanoVectorDB__storage

    async def delete(self, ids: list[str]):
        """Delete vectors with specified IDs

        Importance notes:
        1. Changes will be persisted to disk during the next index_done_callback
        2. Only one process should updating the storage at a time before index_done_callback,
           KG-storage-log should be used to avoid data corruption

        Args:
            ids: List of vector IDs to be deleted
        """
        try:
            client = await self._get_client()
            # Record count before deletion
            before_count = len(client)

            client.delete(ids)

            # Calculate actual deleted count
            after_count = len(client)
            deleted_count = before_count - after_count

            logger.debug(
                f"[{self.workspace}] Successfully deleted {deleted_count} vectors from {self.namespace}"
            )
        except Exception as e:
            logger.error(
                f"[{self.workspace}] Error while deleting vectors from {self.namespace}: {e}"
            )

    async def delete_entity(self, entity_name: str) -> None:
        """
        Importance notes:
        1. Changes will be persisted to disk during the next index_done_callback
        2. Only one process should updating the storage at a time before index_done_callback,
           KG-storage-log should be used to avoid data corruption
        """

        try:
            entity_id = compute_mdhash_id(entity_name, prefix="ent-")
            logger.debug(
                f"[{self.workspace}] Attempting to delete entity {entity_name} with ID {entity_id}"
            )

            # Check if the entity exists
            client = await self._get_client()
            if client.get([entity_id]):
                client.delete([entity_id])
                logger.debug(
                    f"[{self.workspace}] Successfully deleted entity {entity_name}"
                )
            else:
                logger.debug(
                    f"[{self.workspace}] Entity {entity_name} not found in storage"
                )
        except Exception as e:
            logger.error(f"[{self.workspace}] Error deleting entity {entity_name}: {e}")

    async def delete_entity_relation(self, entity_name: str) -> None:
        """
        Importance notes:
        1. Changes will be persisted to disk during the next index_done_callback
        2. Only one process should updating the storage at a time before index_done_callback,
           KG-storage-log should be used to avoid data corruption
        """

        try:
            client = await self._get_client()
            storage = client._NanoVectorDB__storage
            relations = [
                dp
                for dp in storage["data"]
                if dp["src_id"] == entity_name or dp["tgt_id"] == entity_name
            ]
            logger.debug(
                f"[{self.workspace}] Found {len(relations)} relations for entity {entity_name}"
            )
            ids_to_delete = [relation["__id__"] for relation in relations]

            if ids_to_delete:
                client = await self._get_client()
                client.delete(ids_to_delete)
                logger.debug(
                    f"[{self.workspace}] Deleted {len(ids_to_delete)} relations for {entity_name}"
                )
            else:
                logger.debug(
                    f"[{self.workspace}] No relations found for entity {entity_name}"
                )
        except Exception as e:
            logger.error(
                f"[{self.workspace}] Error deleting relations for {entity_name}: {e}"
            )

    async def index_done_callback(self) -> bool:
        """Save data to disk"""
        async with self._storage_lock:
            # Check if storage was updated by another process
            if self.storage_updated.value:
                # Storage was updated by another process, reload data instead of saving
                logger.warning(
                    f"[{self.workspace}] Storage for {self.namespace} was updated by another process, reloading..."
                )
                self._client = NanoVectorDB(
                    self.embedding_func.embedding_dim,
                    storage_file=self._client_file_name,
                )
                # Reset update flag
                self.storage_updated.value = False
                return False  # Return error

        # Acquire lock and perform persistence
        async with self._storage_lock:
            try:
                # Save data to disk
                self._client.save()
                # Notify other processes that data has been updated
                await set_all_update_flags(self.namespace, workspace=self.workspace)
                # Reset own update flag to avoid self-reloading
                self.storage_updated.value = False
                return True  # Return success
            except Exception as e:
                logger.error(
                    f"[{self.workspace}] Error saving data for {self.namespace}: {e}"
                )
                return False  # Return error

        return True  # Return success

    async def get_by_id(self, id: str) -> dict[str, Any] | None:
        """Get vector data by its ID

        Args:
            id: The unique identifier of the vector

        Returns:
            The vector data if found, or None if not found
        """
        client = await self._get_client()
        result = client.get([id])
        if result:
            dp = result[0]
            return {
                **{k: v for k, v in dp.items() if k != "vector"},
                "id": dp.get("__id__"),
                "created_at": dp.get("__created_at__"),
            }
        return None

    async def get_by_ids(self, ids: list[str]) -> list[dict[str, Any]]:
        """Get multiple vector data by their IDs

        Args:
            ids: List of unique identifiers

        Returns:
            List of vector data objects that were found
        """
        if not ids:
            return []

        client = await self._get_client()
        results = client.get(ids)
        result_map: dict[str, dict[str, Any]] = {}

        for dp in results:
            if not dp:
                continue
            record = {
                **{k: v for k, v in dp.items() if k != "vector"},
                "id": dp.get("__id__"),
                "created_at": dp.get("__created_at__"),
            }
            key = record.get("id")
            if key is not None:
                result_map[str(key)] = record

        ordered_results: list[dict[str, Any] | None] = []
        for requested_id in ids:
            ordered_results.append(result_map.get(str(requested_id)))

        return ordered_results

    async def get_vectors_by_ids(self, ids: list[str]) -> dict[str, list[float]]:
        """Get vectors by their IDs, returning only ID and vector data for efficiency

        Args:
            ids: List of unique identifiers

        Returns:
            Dictionary mapping IDs to their vector embeddings
            Format: {id: [vector_values], ...}
        """
        if not ids:
            return {}

        client = await self._get_client()
        results = client.get(ids)

        vectors_dict = {}
        for result in results:
            if result and "vector" in result and "__id__" in result:
                # Decompress vector data (Base64 + zlib + Float16 compressed)
                decoded = base64.b64decode(result["vector"])
                decompressed = zlib.decompress(decoded)
                vector_f16 = np.frombuffer(decompressed, dtype=np.float16)
                vector_f32 = vector_f16.astype(np.float32).tolist()
                vectors_dict[result["__id__"]] = vector_f32

        return vectors_dict

    async def drop(self) -> dict[str, str]:
        """Drop all vector data from storage and clean up resources

        This method will:
        1. Remove the vector database storage file if it exists
        2. Reinitialize the vector database client
        3. Update flags to notify other processes
        4. Changes is persisted to disk immediately

        This method is intended for use in scenarios where all data needs to be removed,

        Returns:
            dict[str, str]: Operation status and message
            - On success: {"status": "success", "message": "data dropped"}
            - On failure: {"status": "error", "message": "<error details>"}
        """
        try:
            async with self._storage_lock:
                # delete _client_file_name
                if os.path.exists(self._client_file_name):
                    os.remove(self._client_file_name)

                self._client = NanoVectorDB(
                    self.embedding_func.embedding_dim,
                    storage_file=self._client_file_name,
                )

                # Notify other processes that data has been updated
                await set_all_update_flags(self.namespace, workspace=self.workspace)
                # Reset own update flag to avoid self-reloading
                self.storage_updated.value = False

                logger.info(
                    f"[{self.workspace}] Process {os.getpid()} drop {self.namespace}(file:{self._client_file_name})"
                )
            return {"status": "success", "message": "data dropped"}
        except Exception as e:
            logger.error(f"[{self.workspace}] Error dropping {self.namespace}: {e}")
            return {"status": "error", "message": str(e)}


@final
@dataclass
class NanoKeywordStorage(BaseKeywordStorage):
    """Simple keyword storage implementation using in-memory inverted index."""

    def __post_init__(self):
        # Initialize basic attributes
        self._keyword_index = {}  # keyword -> {doc_id: {"content": str, "score": float}}
        self._storage_lock = None

        working_dir = self.global_config["working_dir"]
        if self.workspace:
            workspace_dir = os.path.join(working_dir, self.workspace)
            self.final_namespace = f"{self.workspace}_{self.namespace}"
            self._storage_file = os.path.join(
                workspace_dir, f"{self.final_namespace}_keywords.json"
            )
        else:
            self.final_namespace = self.namespace
            self._storage_file = os.path.join(
                working_dir, f"{self.final_namespace}_keywords.json"
            )

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self._storage_file), exist_ok=True)

    async def initialize(self):
        """Initialize the storage"""
        from .shared_storage import get_namespace_lock

        self._storage_lock = get_namespace_lock(
            self.namespace, workspace=self.workspace
        )

        # Load existing keyword index if file exists
        if os.path.exists(self._storage_file):
            try:
                import json

                with open(self._storage_file, encoding="utf-8") as f:
                    self._keyword_index = json.load(f)
                logger.info(
                    f"[{self.workspace}] Loaded keyword index from {self._storage_file}"
                )
            except Exception as e:
                logger.error(f"[{self.workspace}] Failed to load keyword index: {e}")
                self._keyword_index = {}
        else:
            self._keyword_index = {}
            logger.info(f"[{self.workspace}] Created new keyword index")

    async def finalize(self):
        """Finalize the storage"""
        await self._save_index()

    async def index_done_callback(self) -> None:
        """Commit the storage operations after indexing"""
        await self._save_index()

    async def _save_index(self):
        """Save keyword index to disk"""
        try:
            import json

            async with self._storage_lock:
                with open(self._storage_file, "w", encoding="utf-8") as f:
                    json.dump(self._keyword_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[{self.workspace}] Failed to save keyword index: {e}")

    async def index_keywords(
        self, doc_id: str, keywords: list[str], content: str
    ) -> None:
        """Index keywords for a document."""
        async with self._storage_lock:
            for keyword in keywords:
                if keyword not in self._keyword_index:
                    self._keyword_index[keyword] = {}

                self._keyword_index[keyword][doc_id] = {
                    "content": content[:500],  # Store first 500 chars as preview
                    "score": 1.0,
                }

    async def search_keywords(
        self, keywords: list[str], limit: int = 50
    ) -> list[dict[str, Any]]:
        """Search for documents containing the given keywords."""
        doc_scores = {}  # doc_id -> total_score

        async with self._storage_lock:
            for keyword in keywords:
                if keyword in self._keyword_index:
                    for doc_id, doc_data in self._keyword_index[keyword].items():
                        if doc_id not in doc_scores:
                            doc_scores[doc_id] = {
                                "doc_id": doc_id,
                                "content": doc_data["content"],
                                "score": 0.0,
                                "keywords": [],
                            }
                        doc_scores[doc_id]["score"] += doc_data["score"]
                        doc_scores[doc_id]["keywords"].append(keyword)

        # Sort by score and limit results
        sorted_docs = sorted(
            doc_scores.values(), key=lambda x: x["score"], reverse=True
        )
        return sorted_docs[:limit]

    async def delete_document(self, doc_id: str) -> None:
        """Remove a document from the keyword index."""
        async with self._storage_lock:
            for keyword in list(self._keyword_index.keys()):
                if doc_id in self._keyword_index[keyword]:
                    del self._keyword_index[keyword][doc_id]
                # Clean up empty keyword entries
                if not self._keyword_index[keyword]:
                    del self._keyword_index[keyword]

    async def update_document(
        self, doc_id: str, keywords: list[str], content: str
    ) -> None:
        """Update keywords for an existing document."""
        await self.delete_document(doc_id)
        await self.index_keywords(doc_id, keywords, content)

    async def drop(self) -> dict[str, str]:
        """Drop all data from storage and clean up resources."""
        try:
            async with self._storage_lock:
                self._keyword_index = {}
                if os.path.exists(self._storage_file):
                    os.remove(self._storage_file)
                logger.info(
                    f"[{self.workspace}] Dropped keyword storage: {self._storage_file}"
                )
                return {"status": "success", "message": "data dropped"}
        except Exception as e:
            logger.error(f"[{self.workspace}] Error dropping keyword storage: {e}")
            return {"status": "error", "message": str(e)}
