import pytest
import httpx
import asyncio
from lightrag.api.lightrag_server import create_app
from lightrag.api.config import global_args

@pytest.fixture
def api_client():
    """Create a test client for the FastAPI app."""
    # Note: We don't need a full RAG instance for the highlight endpoint
    # as it's independent of the graph storage.
    app = create_app(global_args)
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")

@pytest.mark.integration
@pytest.mark.heavy
@pytest.mark.asyncio
async def test_api_highlight_endpoint(api_client):
    """Test the /highlight endpoint via the API."""
    payload = {
        "query": "What is the capital of France?",
        "context": "Paris is the capital of France. Berlin is the capital of Germany.",
        "threshold": 0.5
    }
    
    async with api_client as client:
        response = await client.post("/highlight", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "highlighted_sentences" in data
    assert len(data["highlighted_sentences"]) > 0
    assert any("Paris" in s for s in data["highlighted_sentences"])

@pytest.mark.integration
@pytest.mark.heavy
@pytest.mark.asyncio
async def test_api_highlight_no_match(api_client):
    """Test the /highlight endpoint with no matches."""
    payload = {
        "query": "What is the capital of France?",
        "context": "Berlin is the capital of Germany.",
        "threshold": 0.9
    }
    
    async with api_client as client:
        response = await client.post("/highlight", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["highlighted_sentences"]) == 0
