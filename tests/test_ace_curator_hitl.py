import os
import shutil
from unittest.mock import AsyncMock, MagicMock

import pytest

from lightrag.ace.config import ACEConfig
from lightrag.ace.curator import ACECurator
from lightrag.ace.playbook import ContextPlaybook


@pytest.fixture
def mock_lightrag():
    rag = MagicMock()
    # Ensure directory exists for config
    if not os.path.exists("./test_ace_data"):
        os.makedirs("./test_ace_data")

    rag.ace_config = ACEConfig(
        base_dir="./test_ace_data", enable_human_in_the_loop=True
    )
    rag.adelete_relation = AsyncMock()
    rag.adelete_entity = AsyncMock()
    rag.amerge_entities = AsyncMock()
    return rag


@pytest.fixture
def ace_curator(mock_lightrag):
    # Setup
    if os.path.exists("./test_ace_data"):
        shutil.rmtree("./test_ace_data")
    os.makedirs("./test_ace_data")

    playbook = ContextPlaybook(mock_lightrag.ace_config)
    curator = ACECurator(mock_lightrag, playbook)
    yield curator

    # Cleanup
    if os.path.exists("./test_ace_data"):
        shutil.rmtree("./test_ace_data")


@pytest.mark.asyncio
async def test_hitl_flow(ace_curator, mock_lightrag):
    # 1. Submit a repair
    repairs = [
        {"action": "delete_relation", "source": "A", "target": "B"},
        {"action": "delete_entity", "name": "C"},
    ]

    await ace_curator.apply_repairs(repairs)

    # Verify NOT executed
    mock_lightrag.adelete_relation.assert_not_called()
    mock_lightrag.adelete_entity.assert_not_called()

    # Verify stored as pending
    pending = ace_curator.get_pending_repairs()
    assert len(pending) == 2
    assert pending[0]["status"] == "pending"

    # Identify which is which
    r1 = next(r for r in pending if r.get("source") == "A")
    r2 = next(r for r in pending if r.get("name") == "C")

    id_1 = r1["id"]
    id_2 = r2["id"]

    # 2. Approve first repair (delete_relation)
    await ace_curator.approve_repair(id_1)

    # Verify executed
    mock_lightrag.adelete_relation.assert_called_once()
    mock_lightrag.adelete_entity.assert_not_called()

    # Verify removed from pending
    pending = ace_curator.get_pending_repairs()
    assert len(pending) == 1
    assert pending[0]["id"] == id_2

    # 3. Reject second repair (delete_entity)
    await ace_curator.reject_repair(id_2)

    # Verify NOT executed (count should still be 0 for delete_entity)
    mock_lightrag.adelete_entity.assert_not_called()

    # Verify removed from pending
    pending = ace_curator.get_pending_repairs()
    assert len(pending) == 0


@pytest.mark.asyncio
async def test_persistence(ace_curator, mock_lightrag):
    repairs = [{"action": "delete_relation", "source": "X", "target": "Y"}]
    await ace_curator.apply_repairs(repairs)

    pending = ace_curator.get_pending_repairs()
    assert len(pending) == 1

    # Create new curator instance to simulate restart
    # We reuse the same playbook/config which points to the same directory
    new_curator = ACECurator(mock_lightrag, ace_curator.playbook)
    pending_loaded = new_curator.get_pending_repairs()

    assert len(pending_loaded) == 1
    assert pending_loaded[0]["source"] == "X"
