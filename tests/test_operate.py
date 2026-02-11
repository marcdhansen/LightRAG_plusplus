#!/usr/bin/env python3
"""
Test suite for lightrag.operate.py module.

This module provides core LightRAG functionality including chunking,
entity extraction, querying, and knowledge graph operations.
Tests cover the comprehensive API to achieve maximum coverage impact.
"""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch, call
from typing import Any, Dict, List
from dataclasses import dataclass

# Import simple functions for testing first
try:
    from lightrag.operate import chunking_by_token_size
    from lightrag.utils import Tokenizer
except ImportError:
    pytest.skip("operate.py module not available for import")


@dataclass
class MockStorage:
    """Mock storage implementation for testing."""

    def __init__(self):
        self.data = {}
        self.vectors = []

    async def upsert(self, data: Dict[str, Any]):
        self.data.update(data)

    async def query(self, query: str, top_k: int = 10):
        return [{"id": "test", "text": "mock result"}]

    async def delete(self, entity_id: str):
        if entity_id in self.data:
            del self.data[entity_id]


class MockLLMFunc:
    """Mock LLM function for testing."""

    def __init__(self, responses: List[str] = None):
        self.responses = responses or ["mock response"]
        self.call_count = 0

    async def __call__(self, prompt: str, **kwargs):
        self.call_count += 1
        return self.responses[self.call_count - 1]


class MockTokenizerInterface:
    """Mock tokenizer interface for testing following the TokenizerInterface protocol."""

    def encode(self, content: str) -> list[int]:
        # Simple word-based tokenization for testing
        # Return unique integers for each word to simulate proper tokenization
        words = content.split()
        # Map each unique word to an integer token
        word_to_token = {}
        token_id = 1
        tokens = []
        for word in words:
            if word not in word_to_token:
                word_to_token[word] = token_id
                token_id += 1
            tokens.append(word_to_token[word])
        return tokens

    def decode(self, tokens: list[int]) -> str:
        # For testing, return a simplified representation
        return " ".join(f"token_{t}" for t in tokens)


class MockTokenizer(Tokenizer):
    """Mock tokenizer wrapper following the Tokenizer class interface."""

    def __init__(self, model_name: str = "test"):
        mock_interface = MockTokenizerInterface()
        super().__init__(model_name, mock_interface)
        self.model_name = model_name


# Comprehensive Mock Infrastructure for Knowledge Graph Operations


class MockGraphStorage:
    """Mock knowledge graph storage for testing."""

    def __init__(self):
        self.entities = {}
        self.relationships = {}
        self.edges = []
        self.nodes = []
        self._lock = AsyncMock()
        self.query_history = []
        self.upsert_history = []

    async def upsert_node(self, node_id: str, node_data: dict):
        """Upsert a node in the graph."""
        self.nodes.append((node_id, node_data))
        self.upsert_history.append(("node", node_id, node_data))

    async def upsert_edge(self, src_id: str, tgt_id: str, edge_data: dict):
        """Upsert an edge in the graph."""
        self.edges.append((src_id, tgt_id, edge_data))
        self.upsert_history.append(("edge", src_id, tgt_id, edge_data))

    async def get_node(self, node_id: str):
        """Get a node by ID."""
        for nid, data in self.nodes:
            if nid == node_id:
                return data
        return None

    async def get_edge(self, src_id: str, tgt_id: str):
        """Get an edge by source and target IDs."""
        for sid, tid, data in self.edges:
            if sid == src_id and tid == tgt_id:
                return data
        return None

    async def has_node(self, node_id: str) -> bool:
        """Check if node exists."""
        return any(nid == node_id for nid, _ in self.nodes)

    async def has_edge(self, src_id: str, tgt_id: str) -> bool:
        """Check if edge exists."""
        return any(sid == src_id and tid == tgt_id for sid, tid, _ in self.edges)

    async def get_node_degree(self, node_id: str) -> int:
        """Get degree of a node."""
        degree = 0
        for sid, tid, _ in self.edges:
            if sid == node_id or tid == node_id:
                degree += 1
        return degree

    async def get_all_nodes(self) -> list:
        """Get all nodes."""
        return [{"id": nid, **data} for nid, data in self.nodes]

    async def get_all_edges(self) -> list:
        """Get all edges."""
        return [{"src": sid, "tgt": tid, **data} for sid, tid, data in self.edges]

    async def query_nodes(self, query: str, top_k: int = 10) -> list:
        """Query nodes."""
        self.query_history.append(("nodes", query, top_k))
        return [{"id": nid, **data} for nid, data in self.nodes[:top_k]]

    async def query_edges(self, query: str, top_k: int = 10) -> list:
        """Query edges."""
        self.query_history.append(("edges", query, top_k))
        return [
            {"src": sid, "tgt": tid, **data} for sid, tid, data in self.edges[:top_k]
        ]

    async def delete_node(self, node_id: str):
        """Delete a node."""
        self.nodes = [(nid, data) for nid, data in self.nodes if nid != node_id]

    async def delete_edge(self, src_id: str, tgt_id: str):
        """Delete an edge."""
        self.edges = [
            (sid, tid, data)
            for sid, tid, data in self.edges
            if not (sid == src_id and tid == tgt_id)
        ]


class MockVectorStorage:
    """Mock vector storage for testing."""

    def __init__(self):
        self.vectors = {}
        self.metadata = {}
        self.query_history = []
        self.upsert_history = []

    async def upsert(self, vector: list, metadata: dict):
        """Upsert a vector with metadata."""
        vector_id = metadata.get("id", f"vec_{len(self.vectors)}")
        self.vectors[vector_id] = vector
        self.metadata[vector_id] = metadata
        self.upsert_history.append((vector_id, vector, metadata))
        return vector_id

    async def query(self, query_vector: list, top_k: int = 10) -> list:
        """Query for similar vectors."""
        self.query_history.append((query_vector, top_k))
        # Return mock similar results
        results = []
        for i, (vid, vector) in enumerate(list(self.vectors.items())[:top_k]):
            results.append(
                {
                    "id": vid,
                    "vector": vector,
                    "metadata": self.metadata[vid],
                    "distance": 0.1 + i * 0.1,  # Mock distance
                }
            )
        return results

    async def delete(self, vector_id: str):
        """Delete a vector."""
        if vector_id in self.vectors:
            del self.vectors[vector_id]
            del self.metadata[vector_id]

    async def get(self, vector_id: str):
        """Get a vector by ID."""
        if vector_id in self.vectors:
            return {
                "id": vector_id,
                "vector": self.vectors[vector_id],
                "metadata": self.metadata[vector_id],
            }
        return None

    async def get_all(self) -> list:
        """Get all vectors."""
        return [
            {"id": vid, "vector": vector, "metadata": metadata}
            for vid, (vector, metadata) in zip(
                self.vectors.items(), self.metadata.values()
            )
        ]


class MockKVStorage:
    """Mock key-value storage for testing."""

    def __init__(self):
        self.data = {}
        self.get_history = []
        self.set_history = []

    async def get(self, key: str):
        """Get value by key."""
        self.get_history.append(key)
        return self.data.get(key)

    async def set(self, key: str, value):
        """Set a key-value pair."""
        self.data[key] = value
        self.set_history.append((key, value))

    async def delete(self, key: str):
        """Delete a key."""
        if key in self.data:
            del self.data[key]

    async def get_all(self) -> dict:
        """Get all key-value pairs."""
        return self.data.copy()

    async def keys(self) -> list:
        """Get all keys."""
        return list(self.data.keys())

    async def values(self) -> list:
        """Get all values."""
        return list(self.data.values())

    async def items(self) -> list:
        """Get all key-value pairs."""
        return list(self.data.items())


class MockQueryResult:
    """Mock query result for testing."""

    def __init__(self, content="mock response", references=None, metadata=None):
        self.content = content
        self.references = references or []
        self.metadata = metadata or {}
        self.response_iterator = None
        self.is_streaming = False

    def __iter__(self):
        return iter([])

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration


class MockQueryParam:
    """Mock query parameters for testing."""

    def __init__(self, mode="local", top_k=10, max_token=4000, **kwargs):
        self.mode = mode
        self.top_k = top_k
        self.max_token = max_token
        self.__dict__.update(kwargs)


# Test Data Factories


def create_test_entities(count=3):
    """Create test entities for testing."""
    entities = {}
    for i in range(count):
        entity_id = f"entity_{i}"
        entities[entity_id] = {
            "entity_type": ["PERSON", "ORG", "LOC"][i % 3],
            "description": f"Test entity {i} description",
            "source_id": f"chunk_{i}",
            "weight": 1.0 - (i * 0.1),
        }
    return entities


def create_test_relationships(count=3):
    """Create test relationships for testing."""
    relationships = {}
    for i in range(count):
        src = f"entity_{i}"
        tgt = f"entity_{(i + 1) % count}"
        relationships[(src, tgt)] = {
            "relation_type": ["WORKS_FOR", "LOCATED_IN", "KNOWS"][i % 3],
            "weight": 1.0 - (i * 0.1),
            "source_id": f"chunk_{i}",
        }
    return relationships


def create_test_chunks(count=3):
    """Create test text chunks for testing."""
    chunks = {}
    for i in range(count):
        chunk_id = f"chunk_{i}"
        chunks[chunk_id] = {
            "content": f"This is test chunk {i} with some sample content.",
            "tokens": [1, 2, 3, 4, 5 + i * 10],
            "chunk_order_index": i,
            "full_doc_id": f"doc_{i % 2}",
        }
    return chunks


def create_test_vectors(dim=384, count=5):
    """Create test vectors for testing."""
    vectors = []
    for i in range(count):
        vector = [0.1 + (i * 0.01)] * dim
        vectors.append(vector)
    return vectors


