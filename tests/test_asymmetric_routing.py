import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_model_complete

@pytest.mark.asyncio
async def test_asymmetric_routing_logic():
    # Mock hashing_kv and global_config
    mock_hashing_kv = AsyncMock()
    mock_hashing_kv.global_config = {
        "llm_model_name": "default-model"
    }

    # Test the underlying ollama_model_complete with override
    prompt = "test prompt"
    
    # Case 1: No override
    with patch("lightrag.llm.ollama._ollama_model_if_cache", new_callable=AsyncMock) as mock_complete:
        await ollama_model_complete(prompt, hashing_kv=mock_hashing_kv)
        mock_complete.assert_called_once()
        assert mock_complete.call_args[0][0] == "default-model"

    # Case 2: With override
    with patch("lightrag.llm.ollama._ollama_model_if_cache", new_callable=AsyncMock) as mock_complete:
        await ollama_model_complete(prompt, hashing_kv=mock_hashing_kv, model="special-model")
        mock_complete.assert_called_once()
        assert mock_complete.call_args[0][0] == "special-model"

@pytest.mark.asyncio
async def test_lightrag_reflection_routing():
    # Initialize LightRAG with distinct models
    # We use a dummy function that just records what it was called with
    calls = []
    async def dummy_llm(prompt, **kwargs):
        calls.append({"prompt": prompt, "model": kwargs.get("model")})
        return "[]" # Return empty JSON list for reflection

    async def dummy_embed(texts):
        import numpy as np
        return np.zeros((len(texts), 1536))

    from lightrag.utils import EmbeddingFunc
    mock_embed = EmbeddingFunc(embedding_dim=1536, func=dummy_embed, max_token_size=8192)

    rag = LightRAG(
        working_dir="./test_rag",
        llm_model_func=dummy_llm,
        llm_model_name="extraction-model",
        reflection_llm_model_name="reflection-model",
        embedding_func=mock_embed,
        enable_ace=True
    )
    
    # Ensure initialization didn't fail
    assert rag.reflection_llm_model_name == "reflection-model"
    assert rag.llm_model_name == "extraction-model"

    # Trigger reflection
    # We need a dummy generation result
    gen_result = {"response": "Some response", "context_data": {"relationships": [], "chunks": []}}
    
    await rag.ace_reflector.reflect("test query", gen_result)
    
    # Check if the call to reflection_llm_model_func used the correct model
    # Note: reflection_llm_model_func is bound to the dummy_llm in __post_init__
    
    # Filter calls to find the reflection one
    reflection_calls = [c for c in calls if "You are the Reflector" in c["prompt"]]
    assert len(reflection_calls) > 0
    assert reflection_calls[0]["model"] == "reflection-model"

@pytest.mark.asyncio
async def test_reflection_threshold_warning():
    async def dummy_llm(prompt, **kwargs):
        return "[]"
    
    async def dummy_embed(texts):
        import numpy as np
        return np.zeros((len(texts), 1536))
    from lightrag.utils import EmbeddingFunc
    mock_embed = EmbeddingFunc(embedding_dim=1536, func=dummy_embed, max_token_size=8192)

    with patch("lightrag.utils.logger.warning") as mock_warning:
        rag = LightRAG(
            working_dir="./test_rag_warn",
            llm_model_func=dummy_llm,
            llm_model_name="qwen2.5-coder:1.5b", # This is < 7B
            enable_ace=True,
            embedding_func=mock_embed
        )
        # Check if warning was called
        warn_msgs = [call.args[0] for call in mock_warning.call_args_list]
        assert any("recommended for reliable ACE reflection" in m for m in warn_msgs)

if __name__ == "__main__":
    asyncio.run(test_asymmetric_routing_logic())
    asyncio.run(test_lightrag_reflection_routing())
    asyncio.run(test_reflection_threshold_warning())
    print("All routing tests passed!")
