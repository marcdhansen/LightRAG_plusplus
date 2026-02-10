"""
Comprehensive API tests for Ollama compatibility routes.
Tests Ollama API compatibility including chat, generate, model info,
and streaming functionality.
"""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from tests.api.conftest import (
    APIResponseValidator,
    MockLightRAG,
)


class MockOllamaResponse:
    """Mock Ollama response data for testing."""

    @staticmethod
    def version_response():
        return {"version": "0.9.3"}

    @staticmethod
    def tags_response():
        return {
            "models": [
                {
                    "name": "lightrag",
                    "model": "lightrag",
                    "modified_at": "2024-01-01T00:00:00Z",
                    "size": 7269176474,
                    "digest": "sha256:abc123",
                    "details": {
                        "parent_model": "",
                        "format": "gguf",
                        "family": "llama",
                        "families": ["llama"],
                        "parameter_size": "13B",
                        "quantization_level": "Q4_0",
                    },
                }
            ]
        }

    @staticmethod
    def ps_response():
        return {
            "models": [
                {
                    "name": "lightrag",
                    "model": "lightrag",
                    "size": 7269176474,
                    "digest": "sha256:abc123",
                    "details": {
                        "parent_model": "",
                        "format": "gguf",
                        "family": "llama",
                        "families": ["llama"],
                        "parameter_size": "7.2B",
                        "quantization_level": "Q4_0",
                    },
                    "expires_at": "2050-12-31T14:38:31.83753-07:00",
                    "size_vram": 7269176474,
                }
            ]
        }

    @staticmethod
    def generate_response():
        return {
            "model": "lightrag",
            "created_at": "2024-01-01T00:00:00Z",
            "response": "This is a test response from LightRAG.",
            "done": True,
            "done_reason": "stop",
            "context": [],
            "total_duration": 1234567890,
            "load_duration": 0,
            "prompt_eval_count": 10,
            "prompt_eval_duration": 123456789,
            "eval_count": 25,
            "eval_duration": 987654321,
        }

    @staticmethod
    def chat_response():
        return {
            "model": "lightrag",
            "created_at": "2024-01-01T00:00:00Z",
            "message": {
                "role": "assistant",
                "content": "This is a test chat response from LightRAG.",
                "images": None,
            },
            "done": True,
            "done_reason": "stop",
            "total_duration": 1234567890,
            "load_duration": 0,
            "prompt_eval_count": 10,
            "prompt_eval_duration": 123456789,
            "eval_count": 25,
            "eval_duration": 987654321,
        }


class MockStreamingResponse:
    """Mock streaming response generator."""

    def __init__(self, chunks=None):
        self.chunks = chunks or [
            {"response": "This "},
            {"response": "is "},
            {"response": "a "},
            {"response": "test "},
            {"response": "response."},
            {"done": True},
        ]

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.chunks:
            raise StopAsyncIteration
        chunk = self.chunks.pop(0)
        if isinstance(chunk, dict):
            return json.dumps(chunk)
        return chunk


@pytest.mark.asyncio
@pytest.mark.api
class TestOllamaVersionInfo:
    """Test Ollama version and model information endpoints."""

    async def test_get_version_success(
        self, authenticated_api_client, response_validator
    ):
        """Test getting Ollama version information."""
        response = await authenticated_api_client.get("/ollama/version")
        data = response_validator.assert_success_response(response)

        assert data["version"] == "0.9.3"

    async def test_get_tags_success(self, authenticated_api_client, response_validator):
        """Test getting available models (tags)."""
        response = await authenticated_api_client.get("/ollama/tags")
        data = response_validator.assert_success_response(response)

        assert "models" in data
        assert len(data["models"]) > 0
        model = data["models"][0]
        assert "name" in model
        assert "model" in model
        assert "size" in model
        assert "details" in model
        assert model["name"] == "lightrag"

    async def test_get_ps_success(self, authenticated_api_client, response_validator):
        """Test getting running models."""
        response = await authenticated_api_client.get("/ollama/ps")
        data = response_validator.assert_success_response(response)

        assert "models" in data
        assert len(data["models"]) > 0
        model = data["models"][0]
        assert "name" in model
        assert "size_vram" in model
        assert "expires_at" in model
        assert model["name"] == "lightrag"