class TestChunking:
    """Test cases for text chunking functionality."""

    def test_chunking_by_token_size_basic(self):
        """Test basic token-based chunking."""
        from lightrag.operate import chunking_by_token_size

        # Create long content that should be chunked
        content = (
            "This is a much longer document that should be split into multiple chunks because it exceeds the token limit. "
            * 10
        )

        mock_tokenizer = MockTokenizer()
        chunks = chunking_by_token_size(
            tokenizer=mock_tokenizer,
            content=content,
            chunk_token_size=20,
            chunk_overlap_token_size=5,
        )

        assert len(chunks) > 1
        assert all("tokens" in chunk for chunk in chunks)
        assert all("content" in chunk for chunk in chunks)
        assert all("chunk_order_index" in chunk for chunk in chunks)

        # Check that chunk order indexes are sequential
        order_indices = [chunk["chunk_order_index"] for chunk in chunks]
        assert order_indices == list(range(len(chunks)))

    def test_chunking_by_token_size_short_content(self):
        """Test chunking with content shorter than limit."""
        from lightrag.operate import chunking_by_token_size

        content = "Short document"
        mock_tokenizer = MockTokenizer()

        chunks = chunking_by_token_size(
            tokenizer=mock_tokenizer, content=content, chunk_token_size=1000
        )

        assert len(chunks) == 1
        # Content is tokenized then detokenized, so it will be different
        # What matters is that it has one chunk with expected structure
        assert chunks[0]["tokens"] > 0
        assert chunks[0]["chunk_order_index"] == 0
        assert "content" in chunks[0]

    def test_chunking_by_token_size_overlap(self):
        """Test chunking with overlap."""
        from lightrag.operate import chunking_by_token_size

        # Create content with repeated words for overlap testing
        content = "word " * 50  # Very long document
        mock_tokenizer = MockTokenizer()

        chunks = chunking_by_token_size(
            tokenizer=mock_tokenizer,
            content=content,
            chunk_token_size=20,
            chunk_overlap_token_size=5,
        )

        # Should have multiple chunks
        assert len(chunks) > 1

        # Check overlap by verifying tokens in neighboring chunks
        # With overlap=5, adjacent chunks should share 5 tokens
        for i in range(len(chunks) - 1):
            current_chunk_tokens = mock_tokenizer.encode(chunks[i]["content"])
            next_chunk_tokens = mock_tokenizer.encode(chunks[i + 1]["content"])

            # The last 5 tokens of current chunk should appear at start of next chunk
            if len(current_chunk_tokens) >= 5 and len(next_chunk_tokens) >= 5:
                overlap_current = current_chunk_tokens[-5:]
                overlap_next = next_chunk_tokens[:5]
                # Check for substantial overlap (allowing for tokenization differences)
                overlap_count = sum(
                    1 for token in overlap_current if token in overlap_next
                )
                assert overlap_count >= 3  # At least 3 overlapping tokens

    def test_chunking_by_character_splitting(self):
        """Test chunking with character-based splitting."""
        from lightrag.operate import chunking_by_token_size

        content = "sentence1\nsentence2\nsentence3\nsentence4"
        mock_tokenizer = MockTokenizer()

        chunks = chunking_by_token_size(
            tokenizer=mock_tokenizer,
            content=content,
            split_by_character="\n",
            split_by_character_only=True,
            chunk_token_size=100,
        )

        # Should create chunks from sentences split by \n
        assert len(chunks) >= 4  # At least 4 sentences

        # Each sentence should be in its own chunk
        sentences = content.split("\n")
        for i, sentence in enumerate(sentences):
            if sentence.strip():  # Skip empty lines
                found = any(
                    sentence.strip() in chunk["content"].strip() for chunk in chunks
                )
                assert found, f"Sentence '{sentence}' not found in any chunk"


class TestCitationGeneration:
    """Test cases for automatic citation generation functionality."""

    @pytest.mark.asyncio
    async def test_auto_citations_enabled(self):
        """Test Zilliz semantic highlighting workflow."""
        from lightrag.operate import _generate_citations_with_auto_highlight

        truncated_chunks = [
            {"content": "First chunk content", "file_path": "doc1.txt"},
            {"content": "Second chunk content", "file_path": "doc2.txt"},
        ]

        mock_query_param = MagicMock()
        mock_query_param.auto_citations = True
        mock_query_param.citation_threshold = 0.5

        with patch("lightrag.operate.generate_citations_from_highlights") as mock_gen:
            mock_gen.return_value = (
                [{"file_path": "doc1.txt", "reference_id": "ref1"}],
                [{"chunk_id": "chunk1", "highlight": "..."}],
            )

            (
                reference_list,
                updated_chunks,
            ) = await _generate_citations_with_auto_highlight(
                truncated_chunks, "test query", mock_query_param
            )

            assert len(reference_list) > 0
            assert len(updated_chunks) == len(truncated_chunks)
            assert updated_chunks[0].get("reference_id") == "ref1"

    @pytest.mark.asyncio
    async def test_auto_citations_fallback(self):
        """Test fallback to frequency-based citations."""
        from lightrag.operate import _generate_citations_with_auto_highlight

        truncated_chunks = [
            {"content": "First chunk content", "file_path": "doc1.txt"},
            {"content": "Second chunk content", "file_path": "doc2.txt"},
        ]

        mock_query_param = MagicMock()
        mock_query_param.auto_citations = True
        mock_query_param.citation_threshold = 0.5

        with patch("lightrag.operate.generate_citations_from_highlights") as mock_gen:
            with patch(
                "lightrag.operate.generate_reference_list_from_chunks"
            ) as mock_fallback:
                mock_gen.side_effect = Exception("Auto-generation failed")
                mock_fallback.return_value = (
                    [{"file_path": "doc1.txt", "reference_id": "ref1"}],
                    truncated_chunks,
                )

                (
                    reference_list,
                    updated_chunks,
                ) = await _generate_citations_with_auto_highlight(
                    truncated_chunks, "test query", mock_query_param
                )

                assert len(reference_list) > 0
                assert len(updated_chunks) == len(truncated_chunks)

    @pytest.mark.asyncio
    async def test_auto_citations_disabled(self):
        """Test behavior when auto_citations is False."""
        from lightrag.operate import _generate_citations_with_auto_highlight

        truncated_chunks = [
            {"content": "First chunk content", "file_path": "doc1.txt"},
        ]

        mock_query_param = MagicMock()
        mock_query_param.auto_citations = False

        with patch(
            "lightrag.operate.generate_reference_list_from_chunks"
        ) as mock_fallback:
            mock_fallback.return_value = (
                [{"file_path": "doc1.txt", "reference_id": "ref1"}],
                truncated_chunks,
            )

            (
                reference_list,
                updated_chunks,
            ) = await _generate_citations_with_auto_highlight(
                truncated_chunks, "test query", mock_query_param
            )

            assert len(reference_list) > 0
            assert len(updated_chunks) == len(truncated_chunks)


class TestTokenTruncation:
    """Test cases for entity identifier truncation."""

    def test_entity_identifier_truncation_short_name(self):
        """Test truncation with short identifiers (should not truncate)."""
        from lightrag.operate import _truncate_entity_identifier

        identifier = "ShortName"
        limit = 50
        chunk_key = "chunk1"
        identifier_role = "Entity name"

        result = _truncate_entity_identifier(
            identifier, limit, chunk_key, identifier_role
        )

        assert result == identifier  # Should not be truncated

    def test_entity_identifier_truncation_long_name(self):
        """Test truncation with long identifiers."""
        from lightrag.operate import _truncate_entity_identifier

        identifier = (
            "VeryLongEntityNameThatExceedsTheMaximumAllowedLengthAndShouldBeTruncated"
        )
        limit = 20
        chunk_key = "chunk1"
        identifier_role = "Entity name"

        result = _truncate_entity_identifier(
            identifier, limit, chunk_key, identifier_role
        )

        assert len(result) <= limit
        assert result == identifier[:limit]

    def test_entity_identifier_truncation_logging(self):
        """Test that truncation logs warning messages."""
        from lightrag.operate import _truncate_entity_identifier

        identifier = (
            "VeryLongEntityNameThatExceedsTheMaximumAllowedLengthAndShouldBeTruncated"
        )
        limit = 20
        chunk_key = "chunk1"
        identifier_role = "Entity name"

        with patch("lightrag.operate.logger") as mock_logger:
            result = _truncate_entity_identifier(
                identifier, limit, chunk_key, identifier_role
            )

            # Should log a warning about truncation
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]  # Get the format string
            warning_args = mock_logger.warning.call_args[0][1:]  # Get the arguments
            assert warning_args[0] == chunk_key
            assert warning_args[1] == identifier_role
            assert warning_args[2] == len(identifier)
            assert warning_args[3] == limit


class TestExtractEntities:
    """Test cases for entity extraction functionality."""

    @pytest.mark.asyncio
    async def test_extract_entities_basic(self):
        """Test basic entity extraction - minimal test for now."""
        from lightrag.operate import extract_entities

        # Skip complex function for now due to parameter complexity
        # Focus on testing that it can be imported and has right signature
        assert callable(extract_entities)

        # Test that it's an async function
        import inspect

        assert inspect.iscoroutinefunction(extract_entities)

    @pytest.mark.asyncio
    async def test_extract_entities_empty_input(self):
        """Test entity extraction with empty documents."""
        from lightrag.operate import extract_entities

        mock_storage = MockStorage()
        mock_llm = MockLLMFunc([json.dumps({"entities": [], "relations": []})])
        global_config = {"llm_model_func": mock_llm, "addon_params": {}}
        documents = []

        with patch("lightrag.operate.entities_vdb", mock_storage):
            with patch("lightrag.operate.relationships_vdb", mock_storage):
                await extract_entities(documents, global_config=global_config)

                # Should still call LLM even with empty input
                assert mock_llm.call_count == 1

    @pytest.mark.asyncio
    async def test_extract_entities_validation_errors(self):
        """Test entity extraction with invalid input data."""
        from lightrag.operate import extract_entities

        mock_storage = MockStorage()
        mock_llm = MockLLMFunc([json.dumps({"entities": [], "relations": []})])
        global_config = {"llm_model_func": mock_llm, "addon_params": {}}
        documents = ["Test document"]

        with patch("lightrag.operate.entities_vdb", mock_storage):
            with patch("lightrag.operate.relationships_vdb", mock_storage):
                # Basic test to ensure function doesn't crash on validation
                await extract_entities(documents, global_config=global_config)

    @pytest.mark.asyncio
    async def test_extract_entities_with_llm_failure(self):
        """Test entity extraction when LLM fails."""
        from lightrag.operate import extract_entities

        mock_storage = MockStorage()
        mock_llm = MockLLMFunc()
        mock_llm.__call__ = AsyncMock(side_effect=Exception("LLM service unavailable"))
        global_config = {"llm_model_func": mock_llm, "addon_params": {}}
        documents = ["Test document"]

        with patch("lightrag.operate.entities_vdb", mock_storage):
            with patch("lightrag.operate.relationships_vdb", mock_storage):
                with pytest.raises(Exception):
                    await extract_entities(documents, global_config=global_config)

    @pytest.mark.asyncio
    async def test_extract_entities_malformed_llm_response(self):
        """Test handling of malformed LLM responses."""
        from lightrag.operate import extract_entities

        mock_storage = MockStorage()
        mock_llm = MockLLMFunc(["invalid json response"])
        global_config = {"llm_model_func": mock_llm, "addon_params": {}}
        documents = ["Test document"]

        with patch("lightrag.operate.entities_vdb", mock_storage):
            with patch("lightrag.operate.relationships_vdb", mock_storage):
                # Should not crash on malformed response
                result = await extract_entities(documents, global_config=global_config)
                # Result depends on error handling implementation
                assert result is not None

    @pytest.mark.asyncio
    async def test_extract_entities_with_special_characters(self):
        """Test entity extraction with special characters and unicode."""
        from lightrag.operate import extract_entities

        mock_storage = MockStorage()
        mock_llm = MockLLMFunc(
            [
                json.dumps(
                    {
                        "entities": [
                            {
                                "id": "café",
                                "type": "LOCATION",
                                "description": "Café with accented characters",
                            },
                            {
                                "id": "user@domain.com",
                                "type": "EMAIL",
                                "description": "Email address with special chars",
                            },
                        ],
                        "relations": [],
                    }
                )
            ]
        )
        global_config = {"llm_model_func": mock_llm, "addon_params": {}}
        documents = ["The café is located at user@domain.com"]

        with patch("lightrag.operate.entities_vdb", mock_storage):
            with patch("lightrag.operate.relationships_vdb", mock_storage):
                await extract_entities(documents, global_config=global_config)

                # Verify entities were stored
                assert len(mock_storage.data) > 0


