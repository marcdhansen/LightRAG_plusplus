import numpy as np
import pytest

from lightrag.kg.memgraph_impl import MemgraphStorage
from lightrag.kg.shared_storage import initialize_share_data
from tests.test_graph_storage import (
    test_graph_advanced as _test_graph_advanced,
)

# Import generic tests to reuse them
from tests.test_graph_storage import (
    test_graph_basic as _test_graph_basic,
)
from tests.test_graph_storage import (
    test_graph_batch_operations as _test_graph_batch_operations,
)

pytestmark = [pytest.mark.heavy, pytest.mark.integration]


# Mock embedding func matching test_graph_storage expectations
async def mock_embedding_func(texts):
    return np.random.rand(len(texts), 10)


@pytest.fixture
async def storage():
    """
    Force MemgraphStorage for these tests.
    """
    initialize_share_data()

    global_config = {
        "embedding_batch_num": 10,
        "vector_db_storage_cls_kwargs": {"cosine_better_than_threshold": 0.5},
        "working_dir": "./test_memgraph_compliance_data",
    }

    storage_instance = MemgraphStorage(
        namespace="test_graph_compliance",
        workspace="memgraph_compliance_ws",
        global_config=global_config,
        embedding_func=mock_embedding_func,
    )

    await storage_instance.initialize()
    if hasattr(storage_instance, "drop"):
        await storage_instance.drop()

    yield storage_instance

    # Cleanup
    if hasattr(storage_instance, "drop"):
        await storage_instance.drop()
    await storage_instance.finalize()


# Wrap imported tests to make them discoverable and use the local fixture
@pytest.mark.asyncio
async def test_memgraph_graph_basic(storage):
    await _test_graph_basic(storage)


@pytest.mark.asyncio
async def test_memgraph_graph_advanced(storage):
    await _test_graph_advanced(storage)


@pytest.mark.asyncio
async def test_memgraph_graph_batch_operations(storage):
    await _test_graph_batch_operations(storage)
