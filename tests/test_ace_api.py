import os
import shutil
from unittest.mock import patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from lightrag import LightRAG
from lightrag.api.config import initialize_config, parse_args
from lightrag.api.lightrag_server import create_app
from lightrag.utils import EmbeddingFunc

TEST_DIR = "test_ace_api_storage"


def get_mock_args():
    # Start with default args
    args = parse_args()
    args.working_dir = os.path.abspath(TEST_DIR)
    args.input_dir = os.path.abspath(TEST_DIR)
    args.llm_binding = "openai"
    args.llm_model = "mock-model"
    args.embedding_binding = "openai"
    args.embedding_model = "mock-embed"
    args.embedding_dim = 768
    args.enable_ace = True
    return args


async def mock_llm_complete(prompt, system_prompt=None, **kwargs):
    if "high_level_keywords" in str(prompt):
        return '{"high_level_keywords": ["test"], "low_level_keywords": ["test"]}'
    if "Context Playbook" in str(prompt) or (
        system_prompt and "Context Playbook" in str(system_prompt)
    ):
        return "This is an ACE API response."
    if "ACE Framework" in str(prompt) and "JSON" in str(prompt):
        return '["API Insight"]'
    return "Mocked response"


async def mock_embed(texts):
    return np.array([[0.1] * 768 for _ in texts])


@pytest.fixture
def client():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR)

    with patch("sys.argv", ["test_ace_api.py"]):
        args = get_mock_args()
        initialize_config(args, force=True)

    # Create the real LightRAG instance we want to use
    test_rag = LightRAG(
        working_dir=TEST_DIR,
        enable_ace=True,
        llm_model_func=mock_llm_complete,
        embedding_func=EmbeddingFunc(
            embedding_dim=768, max_token_size=8192, func=mock_embed
        ),
    )

    # Patch the LightRAG class in lightrag_server to return our instance
    with patch("lightrag.api.lightrag_server.LightRAG", return_value=test_rag):
        app = create_app(args)

        with TestClient(app) as c:
            yield c

    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)


def test_ace_query_endpoint(client):
    # 1. Insert some data first (using existing /documents/upload or similar,
    # but for simplicity we'll just check if the endpoint exists and responds)
    """Test the /ace/query endpoint by inserting data through the API and then querying."""
    # Insert document through API to avoid event loop conflicts
    upload_response = client.post(
        "/documents/text",
        json={
            "text": "ACE Framework enables agentic context evolution.",
            "file_source": "test_doc",
        },
    )
    assert upload_response.status_code == 200

    # Wait a moment for background processing if necessary
    # (though with mock LLM it should be fast)

    response = client.post("/ace/query", json={"query": "What are we testing?"})

    if response.status_code != 200:
        print(f"Response body: {response.text}")

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "trajectory" in data
    assert "playbook_used" in data
    assert isinstance(data["trajectory"], list)
    assert isinstance(data["playbook_used"], dict)
    # Check for insights which indicate reflection happened
    assert "insights" in data
    assert len(data["insights"]) > 0


def test_ace_query_not_enabled(client):
    import lightrag.api.lightrag_server as server

    # Ensure we are modifying the same object the router has
    server.rag.enable_ace = False

    try:
        response = client.post("/ace/query", json={"query": "Should fail"})
        if response.status_code != 501:
            print(f"Response body: {response.text}")
        assert response.status_code == 501
        assert "not enabled" in response.json()["detail"]
    finally:
        # Restore for other tests if any
        server.rag.enable_ace = True