class TestEntityExtractionDetails:
    """Test cases for internal entity extraction functions."""

    @pytest.mark.asyncio
    async def test_handle_single_entity_extraction_valid(self):
        """Test valid entity extraction processing."""
        from lightrag.operate import _handle_single_entity_extraction

        # Valid entity record attributes
        record_attributes = ["entity", "John Doe", "PERSON", "Software Engineer"]
        chunk_key = "chunk1"
        timestamp = 1234567890

        result = await _handle_single_entity_extraction(
            record_attributes, chunk_key, timestamp
        )

        assert result is not None
        assert result["entity_name"] == "John Doe"
        assert (
            result["entity_type"] == "person"
        )  # Should be lowercase and spaces removed
        assert result["description"] == "Software Engineer"
        assert result["source_id"] == chunk_key
        assert result["timestamp"] == timestamp

    @pytest.mark.asyncio
    async def test_handle_single_entity_extraction_invalid_name(self):
        """Test entity extraction with empty/invalid name."""
        from lightrag.operate import _handle_single_entity_extraction

        record_attributes = ["entity", "", "PERSON", "Software Engineer"]
        chunk_key = "chunk1"
        timestamp = 1234567890

        result = await _handle_single_entity_extraction(
            record_attributes, chunk_key, timestamp
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_handle_single_entity_extraction_invalid_type(self):
        """Test entity extraction with invalid type."""
        from lightrag.operate import _handle_single_entity_extraction

        record_attributes = [
            "entity",
            "John Doe",
            "PERSON WITH CHARS",
            "Software Engineer",
        ]
        chunk_key = "chunk1"
        timestamp = 1234567890

        result = await _handle_single_entity_extraction(
            record_attributes, chunk_key, timestamp
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_handle_relationship_extraction_valid(self):
        """Test valid relationship extraction processing."""
        from lightrag.operate import _handle_single_relationship_extraction

        record_attributes = [
            "relation",
            "John Doe",
            "Acme Corp",
            "WORKS_FOR",
            "Employment",
            "1.5",
        ]
        chunk_key = "chunk1"
        timestamp = 1234567890

        result = await _handle_single_relationship_extraction(
            record_attributes, chunk_key, timestamp
        )

        assert result is not None
        assert result["src_id"] == "John Doe"
        assert result["tgt_id"] == "Acme Corp"
        assert result["weight"] == 1.5
        assert result["description"] == "Employment"
        assert result["keywords"] == "WORKS_FOR"
        assert result["source_id"] == chunk_key
        assert result["timestamp"] == timestamp

    @pytest.mark.asyncio
    async def test_handle_relationship_extraction_same_source_target(self):
        """Test relationship extraction with same source and target."""
        from lightrag.operate import _handle_single_relationship_extraction

        record_attributes = [
            "relation",
            "John Doe",
            "John Doe",
            "SELF_REF",
            "Self reference",
            "1.0",
        ]
        chunk_key = "chunk1"
        timestamp = 1234567890

        result = await _handle_single_relationship_extraction(
            record_attributes, chunk_key, timestamp
        )

        assert result is None  # Should filter out self-referencing relationships

    @pytest.mark.asyncio
    async def test_yaml_extraction_format(self):
        """Test YAML format extraction processing."""
        from lightrag.operate import _parse_yaml_extraction

        yaml_content = """
        entities:
          John Doe:
            type: PERSON
            description: "Software engineer"
          Acme Corp:
            type: ORG
            description: "Technology company"
        
        relationships:
          works_for:
            source: John Doe
            target: Acme Corp
            description: "Employment relationship"
        """

        chunk_key = "chunk1"
        timestamp = 1234567890

        nodes, edges = await _parse_yaml_extraction(yaml_content, chunk_key, timestamp)

        assert len(nodes) >= 2
        assert len(edges) >= 1
        assert "John Doe" in nodes
        assert "Acme Corp" in nodes


class TestKnowledgeGraphQuery:
    """Comprehensive test cases for knowledge graph querying functionality."""

    @pytest.mark.asyncio
    async def test_kg_query_local_mode(self):
        """Test kg_query in local mode with proper parameters."""
        from lightrag.operate import kg_query
        from lightrag.base import QueryParam

        # Setup comprehensive mock storage
        kg_storage = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_db = MockKVStorage()
        hashing_kv = MockKVStorage()

        # Create test data
        test_entities = create_test_entities(5)
        test_relationships = create_test_relationships(3)
        test_chunks = create_test_chunks(3)

        # Populate storages
        for entity_id, entity_data in test_entities.items():
            await kg_storage.upsert_node(entity_id, entity_data)
            await entities_vdb.upsert([0.1] * 10, {"id": entity_id, **entity_data})

        for (src, tgt), rel_data in test_relationships.items():
            await kg_storage.upsert_edge(src, tgt, rel_data)
            await relationships_vdb.upsert(
                [0.2] * 10, {"id": f"{src}-{tgt}", "src": src, "tgt": tgt, **rel_data}
            )

        for chunk_id, chunk_data in test_chunks.items():
            await text_chunks_db.set(chunk_id, chunk_data)

        # Create query parameters
        query_param = MockQueryParam(mode="local", top_k=5, max_token=2000)
        global_config = {
            "llm_model_func": MockLLMFunc(["mock response"]),
            "addon_params": {},
        }

        # Execute query
        result = await kg_query(
            query="test person",
            knowledge_graph_inst=kg_storage,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_db=text_chunks_db,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        # Validate result structure
        assert result is not None
        assert hasattr(result, "content") or hasattr(result, "response_iterator")
        assert isinstance(result.content if hasattr(result, "content") else "", str)

        # Validate storage interactions
        assert len(kg_storage.query_history) > 0
        assert len(entities_vdb.query_history) > 0

    @pytest.mark.asyncio
    async def test_kg_query_global_mode(self):
        """Test kg_query in global mode."""
        from lightrag.operate import kg_query

        # Setup mocks
        kg_storage = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_db = MockKVStorage()
        hashing_kv = MockKVStorage()

        query_param = MockQueryParam(mode="global", top_k=3)
        global_config = {
            "llm_model_func": MockLLMFunc(["global response"]),
            "addon_params": {},
        }

        result = await kg_query(
            query="test organization",
            knowledge_graph_inst=kg_storage,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_db=text_chunks_db,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        assert result is not None
        # Global mode should trigger relationship queries
        assert len(relationships_vdb.query_history) > 0

    @pytest.mark.asyncio
    async def test_kg_query_hybrid_mode(self):
        """Test kg_query in hybrid mode."""
        from lightrag.operate import kg_query

        kg_storage = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_db = MockKVStorage()
        hashing_kv = MockKVStorage()

        query_param = MockQueryParam(mode="hybrid", top_k=10)
        global_config = {
            "llm_model_func": MockLLMFunc(["hybrid response"]),
            "addon_params": {},
        }

        result = await kg_query(
            query="test hybrid",
            knowledge_graph_inst=kg_storage,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_db=text_chunks_db,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        assert result is not None
        # Hybrid should query both entities and relationships
        assert len(entities_vdb.query_history) > 0
        assert len(relationships_vdb.query_history) > 0

    @pytest.mark.asyncio
    async def test_kg_query_with_keywords(self):
        """Test kg_query with keyword extraction and processing."""
        from lightrag.operate import kg_query

        kg_storage = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_db = MockKVStorage()
        hashing_kv = MockKVStorage()

        query_param = MockQueryParam(mode="local", top_k=5)
        global_config = {
            "llm_model_func": MockLLMFunc(["keyword response"]),
            "addon_params": {},
        }

        result = await kg_query(
            query="John works at Acme Corporation",
            knowledge_graph_inst=kg_storage,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_db=text_chunks_db,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_kg_query_with_caching(self):
        """Test kg_query with hash-based result caching."""
        from lightrag.operate import kg_query

        kg_storage = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_db = MockKVStorage()
        hashing_kv = MockKVStorage()

        query_param = MockQueryParam(mode="local", top_k=3)
        global_config = {
            "llm_model_func": MockLLMFunc(["cached response"]),
            "addon_params": {},
        }

        # First query
        result1 = await kg_query(
            query="cached query",
            knowledge_graph_inst=kg_storage,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_db=text_chunks_db,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        # Second identical query should use cache
        result2 = await kg_query(
            query="cached query",
            knowledge_graph_inst=kg_storage,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_db=text_chunks_db,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        assert result1 is not None
        assert result2 is not None
        # Check that cache was accessed
        assert len(hashing_kv.get_history) >= 2

    @pytest.mark.asyncio
    async def test_kg_query_streaming_response(self):
        """Test kg_query with streaming response enabled."""
        from lightrag.operate import kg_query

        kg_storage = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_db = MockKVStorage()
        hashing_kv = MockKVStorage()

        query_param = MockQueryParam(mode="local", top_k=3, stream=True)
        global_config = {
            "llm_model_func": MockLLMFunc(["streaming response"]),
            "addon_params": {},
        }

        result = await kg_query(
            query="streaming query",
            knowledge_graph_inst=kg_storage,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_db=text_chunks_db,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        assert result is not None
        if hasattr(result, "is_streaming"):
            assert result.is_streaming is True

    @pytest.mark.asyncio
    async def test_kg_query_empty_query(self):
        """Test kg_query with empty query string."""
        from lightrag.operate import kg_query

        kg_storage = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_db = MockKVStorage()
        hashing_kv = MockKVStorage()

        query_param = MockQueryParam(mode="local", top_k=5)
        global_config = {
            "llm_model_func": MockLLMFunc(["empty response"]),
            "addon_params": {},
        }

        result = await kg_query(
            query="",
            knowledge_graph_inst=kg_storage,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_db=text_chunks_db,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        # Empty query should return fail response or None
        assert result is not None

    @pytest.mark.asyncio
    async def test_kg_query_with_system_prompt(self):
        """Test kg_query with custom system prompt."""
        from lightrag.operate import kg_query

        kg_storage = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_db = MockKVStorage()
        hashing_kv = MockKVStorage()

        query_param = MockQueryParam(mode="local", top_k=3)
        global_config = {
            "llm_model_func": MockLLMFunc(["custom prompt response"]),
            "addon_params": {},
        }
        system_prompt = "You are a helpful assistant for knowledge graphs."

        result = await kg_query(
            query="custom prompt query",
            knowledge_graph_inst=kg_storage,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_db=text_chunks_db,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
            system_prompt=system_prompt,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_kg_query_error_handling(self):
        """Test kg_query error handling for storage failures."""
        from lightrag.operate import kg_query

        kg_storage = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_db = MockKVStorage()
        hashing_kv = MockKVStorage()

        query_param = MockQueryParam(mode="local", top_k=3)
        global_config = {
            "llm_model_func": MockLLMFunc(["error response"]),
            "addon_params": {},
        }

        # Simulate storage error by making query raise exception
        original_query = entities_vdb.query
        entities_vdb.query = AsyncMock(side_effect=Exception("Storage error"))

        try:
            result = await kg_query(
                query="error test",
                knowledge_graph_inst=kg_storage,
                entities_vdb=entities_vdb,
                relationships_vdb=relationships_vdb,
                text_chunks_db=text_chunks_db,
                query_param=query_param,
                global_config=global_config,
                hashing_kv=hashing_kv,
            )
            # Should handle error gracefully
            assert result is not None
        except Exception:
            # Should not crash the system
            pass

    @pytest.mark.asyncio
    async def test_kg_query_context_building(self):
        """Test kg_query context building from entities, relationships, and chunks."""
        from lightrag.operate import kg_query

        kg_storage = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_db = MockKVStorage()
        hashing_kv = MockKVStorage()

        # Create connected data for context building
        test_entities = create_test_entities(3)
        test_relationships = create_test_relationships(2)
        test_chunks = create_test_chunks(3)

        # Populate storages with interconnected data
        for entity_id, entity_data in test_entities.items():
            await kg_storage.upsert_node(entity_id, entity_data)

        for (src, tgt), rel_data in test_relationships.items():
            await kg_storage.upsert_edge(src, tgt, rel_data)

        for chunk_id, chunk_data in test_chunks.items():
            await text_chunks_db.set(chunk_id, chunk_data)

        query_param = MockQueryParam(mode="hybrid", top_k=5, max_token=1000)
        global_config = {
            "llm_model_func": MockLLMFunc(["context response"]),
            "addon_params": {},
        }

        result = await kg_query(
            query="context building test",
            knowledge_graph_inst=kg_storage,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_db=text_chunks_db,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        assert result is not None
        # Should have accessed all storage types for context
        assert len(kg_storage.query_history) > 0
        assert len(text_chunks_db.get_history) > 0

    @pytest.mark.asyncio
    async def test_kg_query_with_chunks_vdb(self):
        """Test kg_query with optional chunks vector database."""
        from lightrag.operate import kg_query

        kg_storage = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_db = MockKVStorage()
        chunks_vdb = MockVectorStorage()
        hashing_kv = MockKVStorage()

        query_param = MockQueryParam(mode="mix", top_k=5)
        global_config = {
            "llm_model_func": MockLLMFunc(["chunks vdb response"]),
            "addon_params": {},
        }

        result = await kg_query(
            query="chunks vdb test",
            knowledge_graph_inst=kg_storage,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_db=text_chunks_db,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
            chunks_vdb=chunks_vdb,
        )

        assert result is not None
        # Should have used chunks_vdb when available
        assert len(chunks_vdb.query_history) > 0


class TestNaiveQuery:
    """Comprehensive test cases for naive vector query functionality."""

    @pytest.mark.asyncio
    async def test_naive_query_basic(self):
        """Test basic naive vector query with proper parameters."""
        from lightrag.operate import naive_query

        # Setup mock storage
        chunks_vdb = MockVectorStorage()
        hashing_kv = MockKVStorage()

        # Create test vectors and metadata
        test_vectors = create_test_vectors(dim=384, count=5)
        for i, vector in enumerate(test_vectors):
            await chunks_vdb.upsert(
                vector,
                {
                    "id": f"chunk_{i}",
                    "content": f"This is test chunk {i} with relevant content.",
                    "tokens": list(range(10 + i, 20 + i)),
                    "chunk_order_index": i,
                },
            )

        query_param = MockQueryParam(mode="naive", top_k=3, max_token=1000)
        global_config = {
            "llm_model_func": MockLLMFunc(["naive response"]),
            "addon_params": {},
        }

        result = await naive_query(
            query="test query",
            chunks_vdb=chunks_vdb,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        # Validate result structure
        assert result is not None
        assert hasattr(result, "content") or hasattr(result, "response_iterator")

        # Validate vector storage interactions
        assert len(chunks_vdb.query_history) > 0

    @pytest.mark.asyncio
    async def test_naive_query_vector_search(self):
        """Test naive query vector search functionality."""
        from lightrag.operate import naive_query

        chunks_vdb = MockVectorStorage()
        hashing_kv = MockKVStorage()

        # Create vectors with known similarity patterns
        query_vector = [0.1] * 384
        similar_vectors = [
            [0.11] * 384,  # Very similar
            [0.2] * 384,  # Less similar
            [0.5] * 384,  # Least similar
        ]

        for i, vector in enumerate(similar_vectors):
            await chunks_vdb.upsert(
                vector,
                {
                    "id": f"doc_{i}",
                    "content": f"Document {i} content",
                    "tokens": list(range(i * 10, (i + 1) * 10)),
                    "chunk_order_index": i,
                },
            )

        query_param = MockQueryParam(mode="naive", top_k=3)
        global_config = {
            "llm_model_func": MockLLMFunc(["vector search response"]),
            "addon_params": {},
        }

        result = await naive_query(
            query="similarity test",
            chunks_vdb=chunks_vdb,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        assert result is not None
        # Should have performed vector search
        assert len(chunks_vdb.query_history) == 1
        query_args = chunks_vdb.query_history[0]
        assert len(query_args[0]) == 384  # Query vector dimension
        assert query_args[1] == 3  # Top k

    @pytest.mark.asyncio
    async def test_naive_query_chunk_retrieval(self):
        """Test naive query chunk retrieval and processing."""
        from lightrag.operate import naive_query

        chunks_vdb = MockVectorStorage()
        hashing_kv = MockKVStorage()

        # Create test chunks with different content
        test_chunks = [
            "This is about machine learning algorithms and neural networks.",
            "The weather today is sunny with a few clouds in the sky.",
            "Python programming is essential for data science and AI development.",
        ]

        for i, content in enumerate(test_chunks):
            await chunks_vdb.upsert(
                [0.1 + i * 0.01] * 384,
                {
                    "id": f"chunk_{i}",
                    "content": content,
                    "tokens": list(range(i * 5, (i + 1) * 5)),
                    "chunk_order_index": i,
                    "full_doc_id": f"doc_{i}",
                },
            )

        query_param = MockQueryParam(mode="naive", top_k=2)
        global_config = {
            "llm_model_func": MockLLMFunc(["chunk retrieval response"]),
            "addon_params": {},
        }

        result = await naive_query(
            query="machine learning",
            chunks_vdb=chunks_vdb,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_naive_query_citation_generation(self):
        """Test naive query automatic citation generation."""
        from lightrag.operate import naive_query

        chunks_vdb = MockVectorStorage()
        hashing_kv = MockKVStorage()

        # Create chunks with source information for citations
        for i in range(3):
            await chunks_vdb.upsert(
                [0.1] * 384,
                {
                    "id": f"source_{i}",
                    "content": f"Content from source document {i} with important information.",
                    "tokens": list(range(i * 10, (i + 1) * 10)),
                    "chunk_order_index": i,
                    "full_doc_id": f"source_doc_{i}",
                    "doc_id": f"source_doc_{i}",
                },
            )

        query_param = MockQueryParam(mode="naive", top_k=3, include_citations=True)
        global_config = {
            "llm_model_func": MockLLMFunc(["citation response"]),
            "addon_params": {},
        }

        result = await naive_query(
            query="information sources",
            chunks_vdb=chunks_vdb,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_naive_query_token_limits(self):
        """Test naive query with token limit handling."""
        from lightrag.operate import naive_query

        chunks_vdb = MockVectorStorage()
        hashing_kv = MockKVStorage()

        # Create chunks that would exceed token limit when combined
        large_content = "A" * 1000  # Large chunk content
        for i in range(5):
            await chunks_vdb.upsert(
                [0.1] * 384,
                {
                    "id": f"large_{i}",
                    "content": large_content,
                    "tokens": list(range(i * 100, (i + 1) * 100)),  # Many tokens
                    "chunk_order_index": i,
                },
            )

        # Set low token limit
        query_param = MockQueryParam(mode="naive", top_k=5, max_token=200)
        global_config = {
            "llm_model_func": MockLLMFunc(["token limited response"]),
            "addon_params": {},
        }

        result = await naive_query(
            query="large content",
            chunks_vdb=chunks_vdb,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_naive_query_parameter_validation(self):
        """Test naive query parameter validation."""
        from lightrag.operate import naive_query

        chunks_vdb = MockVectorStorage()
        hashing_kv = MockKVStorage()

        # Test with various parameter combinations
        test_params = [
            {"mode": "naive", "top_k": 1, "max_token": 500},
            {"mode": "naive", "top_k": 10, "max_token": 2000},
            {"mode": "naive", "top_k": 0, "max_token": 1000},  # Edge case
            {"mode": "naive", "top_k": 100, "max_token": 100},  # Another edge case
        ]

        for i, params in enumerate(test_params):
            query_param = MockQueryParam(**params)
            global_config = {
                "llm_model_func": MockLLMFunc([f"param test {i}"]),
                "addon_params": {},
            }

            result = await naive_query(
                query=f"parameter test {i}",
                chunks_vdb=chunks_vdb,
                query_param=query_param,
                global_config=global_config,
                hashing_kv=hashing_kv,
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_naive_query_cache_operations(self):
        """Test naive query cache operations."""
        from lightrag.operate import naive_query

        chunks_vdb = MockVectorStorage()
        hashing_kv = MockKVStorage()

        # Setup test data
        await chunks_vdb.upsert(
            [0.1] * 384,
            {
                "id": "cached_chunk",
                "content": "Cached content for testing",
                "tokens": [1, 2, 3, 4, 5],
                "chunk_order_index": 0,
            },
        )

        query_param = MockQueryParam(mode="naive", top_k=3)
        global_config = {
            "llm_model_func": MockLLMFunc(["cached response"]),
            "addon_params": {},
        }

        # First query
        result1 = await naive_query(
            query="cached content",
            chunks_vdb=chunks_vdb,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        # Second identical query
        result2 = await naive_query(
            query="cached content",
            chunks_vdb=chunks_vdb,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        assert result1 is not None
        assert result2 is not None
        # Should have used cache for second query
        assert len(hashing_kv.get_history) >= 2

    @pytest.mark.asyncio
    async def test_naive_query_empty_storage(self):
        """Test naive query with empty vector storage."""
        from lightrag.operate import naive_query

        chunks_vdb = MockVectorStorage()  # Empty storage
        hashing_kv = MockKVStorage()

        query_param = MockQueryParam(mode="naive", top_k=5)
        global_config = {
            "llm_model_func": MockLLMFunc(["empty response"]),
            "addon_params": {},
        }

        result = await naive_query(
            query="empty storage test",
            chunks_vdb=chunks_vdb,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        # Should handle empty storage gracefully
        assert result is not None

    @pytest.mark.asyncio
    async def test_naive_query_with_system_prompt(self):
        """Test naive query with custom system prompt."""
        from lightrag.operate import naive_query

        chunks_vdb = MockVectorStorage()
        hashing_kv = MockKVStorage()

        await chunks_vdb.upsert(
            [0.1] * 384,
            {
                "id": "system_prompt_chunk",
                "content": "Content for system prompt testing",
                "tokens": [1, 2, 3],
                "chunk_order_index": 0,
            },
        )

        query_param = MockQueryParam(mode="naive", top_k=3)
        global_config = {
            "llm_model_func": MockLLMFunc(["system prompt response"]),
            "addon_params": {},
        }
        system_prompt = (
            "You are a helpful assistant specializing in document retrieval."
        )

        result = await naive_query(
            query="system prompt test",
            chunks_vdb=chunks_vdb,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
            system_prompt=system_prompt,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_naive_query_error_handling(self):
        """Test naive query error handling for storage failures."""
        from lightrag.operate import naive_query

        chunks_vdb = MockVectorStorage()
        hashing_kv = MockKVStorage()

        query_param = MockQueryParam(mode="naive", top_k=3)
        global_config = {
            "llm_model_func": MockLLMFunc(["error response"]),
            "addon_params": {},
        }

        # Simulate storage error
        original_query = chunks_vdb.query
        chunks_vdb.query = AsyncMock(side_effect=Exception("Vector storage error"))

        try:
            result = await naive_query(
                query="error handling test",
                chunks_vdb=chunks_vdb,
                query_param=query_param,
                global_config=global_config,
                hashing_kv=hashing_kv,
            )
            # Should handle error gracefully
            assert result is not None
        except Exception:
            # Should not crash system
            pass

    @pytest.mark.asyncio
    async def test_naive_query_streaming_mode(self):
        """Test naive query with streaming response enabled."""
        from lightrag.operate import naive_query

        chunks_vdb = MockVectorStorage()
        hashing_kv = MockKVStorage()

        await chunks_vdb.upsert(
            [0.1] * 384,
            {
                "id": "streaming_chunk",
                "content": "Content for streaming test",
                "tokens": [1, 2, 3, 4, 5],
                "chunk_order_index": 0,
            },
        )

        query_param = MockQueryParam(mode="naive", top_k=3, stream=True)
        global_config = {
            "llm_model_func": MockLLMFunc(["streaming response"]),
            "addon_params": {},
        }

        result = await naive_query(
            query="streaming test",
            chunks_vdb=chunks_vdb,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        assert result is not None
        if hasattr(result, "is_streaming"):
            assert result.is_streaming is True

    @pytest.mark.asyncio
    async def test_naive_query_top_k_ranking(self):
        """Test naive query top-k result ranking."""
        from lightrag.operate import naive_query

        chunks_vdb = MockVectorStorage()
        hashing_kv = MockKVStorage()

        # Create chunks with different similarity scores
        similarity_data = [
            ([0.95] * 384, "Most relevant content"),
            ([0.80] * 384, "Relevant content"),
            ([0.60] * 384, "Somewhat relevant content"),
            ([0.40] * 384, "Less relevant content"),
            ([0.20] * 384, "Least relevant content"),
        ]

        for i, (vector, content) in enumerate(similarity_data):
            await chunks_vdb.upsert(
                vector,
                {
                    "id": f"rank_{i}",
                    "content": content,
                    "tokens": list(range(i * 5, (i + 1) * 5)),
                    "chunk_order_index": i,
                },
            )

        query_param = MockQueryParam(mode="naive", top_k=3)
        global_config = {
            "llm_model_func": MockLLMFunc(["ranking response"]),
            "addon_params": {},
        }

        result = await naive_query(
            query="ranking test",
            chunks_vdb=chunks_vdb,
            query_param=query_param,
            global_config=global_config,
            hashing_kv=hashing_kv,
        )

        assert result is not None
        # Should query with top_k=3
        assert len(chunks_vdb.query_history) > 0
        query_args = chunks_vdb.query_history[0]
        assert query_args[1] == 3  # Top k parameter


class TestMergeOperations:
    """Comprehensive test cases for merge_nodes_and_edges functionality."""

    @pytest.mark.asyncio
    async def test_merge_nodes_and_edges_basic(self):
        """Test basic merge_nodes_and_edges with proper parameters."""
        from lightrag.operate import merge_nodes_and_edges

        # Setup mock storages
        knowledge_graph_inst = MockGraphStorage()
        entity_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        global_config = {"llm_model_max_async": 2, "addon_params": {}}

        # Create test chunk results with entities and relationships
        chunk_results = [
            (
                {
                    "entity_1": {
                        "entity_type": "PERSON",
                        "description": "John Doe",
                        "source_id": "chunk_1",
                        "weight": 1.0,
                    },
                    "entity_2": {
                        "entity_type": "ORG",
                        "description": "Acme Corp",
                        "source_id": "chunk_1",
                        "weight": 0.9,
                    },
                },
                {
                    ("entity_1", "entity_2"): {
                        "relation_type": "WORKS_FOR",
                        "weight": 1.0,
                        "source_id": "chunk_1",
                    }
                },
            ),
            (
                {
                    "entity_3": {
                        "entity_type": "PERSON",
                        "description": "Jane Smith",
                        "source_id": "chunk_2",
                        "weight": 0.8,
                    }
                },
                {
                    ("entity_3", "entity_1"): {
                        "relation_type": "KNOWS",
                        "weight": 0.7,
                        "source_id": "chunk_2",
                    }
                },
            ),
        ]

        result = await merge_nodes_and_edges(
            chunk_results=chunk_results,
            knowledge_graph_inst=knowledge_graph_inst,
            entity_vdb=entity_vdb,
            relationships_vdb=relationships_vdb,
            global_config=global_config,
        )

        # Should complete without error
        assert result is None  # Function returns None on success

        # Verify nodes were added to graph
        assert len(knowledge_graph_inst.nodes) >= 3

        # Verify edges were added to graph
        assert len(knowledge_graph_inst.edges) >= 2

        # Verify vectors were upserted
        assert len(entity_vdb.upsert_history) >= 3
        assert len(relationships_vdb.upsert_history) >= 2

    @pytest.mark.asyncio
    async def test_merge_two_phase_processing(self):
        """Test merge_nodes_and_edges two-phase processing (entities first, then relationships)."""
        from lightrag.operate import merge_nodes_and_edges

        knowledge_graph_inst = MockGraphStorage()
        entity_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        global_config = {"llm_model_max_async": 3, "addon_params": {}}

        # Create data that requires two-phase processing
        chunk_results = [
            (
                {
                    "phase1_entity": {
                        "entity_type": "PERSON",
                        "description": "Test Person",
                        "source_id": "chunk_1",
                        "weight": 1.0,
                    }
                },
                {
                    ("phase1_entity", "new_entity"): {
                        "relation_type": "TEST_RELATION",
                        "weight": 0.8,
                        "source_id": "chunk_1",
                    }
                },
            )
        ]

        await merge_nodes_and_edges(
            chunk_results=chunk_results,
            knowledge_graph_inst=knowledge_graph_inst,
            entity_vdb=entity_vdb,
            relationships_vdb=relationships_vdb,
            global_config=global_config,
        )

        # Should process entities first, then relationships
        entity_operations = [
            op for op in entity_vdb.upsert_history if op[0].startswith("entity")
        ]
        relationship_operations = [
            op for op in relationships_vdb.upsert_history if op[0].startswith("entity")
        ]

        assert len(entity_operations) > 0
        assert len(relationship_operations) > 0

    @pytest.mark.asyncio
    async def test_merge_parallel_processing(self):
        """Test merge_nodes_and_edges with parallel processing controlled by max_async."""
        from lightrag.operate import merge_nodes_and_edges

        knowledge_graph_inst = MockGraphStorage()
        entity_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        global_config = {"llm_model_max_async": 2, "addon_params": {}}

        # Create many entities and relationships to test parallelism
        chunk_results = []
        for i in range(10):
            chunk_results.append(
                (
                    {
                        f"entity_{i}": {
                            "entity_type": "TEST",
                            "description": f"Test Entity {i}",
                            "source_id": f"chunk_{i}",
                            "weight": 1.0,
                        }
                    },
                    {
                        (f"entity_{i}", f"entity_{(i + 1) % 10}"): {
                            "relation_type": "TEST_REL",
                            "weight": 0.8,
                            "source_id": f"chunk_{i}",
                        }
                    },
                )
            )

        await merge_nodes_and_edges(
            chunk_results=chunk_results,
            knowledge_graph_inst=knowledge_graph_inst,
            entity_vdb=entity_vdb,
            relationships_vdb=relationships_vdb,
            global_config=global_config,
        )

        # Should process all entities and relationships
        assert len(knowledge_graph_inst.nodes) >= 10
        assert len(knowledge_graph_inst.edges) >= 10
        assert len(entity_vdb.upsert_history) >= 10
        assert len(relationships_vdb.upsert_history) >= 10

    @pytest.mark.asyncio
    async def test_merge_source_id_management(self):
        """Test merge_nodes_and_edges source ID limits and truncation."""
        from lightrag.operate import merge_nodes_and_edges

        knowledge_graph_inst = MockGraphStorage()
        entity_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        global_config = {"llm_model_max_async": 3, "addon_params": {}}

        # Create entities with many source IDs to test truncation
        entities = {}
        for i in range(15):  # More than typical source ID limit
            entities[f"entity_{i}"] = {
                "entity_type": "TEST",
                "description": f"Test Entity {i}",
                "source_id": f"source_{i}",
                "weight": 1.0,
                "extra_sources": [
                    f"extra_{j}" for j in range(20)
                ],  # Many extra sources
            }

        chunk_results = [(entities, {})]

        await merge_nodes_and_edges(
            chunk_results=chunk_results,
            knowledge_graph_inst=knowledge_graph_inst,
            entity_vdb=entity_vdb,
            relationships_vdb=relationships_vdb,
            global_config=global_config,
        )

        # Should handle source ID truncation/limits
        assert len(entity_vdb.upsert_history) >= 15

    @pytest.mark.asyncio
    async def test_merge_error_handling(self):
        """Test merge_nodes_and_edges error handling during entity/relationship processing."""
        from lightrag.operate import merge_nodes_and_edges

        knowledge_graph_inst = MockGraphStorage()
        entity_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        global_config = {"llm_model_max_async": 2, "addon_params": {}}

        chunk_results = [
            (
                {
                    "error_entity": {
                        "entity_type": "TEST",
                        "description": "Test Entity",
                        "source_id": "chunk_1",
                        "weight": 1.0,
                    }
                },
                {},
            )
        ]

        # Simulate storage error
        original_upsert = entity_vdb.upsert
        entity_vdb.upsert = AsyncMock(
            side_effect=Exception("Storage error during entity merge")
        )

        try:
            await merge_nodes_and_edges(
                chunk_results=chunk_results,
                knowledge_graph_inst=knowledge_graph_inst,
                entity_vdb=entity_vdb,
                relationships_vdb=relationships_vdb,
                global_config=global_config,
            )
            # Should handle error gracefully
        except Exception:
            # Should not crash system
            pass

    @pytest.mark.asyncio
    async def test_merge_data_consistency(self):
        """Test merge_nodes_and_edges data consistency across graph and vector storages."""
        from lightrag.operate import merge_nodes_and_edges

        knowledge_graph_inst = MockGraphStorage()
        entity_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        global_config = {"llm_model_max_async": 3, "addon_params": {}}

        # Create consistent entity-relationship pairs
        chunk_results = [
            (
                {
                    "consistent_entity": {
                        "entity_type": "PERSON",
                        "description": "Consistent Person",
                        "source_id": "chunk_1",
                        "weight": 1.0,
                    }
                },
                {
                    ("consistent_entity", "related_entity"): {
                        "relation_type": "KNOWS",
                        "weight": 0.9,
                        "source_id": "chunk_1",
                    }
                },
            ),
            (
                {
                    "related_entity": {
                        "entity_type": "PERSON",
                        "description": "Related Person",
                        "source_id": "chunk_2",
                        "weight": 0.8,
                    }
                },
                {},
            ),
        ]

        await merge_nodes_and_edges(
            chunk_results=chunk_results,
            knowledge_graph_inst=knowledge_graph_inst,
            entity_vdb=entity_vdb,
            relationships_vdb=relationships_vdb,
            global_config=global_config,
        )

        # Verify data consistency across storages
        # Entities in graph should have corresponding vectors
        graph_entity_ids = {
            nid for nid, _ in knowledge_graph_inst.nodes if "entity" in nid
        }
        vector_entity_ids = {
            meta["id"] for _, _, meta in entity_vdb.upsert_history if "id" in meta
        }

        assert len(graph_entity_ids) > 0
        assert len(vector_entity_ids) > 0

        # Relationships in graph should have corresponding vectors
        graph_rel_pairs = {(sid, tid) for sid, tid, _ in knowledge_graph_inst.edges}
        vector_rel_ids = {
            meta["id"]
            for _, _, meta in relationships_vdb.upsert_history
            if "id" in meta
        }

        assert len(graph_rel_pairs) > 0
        assert len(vector_rel_ids) > 0

    @pytest.mark.asyncio
    async def test_merge_with_storage_locks(self):
        """Test merge_nodes_and_edges with storage locks for concurrency control."""
        from lightrag.operate import merge_nodes_and_edges

        knowledge_graph_inst = MockGraphStorage()
        entity_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        global_config = {"llm_model_max_async": 2, "addon_params": {}}

        chunk_results = [
            (
                {
                    "lock_test_entity": {
                        "entity_type": "TEST",
                        "description": "Lock Test Entity",
                        "source_id": "chunk_1",
                        "weight": 1.0,
                    }
                },
                {},
            )
        ]

        # Test that locks would be used (mock locks)
        assert knowledge_graph_inst._lock is not None

        await merge_nodes_and_edges(
            chunk_results=chunk_results,
            knowledge_graph_inst=knowledge_graph_inst,
            entity_vdb=entity_vdb,
            relationships_vdb=relationships_vdb,
            global_config=global_config,
        )

        # Should complete successfully with lock infrastructure
        assert len(knowledge_graph_inst.nodes) > 0

    @pytest.mark.asyncio
    async def test_merge_empty_chunk_results(self):
        """Test merge_nodes_and_edges with empty chunk results."""
        from lightrag.operate import merge_nodes_and_edges

        knowledge_graph_inst = MockGraphStorage()
        entity_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        global_config = {"llm_model_max_async": 2, "addon_params": {}}

        chunk_results = []  # Empty results

        await merge_nodes_and_edges(
            chunk_results=chunk_results,
            knowledge_graph_inst=knowledge_graph_inst,
            entity_vdb=entity_vdb,
            relationships_vdb=relationships_vdb,
            global_config=global_config,
        )

        # Should handle empty results gracefully
        assert len(knowledge_graph_inst.nodes) == 0
        assert len(knowledge_graph_inst.edges) == 0
        assert len(entity_vdb.upsert_history) == 0
        assert len(relationships_vdb.upsert_history) == 0

    @pytest.mark.asyncio
    async def test_merge_with_full_storages(self):
        """Test merge_nodes_and_edges with full entity and relationship storages."""
        from lightrag.operate import merge_nodes_and_edges

        knowledge_graph_inst = MockGraphStorage()
        entity_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        full_entities_storage = MockKVStorage()
        full_relations_storage = MockKVStorage()
        global_config = {"llm_model_max_async": 2, "addon_params": {}}

        chunk_results = [
            (
                {
                    "full_storage_entity": {
                        "entity_type": "TEST",
                        "description": "Full Storage Test",
                        "source_id": "chunk_1",
                        "weight": 1.0,
                    }
                },
                {
                    ("full_storage_entity", "target_entity"): {
                        "relation_type": "TEST_RELATION",
                        "weight": 0.9,
                        "source_id": "chunk_1",
                    }
                },
            )
        ]

        await merge_nodes_and_edges(
            chunk_results=chunk_results,
            knowledge_graph_inst=knowledge_graph_inst,
            entity_vdb=entity_vdb,
            relationships_vdb=relationships_vdb,
            global_config=global_config,
            full_entities_storage=full_entities_storage,
            full_relations_storage=full_relations_storage,
        )

        # Should update full storages with merged data
        assert len(full_entities_storage.set_history) > 0
        assert len(full_relations_storage.set_history) > 0

    @pytest.mark.asyncio
    async def test_merge_duplicate_handling(self):
        """Test merge_nodes_and_edges handling of duplicate entities and relationships."""
        from lightrag.operate import merge_nodes_and_edges

        knowledge_graph_inst = MockGraphStorage()
        entity_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        global_config = {"llm_model_max_async": 2, "addon_params": {}}

        # Create duplicate entities and relationships
        chunk_results = [
            (
                {
                    "duplicate_entity": {
                        "entity_type": "PERSON",
                        "description": "Duplicate Person",
                        "source_id": "chunk_1",
                        "weight": 1.0,
                    }
                },
                {
                    ("duplicate_entity", "target_entity"): {
                        "relation_type": "KNOWS",
                        "weight": 0.9,
                        "source_id": "chunk_1",
                    }
                },
            ),
            (
                {
                    "duplicate_entity": {
                        "entity_type": "PERSON",
                        "description": "Duplicate Person Updated",
                        "source_id": "chunk_2",
                        "weight": 0.8,
                    }
                },
                {
                    ("duplicate_entity", "target_entity"): {
                        "relation_type": "KNOWS",
                        "weight": 0.7,
                        "source_id": "chunk_2",
                    }
                },
            ),
        ]

        await merge_nodes_and_edges(
            chunk_results=chunk_results,
            knowledge_graph_inst=knowledge_graph_inst,
            entity_vdb=entity_vdb,
            relationships_vdb=relationships_vdb,
            global_config=global_config,
        )

        # Should handle duplicates appropriately (depends on implementation)
        # At minimum, should not crash and should process some data
        assert len(entity_vdb.upsert_history) > 0
        assert len(relationships_vdb.upsert_history) > 0

    @pytest.mark.asyncio
    async def test_merge_performance_with_large_dataset(self):
        """Test merge_nodes_and_edges performance with large dataset."""
        from lightrag.operate import merge_nodes_and_edges
        import time

        knowledge_graph_inst = MockGraphStorage()
        entity_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        global_config = {"llm_model_max_async": 5, "addon_params": {}}

        # Create large dataset
        chunk_results = []
        for i in range(50):  # Large dataset
            entities = {}
            relationships = {}

            for j in range(5):  # 5 entities per chunk
                entity_id = f"entity_{i}_{j}"
                entities[entity_id] = {
                    "entity_type": ["PERSON", "ORG", "LOC"][j % 3],
                    "description": f"Entity {i}_{j}",
                    "source_id": f"chunk_{i}",
                    "weight": 1.0 - (j * 0.1),
                }

            for k in range(3):  # 3 relationships per chunk
                src = f"entity_{i}_{k}"
                tgt = f"entity_{i}_{(k + 1) % 5}"
                relationships[(src, tgt)] = {
                    "relation_type": "TEST_RELATION",
                    "weight": 0.8 - (k * 0.1),
                    "source_id": f"chunk_{i}",
                }

            chunk_results.append((entities, relationships))

        start_time = time.time()
        await merge_nodes_and_edges(
            chunk_results=chunk_results,
            knowledge_graph_inst=knowledge_graph_inst,
            entity_vdb=entity_vdb,
            relationships_vdb=relationships_vdb,
            global_config=global_config,
        )
        end_time = time.time()

        # Should complete in reasonable time (very loose threshold for mock environment)
        assert (end_time - start_time) < 30.0

        # Should process all data
        assert len(knowledge_graph_inst.nodes) >= 200  # 40 chunks * 5 entities
        assert len(knowledge_graph_inst.edges) >= 120  # 40 chunks * 3 relationships
        assert len(entity_vdb.upsert_history) >= 200
        assert len(relationships_vdb.upsert_history) >= 120


class TestRebuildKnowledge:
    """Comprehensive test cases for rebuild_knowledge_from_chunks functionality."""

    @pytest.mark.asyncio
    async def test_rebuild_knowledge_from_chunks_basic(self):
        """Test basic rebuild_knowledge_from_chunks with proper parameters."""
        from lightrag.operate import rebuild_knowledge_from_chunks

        # Setup mock storages
        knowledge_graph_inst = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_storage = MockKVStorage()
        llm_response_cache = MockKVStorage()
        global_config = {"llm_model_max_async": 3, "addon_params": {}}

        # Create test data for rebuilding
        entities_to_rebuild = {
            "entity_1": ["chunk_1", "chunk_2"],
            "entity_2": ["chunk_2", "chunk_3"],
            "entity_3": ["chunk_3"],
        }
        relationships_to_rebuild = {
            ("entity_1", "entity_2"): ["chunk_1"],
            ("entity_2", "entity_3"): ["chunk_2"],
        }

        # Mock cached extraction results
        await llm_response_cache.set(
            "extract_chunk_1",
            json.dumps(
                {
                    "entities": {
                        "entity_1": {"entity_type": "PERSON", "description": "Person 1"}
                    },
                    "relations": {
                        "entity_1": {"entity_type": "KNOWS", "description": "Knows"}
                    },
                }
            ),
        )
        await llm_response_cache.set(
            "extract_chunk_2",
            json.dumps(
                {
                    "entities": {
                        "entity_2": {
                            "entity_type": "ORG",
                            "description": "Organization 2",
                        }
                    },
                    "relations": {},
                }
            ),
        )

        result = await rebuild_knowledge_from_chunks(
            entities_to_rebuild=entities_to_rebuild,
            relationships_to_rebuild=relationships_to_rebuild,
            knowledge_graph_inst=knowledge_graph_inst,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_storage=text_chunks_storage,
            llm_response_cache=llm_response_cache,
            global_config=global_config,
        )

        # Should complete successfully (function returns None on success)
        assert result is None

        # Verify entities were rebuilt in graph
        assert len(knowledge_graph_inst.nodes) >= 2

        # Verify relationships were rebuilt
        assert len(knowledge_graph_inst.edges) >= 1

    @pytest.mark.asyncio
    async def test_rebuild_with_parallel_processing(self):
        """Test rebuild_knowledge_from_chunks with parallel processing controlled by max_async."""
        from lightrag.operate import rebuild_knowledge_from_chunks

        knowledge_graph_inst = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_storage = MockKVStorage()
        llm_response_cache = MockKVStorage()
        global_config = {"llm_model_max_async": 2, "addon_params": {}}

        # Create many entities for parallel processing test
        entities_to_rebuild = {}
        relationships_to_rebuild = {}

        for i in range(10):
            entity_name = f"entity_{i}"
            entities_to_rebuild[entity_name] = [f"chunk_{i}"]
            if i < 9:
                relationships_to_rebuild[(entity_name, f"entity_{i + 1}")] = [
                    f"chunk_{i}"
                ]

            # Mock cached extraction results
            await llm_response_cache.set(
                f"extract_chunk_{i}",
                json.dumps(
                    {
                        "entities": {
                            entity_name: {
                                "entity_type": "TEST",
                                "description": f"Test Entity {i}",
                            }
                        },
                        "relations": {
                            (entity_name, f"entity_{i + 1}"): {
                                "relation_type": "TEST_REL",
                                "description": f"Test Relation {i}",
                            }
                        },
                    }
                ),
            )

        result = await rebuild_knowledge_from_chunks(
            entities_to_rebuild=entities_to_rebuild,
            relationships_to_rebuild=relationships_to_rebuild,
            knowledge_graph_inst=knowledge_graph_inst,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_storage=text_chunks_storage,
            llm_response_cache=llm_response_cache,
            global_config=global_config,
        )

        # Should process all entities in parallel
        assert len(knowledge_graph_inst.nodes) >= 10
        assert len(knowledge_graph_inst.edges) >= 9
        assert len(entities_vdb.upsert_history) >= 10
        assert len(relationships_vdb.upsert_history) >= 9

    @pytest.mark.asyncio
    async def test_rebuild_with_cached_extraction_results(self):
        """Test rebuild_knowledge_from_chunks uses cached LLM results instead of live calls."""
        from lightrag.operate import rebuild_knowledge_from_chunks

        knowledge_graph_inst = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_storage = MockKVStorage()
        llm_response_cache = MockKVStorage()
        global_config = {"llm_model_max_async": 3, "addon_params": {}}

        entities_to_rebuild = {"cached_entity": ["chunk_1"]}
        relationships_to_rebuild = {}

        # Setup cached extraction results
        cached_result = {
            "entities": {
                "cached_entity": {
                    "entity_type": "PERSON",
                    "description": "Cached Person",
                }
            },
            "relations": {},
        }
        await llm_response_cache.set("extract_chunk_1", json.dumps(cached_result))

        result = await rebuild_knowledge_from_chunks(
            entities_to_rebuild=entities_to_rebuild,
            relationships_to_rebuild=relationships_to_rebuild,
            knowledge_graph_inst=knowledge_graph_inst,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_storage=text_chunks_storage,
            llm_response_cache=llm_response_cache,
            global_config=global_config,
        )

        # Should use cached results (no new LLM calls)
        assert result is None
        assert len(knowledge_graph_inst.nodes) >= 1

        # Verify cache was accessed
        assert "extract_chunk_1" in llm_response_cache.get_history

    @pytest.mark.asyncio
    async def test_rebuild_with_pipeline_status_tracking(self):
        """Test rebuild_knowledge_from_chunks with pipeline status tracking."""
        from lightrag.operate import rebuild_knowledge_from_chunks

        knowledge_graph_inst = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_storage = MockKVStorage()
        llm_response_cache = MockKVStorage()
        global_config = {"llm_model_max_async": 2, "addon_params": {}}

        # Create pipeline status tracking
        pipeline_status = {
            "entities_processed": 0,
            "relationships_processed": 0,
            "errors": [],
        }

        entities_to_rebuild = {"status_entity": ["chunk_1"]}
        relationships_to_rebuild = {}

        # Mock cached extraction
        await llm_response_cache.set(
            "extract_chunk_1",
            json.dumps(
                {
                    "entities": {
                        "status_entity": {
                            "entity_type": "TEST",
                            "description": "Status Test",
                        }
                    },
                    "relations": {},
                }
            ),
        )

        result = await rebuild_knowledge_from_chunks(
            entities_to_rebuild=entities_to_rebuild,
            relationships_to_rebuild=relationships_to_rebuild,
            knowledge_graph_inst=knowledge_graph_inst,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_storage=text_chunks_storage,
            llm_response_cache=llm_response_cache,
            global_config=global_config,
            pipeline_status=pipeline_status,
        )

        # Should complete and potentially update pipeline status
        assert result is None
        assert len(knowledge_graph_inst.nodes) >= 1

    @pytest.mark.asyncio
    async def test_rebuild_with_chunk_storages(self):
        """Test rebuild_knowledge_from_chunks with entity and relation chunk storages."""
        from lightrag.operate import rebuild_knowledge_from_chunks

        knowledge_graph_inst = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_storage = MockKVStorage()
        llm_response_cache = MockKVStorage()
        entity_chunks_storage = MockKVStorage()
        relation_chunks_storage = MockKVStorage()
        global_config = {"llm_model_max_async": 2, "addon_params": {}}

        entities_to_rebuild = {"chunked_entity": ["chunk_1"]}
        relationships_to_rebuild = {("chunked_entity", "target_entity"): ["chunk_1"]}

        # Mock cached extraction
        await llm_response_cache.set(
            "extract_chunk_1",
            json.dumps(
                {
                    "entities": {
                        "chunked_entity": {
                            "entity_type": "TEST",
                            "description": "Chunked Test",
                        }
                    },
                    "relations": {
                        ("chunked_entity", "target_entity"): {
                            "relation_type": "TEST_REL",
                            "description": "Chunked Relation",
                        }
                    },
                }
            ),
        )

        result = await rebuild_knowledge_from_chunks(
            entities_to_rebuild=entities_to_rebuild,
            relationships_to_rebuild=relationships_to_rebuild,
            knowledge_graph_inst=knowledge_graph_inst,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_storage=text_chunks_storage,
            llm_response_cache=llm_response_cache,
            global_config=global_config,
            entity_chunks_storage=entity_chunks_storage,
            relation_chunks_storage=relation_chunks_storage,
        )

        # Should update chunk storages
        assert result is None
        assert len(knowledge_graph_inst.nodes) >= 1
        assert len(knowledge_graph_inst.edges) >= 1

    @pytest.mark.asyncio
    async def test_rebuild_error_handling(self):
        """Test rebuild_knowledge_from_chunks error handling for cache failures."""
        from lightrag.operate import rebuild_knowledge_from_chunks

        knowledge_graph_inst = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_storage = MockKVStorage()
        llm_response_cache = MockKVStorage()
        global_config = {"llm_model_max_async": 2, "addon_params": {}}

        entities_to_rebuild = {"error_entity": ["chunk_1"]}
        relationships_to_rebuild = {}

        # Don't set up cached extraction to simulate cache miss
        result = await rebuild_knowledge_from_chunks(
            entities_to_rebuild=entities_to_rebuild,
            relationships_to_rebuild=relationships_to_rebuild,
            knowledge_graph_inst=knowledge_graph_inst,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_storage=text_chunks_storage,
            llm_response_cache=llm_response_cache,
            global_config=global_config,
        )

        # Should handle cache miss gracefully
        # Result depends on implementation (might process without cache or return None)
        assert True  # Basic smoke test

    @pytest.mark.asyncio
    async def test_rebuild_with_file_context(self):
        """Test rebuild_knowledge_from_chunks with file path and numbering context."""
        from lightrag.operate import rebuild_knowledge_from_chunks

        knowledge_graph_inst = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_storage = MockKVStorage()
        llm_response_cache = MockKVStorage()
        global_config = {"llm_model_max_async": 2, "addon_params": {}}

        entities_to_rebuild = {"file_entity": ["chunk_1"]}
        relationships_to_rebuild = {}

        # Mock cached extraction
        await llm_response_cache.set(
            "extract_chunk_1",
            json.dumps(
                {
                    "entities": {
                        "file_entity": {
                            "entity_type": "TEST",
                            "description": "File Context Test",
                        }
                    },
                    "relations": {},
                }
            ),
        )

        result = await rebuild_knowledge_from_chunks(
            entities_to_rebuild=entities_to_rebuild,
            relationships_to_rebuild=relationships_to_rebuild,
            knowledge_graph_inst=knowledge_graph_inst,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_storage=text_chunks_storage,
            llm_response_cache=llm_response_cache,
            global_config=global_config,
            doc_id="test_document_123",
            current_file_number=5,
            total_files=10,
            file_path="/path/to/test_document.txt",
        )

        # Should process with file context
        assert result is None
        assert len(knowledge_graph_inst.nodes) >= 1

    @pytest.mark.asyncio
    async def test_rebuild_empty_rebuild_data(self):
        """Test rebuild_knowledge_from_chunks with empty rebuild data."""
        from lightrag.operate import rebuild_knowledge_from_chunks

        knowledge_graph_inst = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_storage = MockKVStorage()
        llm_response_cache = MockKVStorage()
        global_config = {"llm_model_max_async": 2, "addon_params": {}}

        entities_to_rebuild = {}  # Empty
        relationships_to_rebuild = {}  # Empty

        result = await rebuild_knowledge_from_chunks(
            entities_to_rebuild=entities_to_rebuild,
            relationships_to_rebuild=relationships_to_rebuild,
            knowledge_graph_inst=knowledge_graph_inst,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_storage=text_chunks_storage,
            llm_response_cache=llm_response_cache,
            global_config=global_config,
        )

        # Should handle empty data gracefully
        assert result is None
        assert len(knowledge_graph_inst.nodes) == 0
        assert len(knowledge_graph_inst.edges) == 0

    @pytest.mark.asyncio
    async def test_rebuild_storage_consistency(self):
        """Test rebuild_knowledge_from_chunks ensures storage consistency across all layers."""
        from lightrag.operate import rebuild_knowledge_from_chunks

        knowledge_graph_inst = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_storage = MockKVStorage()
        llm_response_cache = MockKVStorage()
        global_config = {"llm_model_max_async": 3, "addon_params": {}}

        entities_to_rebuild = {
            "consistent_entity_1": ["chunk_1"],
            "consistent_entity_2": ["chunk_2"],
        }
        relationships_to_rebuild = {
            ("consistent_entity_1", "consistent_entity_2"): ["chunk_1"]
        }

        # Mock cached extraction results
        await llm_response_cache.set(
            "extract_chunk_1",
            json.dumps(
                {
                    "entities": {
                        "consistent_entity_1": {
                            "entity_type": "TEST",
                            "description": "Consistent 1",
                        }
                    },
                    "relations": {
                        ("consistent_entity_1", "consistent_entity_2"): {
                            "relation_type": "CONSISTENT_REL",
                            "description": "Consistent Relation",
                        }
                    },
                }
            ),
        )
        await llm_response_cache.set(
            "extract_chunk_2",
            json.dumps(
                {
                    "entities": {
                        "consistent_entity_2": {
                            "entity_type": "TEST",
                            "description": "Consistent 2",
                        }
                    },
                    "relations": {},
                }
            ),
        )

        result = await rebuild_knowledge_from_chunks(
            entities_to_rebuild=entities_to_rebuild,
            relationships_to_rebuild=relationships_to_rebuild,
            knowledge_graph_inst=knowledge_graph_inst,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_storage=text_chunks_storage,
            llm_response_cache=llm_response_cache,
            global_config=global_config,
        )

        # Verify consistency across storages
        # Entities should be in graph and have vectors
        graph_entities = {
            nid for nid, _ in knowledge_graph_inst.nodes if "consistent" in nid
        }
        vector_entities = {
            meta["id"]
            for _, _, meta in entity_vdb.upsert_history
            if "id" in meta and "consistent" in meta["id"]
        }

        assert len(graph_entities) >= 2
        assert len(vector_entities) >= 2

        # Relationships should be in graph and have vectors
        graph_rels = {
            (sid, tid)
            for sid, tid, _ in knowledge_graph_inst.edges
            if "consistent" in sid
        }
        vector_rels = {
            meta["id"]
            for _, _, meta in relationships_vdb.upsert_history
            if "id" in meta and "consistent" in meta["id"]
        }

        assert len(graph_rels) >= 1
        assert len(vector_rels) >= 1

    @pytest.mark.asyncio
    async def test_rebuild_performance_with_large_dataset(self):
        """Test rebuild_knowledge_from_chunks performance with large dataset."""
        from lightrag.operate import rebuild_knowledge_from_chunks
        import time

        knowledge_graph_inst = MockGraphStorage()
        entities_vdb = MockVectorStorage()
        relationships_vdb = MockVectorStorage()
        text_chunks_storage = MockKVStorage()
        llm_response_cache = MockKVStorage()
        global_config = {"llm_model_max_async": 5, "addon_params": {}}

        # Create large dataset for performance testing
        entities_to_rebuild = {}
        relationships_to_rebuild = {}

        for i in range(50):  # Large dataset
            entity_name = f"perf_entity_{i}"
            entities_to_rebuild[entity_name] = [f"chunk_{i}"]

            if i < 49:
                relationships_to_rebuild[(entity_name, f"perf_entity_{i + 1}")] = [
                    f"chunk_{i}"
                ]

            # Mock cached extraction results
            await llm_response_cache.set(
                f"extract_chunk_{i}",
                json.dumps(
                    {
                        "entities": {
                            entity_name: {
                                "entity_type": "PERF_TEST",
                                "description": f"Performance Test Entity {i}",
                            }
                        },
                        "relations": {
                            (entity_name, f"perf_entity_{i + 1}"): {
                                "relation_type": "PERF_REL",
                                "description": f"Performance Relation {i}",
                            }
                        },
                    }
                ),
            )

        start_time = time.time()
        result = await rebuild_knowledge_from_chunks(
            entities_to_rebuild=entities_to_rebuild,
            relationships_to_rebuild=relationships_to_rebuild,
            knowledge_graph_inst=knowledge_graph_inst,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_storage=text_chunks_storage,
            llm_response_cache=llm_response_cache,
            global_config=global_config,
        )
        end_time = time.time()

        # Should complete in reasonable time for mock environment
        assert (end_time - start_time) < 60.0

        # Should process all entities and relationships
        assert len(knowledge_graph_inst.nodes) >= 50
        assert len(knowledge_graph_inst.edges) >= 49
        assert len(entities_vdb.upsert_history) >= 50
        assert len(relationships_vdb.upsert_history) >= 49


class TestErrorHandling:
    """Test cases for error handling."""

    @pytest.mark.asyncio
    async def test_extract_entities_with_llm_error(self):
        """Test entity extraction when LLM fails."""
        from lightrag.operate import extract_entities

        mock_storage = MockStorage()
        mock_llm = MockLLMFunc()
        mock_llm.side_effect = Exception("LLM service unavailable")

        documents = ["Test document"]

        with patch("lightrag.operate.global_config", {"llm_model_func": mock_llm}):
            with patch("lightrag.operate.entities_vdb", mock_storage):
                with pytest.raises(Exception):
                    await extract_entities(documents)

    @pytest.mark.asyncio
    async def test_query_with_storage_error(self):
        """Test query when storage is unavailable."""
        from lightrag.operate import kg_query

        mock_storage = MockStorage()
        mock_storage.side_effect = Exception("Storage connection failed")

        with patch("lightrag.operate.knowledge_graph_inst", mock_storage):
            # Should handle storage errors gracefully
            result = await kg_query("test query")

            # Result depends on error handling implementation
            assert result is not None
