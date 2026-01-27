import pytest
import numpy as np
from lightrag.core import LightRAG, EmbeddingFunc

# Dummy embedding function
async def dummy_embed(texts, **kwargs):
    return np.random.rand(len(texts), 384)

# Dummy LLM function
async def dummy_llm_func(prompt, **kwargs):
    return "Dummy response"

@pytest.fixture
def dummy_embedding_func():
    return EmbeddingFunc(embedding_dim=384, max_token_size=8192, func=dummy_embed)

def test_ace_policy_raises_error_for_small_model(dummy_embedding_func):
    """
    Test that LightRAG raises ValueError when enable_ace is True 
    and reflection model is small (<7B), without override.
    """
    try:
        LightRAG(
            working_dir="./test_ace_policy_temp",
            enable_ace=True,
            reflection_llm_model_name="qwen2.5-coder:1.5b",
            llm_model_name="gpt-4o-mini",
            embedding_func=dummy_embedding_func,
            llm_model_func=dummy_llm_func
        )
        pytest.fail("Should have raised ValueError due to small model size")
    except ValueError as e:
        assert "Reasoning Threshold Violation" in str(e)
        assert "has 1.5B parameters" in str(e)

def test_ace_policy_override_works(dummy_embedding_func):
    """
    Test that LightRAG allows small model when override is set.
    """
    rag = LightRAG(
        working_dir="./test_ace_policy_temp_override",
        enable_ace=True,
        reflection_llm_model_name="qwen2.5-coder:1.5b",
        ace_allow_small_reflector=True,
        embedding_func=dummy_embedding_func,
        llm_model_func=dummy_llm_func
    )
    assert rag.ace_allow_small_reflector is True
    # Should reach here without error

def test_ace_policy_passes_for_large_model(dummy_embedding_func):
    """
    Test that LightRAG allows large model without override.
    """
    rag = LightRAG(
        working_dir="./test_ace_policy_temp_large",
        enable_ace=True,
        reflection_llm_model_name="qwen2.5-coder:32b",
        embedding_func=dummy_embedding_func,
        llm_model_func=dummy_llm_func
    )
    # Should reach here without error

def test_ace_policy_passes_if_ace_disabled(dummy_embedding_func):
    """
    Test that policy is ignored if ACE is disabled.
    """
    rag = LightRAG(
        working_dir="./test_ace_policy_temp_disabled",
        enable_ace=False,
        reflection_llm_model_name="qwen2.5-coder:1.5b",
        embedding_func=dummy_embedding_func,
        llm_model_func=dummy_llm_func
    )
    # Should reach here without error
