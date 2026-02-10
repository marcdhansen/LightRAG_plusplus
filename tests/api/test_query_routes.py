"""
Comprehensive API tests for query routes.
Tests all query modes, streaming, parameters validation, and error handling.
"""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from lightrag.base import QueryParam
from tests.api.conftest import (
    APIResponseValidator,
    MockLightRAG,
)


class MockQueryResponse:
    """Mock query response data for testing."""

    @staticmethod
    def basic_response():
        return {
            "response": "This is a test response about LightRAG functionality.",
            "references": [
                {
                    "reference_id": "doc_1",
                    "file_path": "test_document.txt",
                    "content": ["LightRAG is a retrieval-augmented generation system."],
                    "score": 0.95,
                    "metadata": {"type": "text", "source": "test_document.txt"},
                }
            ],
        }

    @staticmethod
    def streaming_chunks():
        return [
            {"response": "LightRAG is"},
            {"response": " a retrieval-augmented"},
            {"response": " generation system."},
            {
                "references": [
                    {
                        "reference_id": "doc_1",
                        "file_path": "test_document.txt",
                        "content": ["LightRAG documentation"],
                        "score": 0.92,
                        "metadata": {"type": "text"},
                    }
                ]
            },
        ]

    @staticmethod
    def context_only_response():
        return {
            "context": {
                "entities": ["LightRAG", "RAG"],
                "relationships": ["LightRAG-enhances->RAG"],
                "chunks": ["LightRAG implements retrieval-augmented generation."],
            }
        }

    @staticmethod
    def prompt_only_response():
        return {
            "prompt": "Based on the following context, answer the user query...\n\nContext: LightRAG is a RAG system."
        }


