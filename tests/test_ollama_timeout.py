
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from lightrag.llm.ollama import ollama_model_complete
from lightrag.exceptions import APITimeoutError
import httpx

@pytest.mark.asyncio
async def test_ollama_timeout_enforcement():
    """
    Test that the Ollama client correctly raises a timeout error when the
    request takes longer than the configured timeout.
    """
    # Mock parameters
    model = "test-model"
    prompt = "test prompt"
    # Set a very short timeout for the test
    test_timeout = 0.5
    
    # Create a mock for the hashing_kv global_config
    mock_hashing_kv = MagicMock()
    mock_hashing_kv.global_config = {"llm_model_name": model}

    # IMPORTANT: ollama_model_complete calls _ollama_model_if_cache
    # which instantiates ollama.AsyncClient. We need to mock ollama.AsyncClient
    # so that its chat method sleeps longer than test_timeout.

    with patch("lightrag.llm.ollama.ollama.AsyncClient") as MockAsyncClient:
        # Create a mock client instance
        mock_client_instance = MockAsyncClient.return_value
        
        # Define a chat side effect that simulates a delay
        async def delayed_chat(*args, **kwargs):
            # Sleep longer than the timeout
            await asyncio.sleep(test_timeout + 0.5) 
            return {"message": {"content": "completed"}}

        # However, the timeout in `ollama.AsyncClient` is usually handled by the
        # underlying http client (httpx). Configuring `ollama.AsyncClient` 
        # with a timeout and using a side_effect on `chat` might not trigger 
        # the *internal* http timeout logic of the *real* client if we replace 
        # the whole client with a mock.
        
        # Instead, since we want to verify that `ollama_model_complete` passes 
        # the timeout correctly and handles the exception, we can mock `chat`
        # to raise `httpx.ReadTimeout` or `APITimeoutError` directly if we 
        # want to simulate the client's behavior, OR we can try to rely on 
        # the wrapping `wait_for` logic if it exists (but looking at the code 
        # earlier, `_ollama_model_if_cache` does not wrap with `wait_for`, 
        # it passes `timeout` to `AsyncClient`).
        
        # So essentially, we are verifying that if the underlying client raises
        # a timeout, it is propagated or handled.
        
        # Let's adjust the test to simulate `httpx.ReadTimeout` which is what we saw in the logs.
        # This confirms that if the low-level client times out, the error bubbles up.
        
        mock_client_instance.chat.side_effect = httpx.ReadTimeout("Request timed out")

        # Configuration dictionary passed via kwargs (as seen in lightrag_server.py)
        kwargs = {
            "hashing_kv": mock_hashing_kv,
            "timeout": test_timeout
        }

        # We expect httpx.ReadTimeout to be raised (or wrapped)
        # In the log trace: 
        # File "/.../lightrag/llm/ollama.py", line 139, in _ollama_model_if_cache
        #     raise e
        # ...
        # httpx.ReadTimeout
        
        with pytest.raises(httpx.ReadTimeout):
            await ollama_model_complete(prompt, **kwargs)

        # Verify that AsyncClient was initialized with the correct timeout
        # Arguments to AsyncClient are (host=..., timeout=..., headers=...)
        # We need to check the call args.
        _, init_kwargs = MockAsyncClient.call_args
        assert init_kwargs.get("timeout") == test_timeout, f"Expected timeout {test_timeout}, got {init_kwargs.get('timeout')}"

@pytest.mark.asyncio
async def test_ollama_timeout_parameter_passed():
    """
    Test that the timeout parameter is correctly extracted from kwargs 
    and passed to the AsyncClient constructor.
    """
    model = "test-model"
    prompt = "test prompt"
    expected_timeout = 123  # distinct value
    
    mock_hashing_kv = MagicMock()
    mock_hashing_kv.global_config = {"llm_model_name": model}

    with patch("lightrag.llm.ollama.ollama.AsyncClient") as MockAsyncClient:
        mock_client_instance = MockAsyncClient.return_value
        mock_client_instance.chat = AsyncMock(return_value={"message": {"content": "ok"}})
        
        kwargs = {
            "hashing_kv": mock_hashing_kv,
            "timeout": expected_timeout
        }
        
        await ollama_model_complete(prompt, **kwargs)
        
        # Verification
        _, init_kwargs = MockAsyncClient.call_args
        assert init_kwargs.get("timeout") == expected_timeout, "Timeout configuration was not passed to AsyncClient"
