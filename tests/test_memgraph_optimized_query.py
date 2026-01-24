import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np
from lightrag.kg.memgraph_impl import MemgraphStorage, MemgraphVectorStorage
from lightrag.operate import _get_node_data, _get_edge_data, QueryParam

@pytest.fixture
def mock_embedding_func():
    async def _embed(texts):
        return [np.random.rand(768).astype(np.float32) for _ in texts]
    return _embed

@pytest.fixture
def mock_driver():
    driver = MagicMock()
    # Mock the session context manager
    session_ctx = MagicMock()
    session = AsyncMock()
    
    # driver.session(...) returns session_ctx
    driver.session.return_value = session_ctx
    
    # async with session_ctx returns session
    async def __aenter__():
        return session
    session_ctx.__aenter__.side_effect = __aenter__
    session_ctx.__aexit__ = AsyncMock()
    
    return driver, session

@pytest.fixture
def mock_data_init_lock():
    with patch("lightrag.kg.memgraph_impl.get_data_init_lock") as mock_lock:
        mock_lock.return_value.__aenter__.return_value = None
        yield mock_lock


@pytest.mark.asyncio
async def test_unified_neighbor_search_call(mock_driver, mock_embedding_func, mock_data_init_lock):
    driver, session = mock_driver
    
    # Mock result for session.run
    mock_result = AsyncMock()
    mock_result.fetch.return_value = []
    
    # Needs to proceed async iteration
    async def async_iter():
        yield {
            "g_node": {"entity_id": "Entity1", "prop": "val", "labels": ["Label"]},
            "degree": 5,
            "similarity": 0.9
        }
    mock_result.__aiter__.return_value = async_iter()
    
    session.run.return_value = mock_result

    # Initialize Storage
    with patch("lightrag.kg.memgraph_impl.AsyncGraphDatabase.driver", return_value=driver):
        kg = MemgraphStorage(namespace="test", global_config={}, embedding_func=mock_embedding_func)
        await kg.initialize()
        
        vdb = MemgraphVectorStorage(namespace="test", global_config={}, embedding_func=mock_embedding_func, workspace="default")
        await vdb.initialize()

    # Create QueryParam
    qp = QueryParam(mode="local", top_k=10)

    # Mock _find_most_related_edges_from_entities to avoid deeper execution
    with patch("lightrag.operate._find_most_related_edges_from_entities", new_callable=AsyncMock) as mock_find_edges:
        mock_find_edges.return_value = []
        
        # Execute _get_node_data
        await _get_node_data("test query", kg, vdb, qp)
        
        # Verify unified query was called
        # We check the arguments passed to session.run
        assert session.run.called
        call_args = session.run.call_args[0]
        query_str = call_args[0]
        
        assert "CALL vector_search.search" in query_str
        assert "MATCH (g_node:`base` {entity_id: v_node.entity_name})" in query_str
        assert "count(r) as degree" in query_str

@pytest.mark.asyncio
async def test_unified_edge_search_call(mock_driver, mock_embedding_func, mock_data_init_lock):
    driver, session = mock_driver
    
    mock_result = AsyncMock()
    async def async_iter():
        yield {
            "r": {"weight": 0.8},
            "src": {"entity_id": "Src1"},
            "tgt": {"entity_id": "Tgt1"},
            "similarity": 0.85
        }
    mock_result.__aiter__.return_value = async_iter()
    session.run.return_value = mock_result

    with patch("lightrag.kg.memgraph_impl.AsyncGraphDatabase.driver", return_value=driver):
        kg = MemgraphStorage(namespace="test", global_config={}, embedding_func=mock_embedding_func)
        await kg.initialize()
        
        vdb = MemgraphVectorStorage(namespace="test", global_config={}, embedding_func=mock_embedding_func, workspace="default")
        await vdb.initialize()

    qp = QueryParam(mode="global", top_k=10)

    with patch("lightrag.operate._find_most_related_entities_from_relationships", new_callable=AsyncMock) as mock_find_ents:
        mock_find_ents.return_value = []
        
        await _get_edge_data("test query", kg, vdb, qp)
        
        assert session.run.called
        call_args = session.run.call_args[0]
        query_str = call_args[0]
        
        assert "CALL vector_search.search" in query_str
        assert "MATCH (src:`base` {entity_id: v_node.src_id})" in query_str