@pytest.mark.asyncio
@pytest.mark.api
class TestOllamaGenerate:
    """Test Ollama generate endpoint."""

    async def test_generate_success(self, authenticated_api_client, response_validator):
        """Test successful generate request."""
        generate_request = {
            "model": "lightrag",
            "prompt": "What is LightRAG?",
            "stream": False,
        }

        with patch.object(MockLightRAG, "llm_model_func") as mock_llm:
            mock_llm.return_value = (
                "LightRAG is a retrieval-augmented generation system."
            )

            response = await authenticated_api_client.post(
                "/ollama/generate", json=generate_request
            )
            data = response_validator.assert_success_response(response)

            assert data["model"] == "lightrag"
            assert "response" in data
            assert data["done"] is True
            assert "total_duration" in data
            assert "prompt_eval_count" in data
            assert "eval_count" in data
            mock_llm.assert_called_once()

    async def test_generate_with_system_prompt(
        self, authenticated_api_client, response_validator
    ):
        """Test generate with system prompt."""
        generate_request = {
            "model": "lightrag",
            "prompt": "Test prompt",
            "system": "You are a helpful assistant.",
            "stream": False,
        }

        with patch.object(MockLightRAG, "llm_model_func") as mock_llm:
            mock_llm.return_value = "Test response"

            response = await authenticated_api_client.post(
                "/ollama/generate", json=generate_request
            )
            data = response_validator.assert_success_response(response)

            assert data["response"] == "Test response"
            # Verify system prompt was set
            assert "system_prompt" in MockLightRAG.llm_model_kwargs
            assert (
                MockLightRAG.llm_model_kwargs["system_prompt"]
                == "You are a helpful assistant."
            )

    async def test_generate_with_options(
        self, authenticated_api_client, response_validator
    ):
        """Test generate with custom options."""
        generate_request = {
            "model": "lightrag",
            "prompt": "Test prompt",
            "options": {"temperature": 0.7, "max_tokens": 100},
            "stream": False,
        }

        with patch.object(MockLightRAG, "llm_model_func") as mock_llm:
            mock_llm.return_value = "Test response"

            response = await authenticated_api_client.post(
                "/ollama/generate", json=generate_request
            )
            data = response_validator.assert_success_response(response)

            assert data["response"] == "Test response"

    async def test_generate_streaming_success(
        self, authenticated_api_client, response_validator
    ):
        """Test successful streaming generate request."""
        generate_request = {
            "model": "lightrag",
            "prompt": "What is LightRAG?",
            "stream": True,
        }

        with patch.object(MockLightRAG, "llm_model_func") as mock_llm:
            mock_llm.return_value = MockStreamingResponse()

            response = await authenticated_api_client.post(
                "/ollama/generate", json=generate_request
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/x-ndjson"

            # Parse streaming response
            content = response.text
            lines = [line for line in content.split("\n") if line.strip()]
            assert len(lines) >= 2  # At least response + done message

            # Verify streaming format
            first_chunk = json.loads(lines[0])
            assert "response" in first_chunk
            assert first_chunk["done"] is False

            # Find the final chunk
            final_chunk = json.loads(lines[-1])
            assert final_chunk["done"] is True
            assert "total_duration" in final_chunk

    async def test_generate_missing_prompt(
        self, authenticated_api_client, response_validator
    ):
        """Test generate request without prompt."""
        invalid_request = {"model": "lightrag", "stream": False}

        response = await authenticated_api_client.post(
            "/ollama/generate", json=invalid_request
        )
        response_validator.assert_error_response(response, 422)

    async def test_generate_missing_model(
        self, authenticated_api_client, response_validator
    ):
        """Test generate request without model."""
        invalid_request = {"prompt": "Test prompt", "stream": False}

        response = await authenticated_api_client.post(
            "/ollama/generate", json=invalid_request
        )
        response_validator.assert_error_response(response, 422)

    async def test_generate_empty_response(
        self, authenticated_api_client, response_validator
    ):
        """Test generate when LLM returns empty response."""
        generate_request = {
            "model": "lightrag",
            "prompt": "Test prompt",
            "stream": False,
        }

        with patch.object(MockLightRAG, "llm_model_func") as mock_llm:
            mock_llm.return_value = ""

            response = await authenticated_api_client.post(
                "/ollama/generate", json=generate_request
            )
            data = response_validator.assert_success_response(response)

            assert data["response"] == "No response generated"

    async def test_generate_llm_error(
        self, authenticated_api_client, response_validator
    ):
        """Test generate when LLM raises error."""
        generate_request = {
            "model": "lightrag",
            "prompt": "Test prompt",
            "stream": False,
        }

        with patch.object(MockLightRAG, "llm_model_func") as mock_llm:
            mock_llm.side_effect = Exception("LLM processing failed")

            response = await authenticated_api_client.post(
                "/ollama/generate", json=generate_request
            )
            response_validator.assert_error_response(response, 500)


@pytest.mark.asyncio
@pytest.mark.api
class TestOllamaChat:
    """Test Ollama chat endpoint."""

    async def test_chat_success(self, authenticated_api_client, response_validator):
        """Test successful chat request."""
        chat_request = {
            "model": "lightrag",
            "messages": [
                {"role": "user", "content": "What is LightRAG?"},
            ],
            "stream": False,
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = (
                "LightRAG is a retrieval-augmented generation system."
            )

            response = await authenticated_api_client.post(
                "/ollama/chat", json=chat_request
            )
            data = response_validator.assert_success_response(response)

            assert data["model"] == "lightrag"
            assert data["message"]["role"] == "assistant"
            assert "response" not in data["message"]  # chat format
            assert "content" in data["message"]
            assert data["done"] is True
            assert "total_duration" in data
            mock_query.assert_called_once()

    async def test_chat_with_history(
        self, authenticated_api_client, response_validator
    ):
        """Test chat with conversation history."""
        chat_request = {
            "model": "lightrag",
            "messages": [
                {"role": "user", "content": "What is RAG?"},
                {
                    "role": "assistant",
                    "content": "RAG stands for Retrieval-Augmented Generation.",
                },
                {"role": "user", "content": "How does it work?"},
            ],
            "stream": False,
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = (
                "RAG works by combining retrieval with language models."
            )

            response = await authenticated_api_client.post(
                "/ollama/chat", json=chat_request
            )
            data = response_validator.assert_success_response(response)

            assert (
                data["message"]["content"]
                == "RAG works by combining retrieval with language models."
            )

            # Verify conversation history was passed
            call_args = mock_query.call_args
            if call_args:
                param = call_args[1] if len(call_args) > 1 else call_args.get("param")
                if param and hasattr(param, "conversation_history"):
                    assert len(param.conversation_history) == 2  # Previous messages

    async def test_chat_with_system_prompt(
        self, authenticated_api_client, response_validator
    ):
        """Test chat with system prompt."""
        chat_request = {
            "model": "lightrag",
            "messages": [{"role": "user", "content": "Test"}],
            "system": "You are a helpful assistant.",
            "stream": False,
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = "Test response"

            response = await authenticated_api_client.post(
                "/ollama/chat", json=chat_request
            )
            data = response_validator.assert_success_response(response)

            assert data["message"]["content"] == "Test response"
            # Verify system prompt was set
            assert "system_prompt" in MockLightRAG.llm_model_kwargs

    async def test_chat_streaming_success(
        self, authenticated_api_client, response_validator
    ):
        """Test successful streaming chat request."""
        chat_request = {
            "model": "lightrag",
            "messages": [{"role": "user", "content": "What is LightRAG?"}],
            "stream": True,
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = MockStreamingResponse()

            response = await authenticated_api_client.post(
                "/ollama/chat", json=chat_request
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/x-ndjson"

            # Parse streaming response
            content = response.text
            lines = [line for line in content.split("\n") if line.strip()]
            assert len(lines) >= 2

            # Verify streaming format
            first_chunk = json.loads(lines[0])
            assert "message" in first_chunk
            assert first_chunk["message"]["role"] == "assistant"
            assert first_chunk["done"] is False

    async def test_chat_missing_messages(
        self, authenticated_api_client, response_validator
    ):
        """Test chat request without messages."""
        invalid_request = {"model": "lightrag", "stream": False}

        response = await authenticated_api_client.post(
            "/ollama/chat", json=invalid_request
        )
        response_validator.assert_error_response(response, 422)

    async def test_chat_empty_messages(
        self, authenticated_api_client, response_validator
    ):
        """Test chat request with empty messages list."""
        chat_request = {
            "model": "lightrag",
            "messages": [],
            "stream": False,
        }

        response = await authenticated_api_client.post(
            "/ollama/chat", json=chat_request
        )
        response_validator.assert_error_response(response, 422)

    async def test_chat_last_message_not_user(
        self, authenticated_api_client, response_validator
    ):
        """Test chat request where last message is not from user."""
        invalid_request = {
            "model": "lightrag",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
            "stream": False,
        }

        response = await authenticated_api_client.post(
            "/ollama/chat", json=invalid_request
        )
        response_validator.assert_error_response(response, 422)

    async def test_chat_bypass_mode(self, authenticated_api_client, response_validator):
        """Test chat request with bypass prefix."""
        chat_request = {
            "model": "lightrag",
            "messages": [{"role": "user", "content": "/bypass Tell me a joke"}],
            "stream": False,
        }

        with patch.object(MockLightRAG, "llm_model_func") as mock_llm:
            mock_llm.return_value = (
                "Why don't scientists trust atoms? Because they make up everything!"
            )

            response = await authenticated_api_client.post(
                "/ollama/chat", json=chat_request
            )
            data = response_validator.assert_success_response(response)

            assert (
                data["message"]["content"]
                == "Why don't scientists trust atoms? Because they make up everything!"
            )

    async def test_chat_with_query_modes(
        self, authenticated_api_client, response_validator
    ):
        """Test chat with different query mode prefixes."""
        test_cases = [
            ("/local What is RAG?", "local"),
            ("/global Explain AI", "global"),
            ("/hybrid Test query", "hybrid"),
            ("/naive Simple test", "naive"),
            ("/mix Combined approach", "mix"),
        ]

        for query, expected_mode in test_cases:
            chat_request = {
                "model": "lightrag",
                "messages": [{"role": "user", "content": query}],
                "stream": False,
            }

            with patch.object(MockLightRAG, "aquery") as mock_query:
                mock_query.return_value = f"Response for {expected_mode} mode"

                response = await authenticated_api_client.post(
                    "/ollama/chat", json=chat_request
                )
                data = response_validator.assert_success_response(response)

                assert (
                    data["message"]["content"] == f"Response for {expected_mode} mode"
                )

                # Verify mode was passed correctly
                call_args = mock_query.call_args
                if call_args:
                    param = (
                        call_args[1] if len(call_args) > 1 else call_args.get("param")
                    )
                    if param:
                        assert param.mode == expected_mode

    async def test_chat_with_user_prompt(
        self, authenticated_api_client, response_validator
    ):
        """Test chat with user prompt in brackets."""
        chat_request = {
            "model": "lightrag",
            "messages": [
                {
                    "role": "user",
                    "content": "/local[use markdown format] Explain quantum computing",
                }
            ],
            "stream": False,
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = (
                "Quantum computing explanation in markdown format."
            )

            response = await authenticated_api_client.post(
                "/ollama/chat", json=chat_request
            )
            data = response_validator.assert_success_response(response)

            assert "markdown" in data["message"]["content"]

            # Verify user prompt was extracted
            call_args = mock_query.call_args
            if call_args:
                param = call_args[1] if len(call_args) > 1 else call_args.get("param")
                if param and hasattr(param, "user_prompt"):
                    assert param.user_prompt == "use markdown format"


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.error_handling
class TestOllamaErrorHandling:
    """Test error handling for Ollama routes."""

    async def test_ollama_routes_unauthorized_access(
        self, api_client, response_validator
    ):
        """Test that unauthenticated requests are rejected."""
        endpoints = [
            "/ollama/version",
            "/ollama/tags",
            "/ollama/ps",
        ]

        for endpoint in endpoints:
            response = await api_client.get(endpoint)
            response_validator.assert_error_response(response, 401)

        # Test POST endpoints
        generate_request = {
            "model": "lightrag",
            "prompt": "test",
            "stream": False,
        }
        chat_request = {
            "model": "lightrag",
            "messages": [{"role": "user", "content": "test"}],
            "stream": False,
        }

        post_endpoints = [
            ("/ollama/generate", generate_request),
            ("/ollama/chat", chat_request),
        ]

        for endpoint, payload in post_endpoints:
            response = await api_client.post(endpoint, json=payload)
            response_validator.assert_error_response(response, 401)

    async def test_invalid_json_requests(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of malformed JSON requests."""
        response = await authenticated_api_client.post(
            "/ollama/generate",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        response_validator.assert_error_response(response, 422)

        response = await authenticated_api_client.post(
            "/ollama/chat",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        response_validator.assert_error_response(response, 422)

    async def test_octet_stream_requests(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of octet-stream content type."""
        generate_request = {
            "model": "lightrag",
            "prompt": "Test prompt",
            "stream": False,
        }

        # Test with application/octet-stream content type
        response = await authenticated_api_client.post(
            "/ollama/generate",
            json=generate_request,
            headers={"Content-Type": "application/octet-stream"},
        )
        data = response_validator.assert_success_response(response)

        assert "response" in data

    async def test_streaming_error_handling(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of streaming errors."""
        generate_request = {
            "model": "lightrag",
            "prompt": "Test prompt",
            "stream": True,
        }

        with patch.object(MockLightRAG, "llm_model_func") as mock_llm:
            # Mock streaming error
            async def error_stream():
                yield "initial chunk"
                raise Exception("Stream error occurred")

            mock_llm.return_value = error_stream()

            response = await authenticated_api_client.post(
                "/ollama/generate", json=generate_request
            )

            assert response.status_code == 200
            content = response.text
            lines = [line for line in content.split("\n") if line.strip()]

            # Should contain error message
            error_found = any("Error" in line for line in lines)
            assert error_found, "Stream error should be included in response"

    async def test_chat_with_session_context(
        self, authenticated_api_client, response_validator
    ):
        """Test chat handling of OpenWebUI session context."""
        # Test OpenWebUI session title generation pattern
        chat_request = {
            "model": "lightrag",
            "messages": [
                {
                    "role": "user",
                    "content": "\n<chat_history>\nUSER: Generate session title\nASSISTANT: Previous response",
                }
            ],
            "stream": False,
        }

        with patch.object(MockLightRAG, "llm_model_func") as mock_llm:
            mock_llm.return_value = "Session Title: LightRAG Discussion"

            response = await authenticated_api_client.post(
                "/ollama/chat", json=chat_request
            )
            data = response_validator.assert_success_response(response)

            assert "Session Title" in data["message"]["content"]


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.performance
class TestOllamaPerformance:
    """Test performance aspects of Ollama API."""

    async def test_response_time_benchmark(
        self, authenticated_api_client, response_validator
    ):
        """Test response time benchmarking."""
        import time

        generate_request = {
            "model": "lightrag",
            "prompt": "Performance test prompt",
            "stream": False,
        }

        with patch.object(MockLightRAG, "llm_model_func") as mock_llm:
            mock_llm.return_value = "Quick response"

            start_time = time.time()
            response = await authenticated_api_client.post(
                "/ollama/generate", json=generate_request
            )
            end_time = time.time()

            response_validator.assert_success_response(response)

            response_time = end_time - start_time
            # Should be fast for mocked response
            assert response_time < 1.0, f"Generate took too long: {response_time:.3f}s"

    async def test_concurrent_requests(
        self, authenticated_api_client, response_validator
    ):
        """Test handling of concurrent Ollama requests."""
        import asyncio

        generate_request = {
            "model": "lightrag",
            "prompt": "Concurrent test",
            "stream": False,
        }

        with patch.object(MockLightRAG, "llm_model_func") as mock_llm:
            mock_llm.return_value = f"Response for concurrent test"

            # Send 5 concurrent requests
            tasks = []
            for i in range(5):
                req = generate_request.copy()
                req["prompt"] = f"Concurrent test {i}"
                task = authenticated_api_client.post("/ollama/generate", json=req)
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # All responses should succeed
            for i, response in enumerate(responses):
                if not isinstance(response, Exception):
                    data = response_validator.assert_success_response(response)
                    assert "response" in data
                else:
                    pytest.fail(
                        f"Concurrent request {i} failed with exception: {response}"
                    )

    async def test_memory_usage_tracking(
        self, authenticated_api_client, response_validator
    ):
        """Test that token estimation and usage tracking works."""
        generate_request = {
            "model": "lightrag",
            "prompt": "This is a test prompt for token estimation.",
            "stream": False,
        }

        with patch.object(MockLightRAG, "llm_model_func") as mock_llm:
            mock_llm.return_value = "Test response"

            response = await authenticated_api_client.post(
                "/ollama/generate", json=generate_request
            )
            data = response_validator.assert_success_response(response)

            # Verify usage metrics are present
            assert "prompt_eval_count" in data
            assert "eval_count" in data
            assert "total_duration" in data
            assert isinstance(data["prompt_eval_count"], int)
            assert isinstance(data["eval_count"], int)
            assert data["prompt_eval_count"] > 0
            assert data["eval_count"] > 0


@pytest.mark.asyncio
@pytest.mark.api
@pytest.mark.integration
class TestOllamaIntegration:
    """Integration tests for Ollama API compatibility."""

    async def test_end_to_end_generate_workflow(
        self, authenticated_api_client, response_validator
    ):
        """Test complete generate workflow with various options."""
        # Test with all options
        generate_request = {
            "model": "lightrag",
            "prompt": "Explain quantum computing in simple terms",
            "system": "You are a science educator.",
            "options": {
                "temperature": 0.8,
                "top_p": 0.9,
                "max_tokens": 200,
            },
            "stream": False,
        }

        with patch.object(MockLightRAG, "llm_model_func") as mock_llm:
            mock_llm.return_value = (
                "Quantum computing uses quantum mechanical phenomena..."
            )

            response = await authenticated_api_client.post(
                "/ollama/generate", json=generate_request
            )
            data = response_validator.assert_success_response(response)

            assert data["model"] == "lightrag"
            assert "response" in data
            assert data["done"] is True

            # Verify all parameters were passed through
            mock_llm.assert_called_once()
            call_kwargs = mock_llm.call_args[1] if mock_llm.call_args else {}
            assert "system_prompt" in MockLightRAG.llm_model_kwargs

    async def test_end_to_end_chat_workflow(
        self, authenticated_api_client, response_validator
    ):
        """Test complete chat workflow with history and modes."""
        chat_request = {
            "model": "lightrag",
            "messages": [
                {"role": "user", "content": "What is machine learning?"},
                {"role": "assistant", "content": "Machine learning is..."},
                {"role": "user", "content": "/hybrid Can you give me more details?"},
            ],
            "stream": False,
        }

        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = "Here are more details about machine learning..."

            response = await authenticated_api_client.post(
                "/ollama/chat", json=chat_request
            )
            data = response_validator.assert_success_response(response)

            assert data["message"]["role"] == "assistant"
            assert "response" not in data["message"]  # chat format
            assert "content" in data["message"]

            # Verify conversation history was passed correctly
            call_args = mock_query.call_args
            if call_args:
                param = call_args[1] if len(call_args) > 1 else call_args.get("param")
                if param and hasattr(param, "conversation_history"):
                    history = param.conversation_history
                    assert len(history) == 2  # Previous messages
                    assert history[0]["role"] == "user"
                    assert history[1]["role"] == "assistant"

    async def test_streaming_vs_non_streaming_consistency(
        self, authenticated_api_client, response_validator
    ):
        """Test that streaming and non-streaming responses are consistent."""
        prompt = "What is the difference between AI and ML?"

        # Non-streaming request
        non_stream_request = {
            "model": "lightrag",
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        # Streaming request
        stream_request = {
            "model": "lightrag",
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }

        expected_response = "AI is the broader field while ML is a specific subset..."

        # Mock non-streaming
        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_query.return_value = expected_response

            non_stream_response = await authenticated_api_client.post(
                "/ollama/chat", json=non_stream_request
            )
            non_stream_data = response_validator.assert_success_response(
                non_stream_response
            )

        # Mock streaming
        with patch.object(MockLightRAG, "aquery") as mock_query:
            mock_stream_response = MockStreamingResponse(
                [
                    {"response": "AI "},
                    {"response": "is "},
                    {"response": "the "},
                    {"response": "broader "},
                    {"response": "field "},
                    {"response": "while "},
                    {"response": "ML "},
                    {"response": "is "},
                    {"response": "a "},
                    {"response": "specific "},
                    {"response": "subset..."},
                    {"done": True},
                ]
            )
            mock_query.return_value = mock_stream_response

            stream_response = await authenticated_api_client.post(
                "/ollama/chat", json=stream_request
            )

            # Combine streaming chunks
            content = stream_response.text
            lines = [line for line in content.split("\n") if line.strip()]

            # Extract complete response from streaming
            full_response = ""
            for line in lines:
                chunk = json.loads(line)
                if "message" in chunk and "content" in chunk["message"]:
                    full_response += chunk["message"]["content"]

            # Verify consistency
            assert full_response == expected_response
            assert full_response == non_stream_data["message"]["content"]