@pytest.mark.asyncio
@pytest.mark.api
class TestQueryEndpoints:
    """Test basic query endpoints."""

    async def test_query_basic_success(
        self, authenticated_api_client, response_validator
    ):
        """Test basic successful query."""
        query_data = {"query": "What is LightRAG?", "mode": "mix"}

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = MockQueryResponse.basic_response()

            response = await authenticated_api_client.post("/query", json=query_data)
            data = response_validator.assert_success_response(response)

            assert "response" in data
            assert "references" in data
            assert len(data["references"]) > 0
            assert (
                data["response"]
                == "This is a test response about LightRAG functionality."
            )

    async def test_query_streaming_success(
        self, authenticated_api_client, response_validator
    ):
        """Test streaming query response."""
        query_data = {"query": "What is LightRAG?", "mode": "mix", "stream": True}

        with patch.object(MockLightRAG, "aquery_stream") as mock_query_stream:
            mock_query_stream.return_value = MockQueryResponse.streaming_chunks()

            response = await authenticated_api_client.post(
                "/query/stream", json=query_data
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/x-ndjson"

            # Parse streaming response
            content = response.text
            lines = [line for line in content.split("\n") if line.strip()]

            assert len(lines) >= 2  # At least response + references

            # First chunk should contain part of response
            first_chunk = json.loads(lines[0])
            assert "response" in first_chunk

            # Last chunk should contain references
            last_chunk = json.loads(lines[-1])
            assert "references" in last_chunk

    async def test_query_with_all_parameters(
        self, authenticated_api_client, response_validator
    ):
        """Test query with all optional parameters."""
        query_data = {
            "query": "What are the benefits of LightRAG?",
            "mode": "hybrid",
            "only_need_context": False,
            "only_need_prompt": False,
            "response_type": "Multiple Paragraphs",
            "top_k": 10,
            "chunk_top_k": 5,
            "max_entity_tokens": 1000,
            "max_relation_tokens": 500,
            "max_total_tokens": 2000,
            "hl_keywords": ["LightRAG", "benefits"],
            "ll_keywords": ["retrieval", "generation"],
            "conversation_history": [
                {"role": "user", "content": "Previous question"},
                {"role": "assistant", "content": "Previous answer"},
            ],
            "user_prompt": "Custom prompt template",
            "enable_rerank": True,
            "rerank_entities": True,
            "rerank_relationships": False,
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = MockQueryResponse.basic_response()

            response = await authenticated_api_client.post("/query", json=query_data)
            data = response_validator.assert_success_response(response)

            assert "response" in data
            assert "references" in data

            # Verify mock was called with correct parameters
            mock_query.assert_called_once()
            call_args = mock_query.call_args[1]

            param = call_args.get("param") or QueryParam()
            assert param.mode == "hybrid"
            assert param.top_k == 10
            assert param.chunk_top_k == 5
            assert param.max_entity_tokens == 1000
            assert param.enable_rerank == True

    async def test_query_context_only(
        self, authenticated_api_client, response_validator
    ):
        """Test query with only context needed."""
        query_data = {
            "query": "What entities are related to LightRAG?",
            "mode": "local",
            "only_need_context": True,
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = MockQueryResponse.context_only_response()

            response = await authenticated_api_client.post("/query", json=query_data)
            data = response_validator.assert_success_response(response)

            assert "response" not in data
            assert "context" in data
            assert "entities" in data["context"]
            assert "relationships" in data["context"]

    async def test_query_prompt_only(
        self, authenticated_api_client, response_validator
    ):
        """Test query with only prompt needed."""
        query_data = {
            "query": "Generate a prompt about LightRAG",
            "mode": "naive",
            "only_need_prompt": True,
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = MockQueryResponse.prompt_only_response()

            response = await authenticated_api_client.post("/query", json=query_data)
            data = response_validator.assert_success_response(response)

            assert "response" not in data
            assert "prompt" in data
            assert len(data["prompt"]) > 0

    @pytest.mark.parametrize(
        "mode", ["local", "global", "hybrid", "naive", "mix", "bypass"]
    )
    async def test_query_all_modes(
        self, authenticated_api_client, response_validator, mode
    ):
        """Test all query modes."""
        query_data = {"query": f"Test query for {mode} mode", "mode": mode}

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = MockQueryResponse.basic_response()

            response = await authenticated_api_client.post("/query", json=query_data)
            data = response_validator.assert_success_response(response)

            assert "response" in data
            mock_query.assert_called_once()

            # Verify mode was passed correctly
            call_args = mock_query.call_args[1]
            param = call_args.get("param") or QueryParam()
            assert param.mode == mode


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.validation
class TestQueryParameterValidation:
    """Test parameter validation for query endpoints."""

    async def test_query_missing_required_fields(
        self, authenticated_api_client, response_validator
    ):
        """Test validation of missing required fields."""
        # Missing query
        invalid_data = {"mode": "mix"}

        response = await authenticated_api_client.post("/query", json=invalid_data)
        response_validator.assert_error_response(response, 422)

        # Missing mode (should default to "mix")
        valid_data = {"query": "Test query"}
        response = await authenticated_api_client.post("/query", json=valid_data)
        data = response_validator.assert_success_response(response)
        assert "response" in data

    async def test_query_invalid_query_length(
        self, authenticated_api_client, response_validator
    ):
        """Test validation of query length."""
        # Query too short
        invalid_data = {"query": "x", "mode": "mix"}

        response = await authenticated_api_client.post("/query", json=invalid_data)
        response_validator.assert_error_response(response, 422)

        # Query extremely long (should either succeed or fail with validation error)
        long_query = "x" * 10000
        long_data = {"query": long_query, "mode": "mix"}

        response = await authenticated_api_client.post("/query", json=long_data)
        # Implementation dependent - may succeed or fail
        assert response.status_code in [200, 422]

    async def test_query_invalid_mode(
        self, authenticated_api_client, response_validator
    ):
        """Test validation of query mode."""
        invalid_data = {"query": "Test query", "mode": "invalid_mode"}

        response = await authenticated_api_client.post("/query", json=invalid_data)
        response_validator.assert_error_response(response, 422)

    async def test_query_invalid_numeric_parameters(
        self, authenticated_api_client, response_validator
    ):
        """Test validation of numeric parameters."""
        # Negative top_k
        invalid_data = {"query": "Test query", "top_k": -1}

        response = await authenticated_api_client.post("/query", json=invalid_data)
        response_validator.assert_error_response(response, 422)

        # Zero top_k
        invalid_data = {"query": "Test query", "top_k": 0}

        response = await authenticated_api_client.post("/query", json=invalid_data)
        response_validator.assert_error_response(response, 422)

        # Excessive max_tokens
        invalid_data = {"query": "Test query", "max_total_tokens": 1000000}

        response = await authenticated_api_client.post("/query", json=invalid_data)
        # May succeed or fail depending on limits
        assert response.status_code in [200, 422]

    async def test_query_invalid_response_type(
        self, authenticated_api_client, response_validator
    ):
        """Test validation of response_type parameter."""
        invalid_data = {
            "query": "Test query",
            "response_type": "",  # Empty response type
        }

        response = await authenticated_api_client.post("/query", json=invalid_data)
        response_validator.assert_error_response(response, 422)

    async def test_query_invalid_conversation_history(
        self, authenticated_api_client, response_validator
    ):
        """Test validation of conversation history."""
        # Invalid role in conversation history
        invalid_data = {
            "query": "Test query",
            "conversation_history": [
                {"role": "invalid_role", "content": "Invalid message"}
            ],
        }

        response = await authenticated_api_client.post("/query", json=invalid_data)
        # May succeed or fail depending on validation
        assert response.status_code in [200, 422]


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.error_handling
class TestQueryErrorHandling:
    """Test error handling for query endpoints."""

    async def test_query_with_malformed_json(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of malformed JSON."""
        response = await authenticated_api_client.post(
            "/query",
            content="invalid json request",
            headers={"Content-Type": "application/json"},
        )
        response_validator.assert_error_response(response, 422)

    async def test_query_llm_error(self, authenticated_api_client, response_validator):
        """Test handling of LLM processing errors."""
        query_data = {"query": "What is LightRAG?", "mode": "mix"}

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.side_effect = Exception("LLM processing failed")

            response = await authenticated_api_client.post("/query", json=query_data)
            response_validator.assert_error_response(response, 500)

    async def test_query_timeout_handling(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of query timeouts."""
        query_data = {"query": "What is LightRAG?", "mode": "mix"}

        with patch.object(MockLightRAG, "aquery") as mock_query:
            import asyncio

            mock_query.side_effect = asyncio.TimeoutError("Query timeout")

            response = await authenticated_api_client.post("/query", json=query_data)
            response_validator.assert_error_response(response, 504)

    async def test_query_empty_response(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of empty response from RAG."""
        query_data = {"query": "Empty query test", "mode": "naive"}

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = {"response": "", "references": []}

            response = await authenticated_api_client.post("/query", json=query_data)
            data = response_validator.assert_success_response(response)

            assert data["response"] == ""
            assert len(data["references"]) == 0

    async def test_query_streaming_error(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of streaming errors."""
        query_data = {"query": "What is LightRAG?", "mode": "mix"}

        with patch.object(MockLightRAG, "aquery_stream") as mock_query_stream:
            mock_query_stream.side_effect = Exception("Streaming error")

            response = await authenticated_api_client.post(
                "/query/stream", json=query_data
            )
            response_validator.assert_error_response(response, 500)


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.performance
class TestQueryPerformance:
    """Test performance-related aspects of query endpoints."""

    async def test_query_response_time(
        self, authenticated_api_client, response_validator
    ):
        """Test query response time benchmarking."""
        import time

        query_data = {"query": "Performance test query", "mode": "mix"}

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = MockQueryResponse.basic_response()

            start_time = time.time()
            response = await authenticated_api_client.post("/query", json=query_data)
            end_time = time.time()

            response_validator.assert_success_response(response)

            response_time = end_time - start_time
            # Should be fast for mocked response
            assert response_time < 1.0, f"Query took too long: {response_time:.3f}s"

    async def test_concurrent_queries(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of concurrent queries."""
        import asyncio

        query_data = {"query": "Concurrent test query", "mode": "mix"}

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = MockQueryResponse.basic_response()

            # Send 10 concurrent queries
            tasks = []
            for i in range(10):
                data = query_data.copy()
                data["query"] = f"Concurrent test query {i}"
                task = authenticated_api_client.post("/query", json=data)
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # All responses should succeed
            for response in responses:
                if not isinstance(response, Exception):
                    data = response_validator.assert_success_response(response)
                    assert "response" in data
                else:
                    pytest.fail(f"Concurrent query failed with exception: {response}")

    async def test_large_context_handling(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of large context queries."""
        # Create a query that would generate large context
        large_keywords = ["keyword" + str(i) for i in range(100)]

        query_data = {
            "query": "Large context test",
            "mode": "local",
            "hl_keywords": large_keywords,
            "ll_keywords": large_keywords[:50],
            "top_k": 50,
            "max_total_tokens": 10000,
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = MockQueryResponse.basic_response()

            response = await authenticated_api_client.post("/query", json=query_data)
            data = response_validator.assert_success_response(response)

            assert "response" in data

            # Verify parameters were passed correctly
            call_args = mock_query.call_args[1]
            param = call_args.get("param") or QueryParam()
            assert len(param.hl_keywords) == 100
            assert len(param.ll_keywords) == 50


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.authentication
class TestQueryAuthentication:
    """Test authentication for query endpoints."""

    async def test_unauthorized_query_access(self, api_client, response_validator):
        """Test that unauthenticated queries are rejected."""
        query_data = {"query": "Test query", "mode": "mix"}

        response = await api_client.post("/query", json=query_data)
        response_validator.assert_error_response(response, 401)

        response = await api_client.post("/query/stream", json=query_data)
        response_validator.assert_error_response(response, 401)

    async def test_invalid_token_query(self, api_client, response_validator):
        """Test that invalid tokens are rejected for queries."""
        api_client.headers.update({"Authorization": "Bearer invalid_token"})

        query_data = {"query": "Test query", "mode": "mix"}
        response = await api_client.post("/query", json=query_data)
        response_validator.assert_error_response(response, 401)

    async def test_expired_token_query(self, api_client, response_validator):
        """Test handling of expired tokens."""
        # Mock expired token
        api_client.headers.update({"Authorization": "Bearer expired_token_12345"})

        query_data = {"query": "Test query", "mode": "mix"}
        response = await api_client.post("/query", json=query_data)
        # Should be rejected by auth middleware
        response_validator.assert_error_response(response, 401)


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.integration
class TestQueryIntegration:
    """Integration tests for query endpoints."""

    async def test_query_with_citations(
        self, authenticated_api_client, response_validator
    ):
        """Test query response with proper citation formatting."""
        query_data = {"query": "What is LightRAG?", "mode": "hybrid"}

        mock_response = {
            "response": "LightRAG is a retrieval-augmented generation system [1].",
            "references": [
                {
                    "reference_id": "doc_1",
                    "file_path": "lightrag_overview.txt",
                    "content": [
                        "LightRAG implements advanced retrieval-augmented generation capabilities."
                    ],
                    "score": 0.95,
                    "metadata": {"title": "LightRAG Overview", "page": 1},
                }
            ],
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = mock_response

            response = await authenticated_api_client.post("/query", json=query_data)
            data = response_validator.assert_success_response(response)

            assert "[1]" in data["response"]
            assert len(data["references"]) == 1
            assert data["references"][0]["reference_id"] == "doc_1"

    async def test_query_with_conversation_history(
        self, authenticated_api_client, response_validator
    ):
        """Test query with conversation history context."""
        query_data = {
            "query": "Can you elaborate on that?",
            "mode": "mix",
            "conversation_history": [
                {"role": "user", "content": "What is LightRAG?"},
                {
                    "role": "assistant",
                    "content": "LightRAG is a retrieval-augmented generation system.",
                },
            ],
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_response = MockQueryResponse.basic_response()
            mock_response["response"] = (
                "LightRAG combines information retrieval with language models to provide accurate, context-aware responses."
            )
            mock_query.return_value = mock_response

            response = await authenticated_api_client.post("/query", json=query_data)
            data = response_validator.assert_success_response(response)

            assert "elaborate" in data["response"]

            # Verify conversation history was passed
            call_args = mock_query.call_args[1]
            conv_history = call_args.get("conversation_history", [])
            assert len(conv_history) == 2

    async def test_query_keyword_filtering(
        self, authenticated_api_client, response_validator
    ):
        """Test query with high/low level keyword filtering."""
        query_data = {
            "query": "Information about machine learning",
            "mode": "local",
            "hl_keywords": ["machine learning", "AI"],
            "ll_keywords": ["neural networks", "algorithms", "training"],
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = MockQueryResponse.basic_response()

            response = await authenticated_api_client.post("/query", json=query_data)
            data = response_validator.assert_success_response(response)

            # Verify keywords were passed correctly
            call_args = mock_query.call_args[1]
            param = call_args.get("param") or QueryParam()
            assert "machine learning" in param.hl_keywords
            assert "AI" in param.hl_keywords
            assert "neural networks" in param.ll_keywords

    async def test_query_streaming_vs_non_streaming_consistency(
        self, authenticated_api_client, response_validator
    ):
        """Test that streaming and non-streaming responses are consistent."""
        query_data = {"query": "What is LightRAG?", "mode": "mix"}

        mock_response = MockQueryResponse.basic_response()

        # Test non-streaming
        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = mock_response

            response = await authenticated_api_client.post("/query", json=query_data)
            non_streaming_data = response_validator.assert_success_response(response)

        # Test streaming
        with patch.object(MockLightRAG, "aquery_stream") as mock_query_stream:
            # Simulate streaming response that produces same final result
            chunks = [
                {"response": "LightRAG is"},
                {"response": " a retrieval-augmented"},
                {"response": " generation system."},
                {"references": mock_response["references"]},
            ]
            mock_query_stream.return_value = chunks

            stream_response = await authenticated_api_client.post(
                "/query/stream", json={**query_data, "stream": True}
            )

            # Combine streaming chunks
            content = stream_response.text
            lines = [line for line in content.split("\n") if line.strip()]

            # Extract final response and references from streaming
            full_response = ""
            final_references = []
            for line in lines:
                chunk = json.loads(line)
                if "response" in chunk:
                    full_response += chunk["response"]
                if "references" in chunk:
                    final_references = chunk["references"]

            # Verify consistency
            assert full_response == non_streaming_data["response"]
            assert final_references == non_streaming_data["references"]


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.edge_cases
class TestQueryEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_query_with_unicode_content(
        self, authenticated_api_client, response_validator
    ):
        """Test query with unicode characters."""
        query_data = {
            "query": "什么是LightRAG？🚀 Unicode test: café, naïve, résumé",
            "mode": "mix",
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_response = MockQueryResponse.basic_response()
            mock_response["response"] = "LightRAG支持多语言查询和Unicode字符。"
            mock_query.return_value = mock_response

            response = await authenticated_api_client.post("/query", json=query_data)
            data = response_validator.assert_success_response(response)

            # Verify unicode content is handled correctly
            assert "多语言" in data["response"]
            assert "Unicode" in query_data["query"]

    async def test_query_with_special_characters(
        self, authenticated_api_client, response_validator
    ):
        """Test query with special characters and markdown."""
        query_data = {
            "query": "Explain `function()` in **JavaScript** with <code>examples</code>",
            "mode": "naive",
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_response = MockQueryResponse.basic_response()
            mock_response["response"] = (
                "In JavaScript, `function()` declares a function. **Examples**: `function test() { return true; }`"
            )
            mock_query.return_value = mock_response

            response = await authenticated_api_client.post("/query", json=query_data)
            data = response_validator.assert_success_response(response)

            assert "function()" in data["response"]

    async def test_query_with_empty_optional_arrays(
        self, authenticated_api_client, response_validator
    ):
        """Test query with empty array parameters."""
        query_data = {
            "query": "Test query with empty arrays",
            "mode": "local",
            "hl_keywords": [],
            "ll_keywords": [],
            "conversation_history": [],
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = MockQueryResponse.basic_response()

            response = await authenticated_api_client.post("/query", json=query_data)
            data = response_validator.assert_success_response(response)

            # Verify empty arrays were handled
            call_args = mock_query.call_args[1]
            param = call_args.get("param") or QueryParam()
            assert param.hl_keywords == []
            assert param.ll_keywords == []
            assert param.conversation_history == []

    async def test_query_minimal_parameters(
        self, authenticated_api_client, response_validator
    ):
        """Test query with minimal required parameters only."""
        query_data = {"query": "Minimal test query"}  # mode should default to "mix"

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = MockQueryResponse.basic_response()

            response = await authenticated_api_client.post("/query", json=query_data)
            data = response_validator.assert_success_response(response)

            assert "response" in data
            assert "references" in data

            # Verify default parameters were applied
            call_args = mock_query.call_args[1]
            param = call_args.get("param") or QueryParam()
            assert param.mode == "mix"  # Default mode
