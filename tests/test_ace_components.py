import pytest

pytestmark = pytest.mark.light
from unittest.mock import MagicMock, AsyncMock

from lightrag.ace.config import ACEConfig
from lightrag.ace.playbook import ContextPlaybook
from lightrag.ace.generator import ACEGenerator
from lightrag.ace.reflector import ACEReflector
from lightrag.ace.curator import ACECurator
from lightrag.core import LightRAG

@pytest.fixture
def mock_lightrag():
    rag = MagicMock(spec=LightRAG)
    rag.aquery_data = AsyncMock()
    rag.llm_model_func = AsyncMock()
    return rag

@pytest.fixture
def temp_playbook(tmp_path):
    config = ACEConfig(base_dir=str(tmp_path))
    return ContextPlaybook(config)

def test_playbook_persistence(temp_playbook):
    # Test initial state
    assert len(temp_playbook.content.core_directives) > 0
    
    # Test add lesson
    temp_playbook.add_lesson("Test Lesson")
    assert "Test Lesson" in temp_playbook.content.lessons_learned
    
    # Test reload
    new_playbook = ContextPlaybook(temp_playbook.config)
    assert "Test Lesson" in new_playbook.content.lessons_learned

def test_playbook_render(temp_playbook):
    rendered = temp_playbook.render()
    assert "### Core Directives" in rendered
    assert "### Operational Strategies" in rendered

@pytest.mark.asyncio
async def test_generator_flow(mock_lightrag, temp_playbook):
    # Setup mocks
    mock_lightrag.aquery_data.return_value = {
        "status": "success",
        "data": {
            "entities": [{"entity_name": "TestEntity", "entity_type": "TestType", "description": "Desc"}],
            "relationships": [],
            "chunks": []
        }
    }
    mock_lightrag.llm_model_func.return_value = "Generated Answer"
    
    generator = ACEGenerator(mock_lightrag, temp_playbook)
    result = await generator.generate("Test Query")
    
    assert result["response"] == "Generated Answer"
    mock_lightrag.aquery_data.assert_called_once()
    mock_lightrag.llm_model_func.assert_called_once()
    
    # Verify playbook was injected
    call_args = mock_lightrag.llm_model_func.call_args[0][0]
    assert "### ACE Context Playbook" in call_args

@pytest.mark.asyncio
async def test_reflector_flow(mock_lightrag):
    mock_lightrag.llm_model_func.return_value = '["Lesson 1", "Lesson 2"]'
    
    reflector = ACEReflector(mock_lightrag)
    insights = await reflector.reflect("Query", {"response": "Response"})
    
    assert len(insights) == 2
    assert "Lesson 1" in insights

@pytest.mark.asyncio
async def test_curator_flow(temp_playbook):
    curator = ACECurator(temp_playbook)
    await curator.curate(["New Insight"])
    
    assert "New Insight" in temp_playbook.content.lessons_learned
