import json
import logging
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock

# Add project root to path
sys.path.append(".")

from lightrag.ace.curator import ACECurator
from lightrag.ace.reflector import ACEReflector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestACEReflector(unittest.IsolatedAsyncioTestCase):
    async def test_reflect_graph_issues_identifies_hallucination(self):
        """
        Test that reflect_graph_issues correctly identifies a hallucinated relationship
        and suggests a 'delete_relation' repair action.
        """
        # Mock LightRAG instance
        rag_mock = MagicMock()

        # Mock LLM response to simulate Reflector logic
        # The Reflector sends a prompt asking to verify relations.
        # We simulate the LLM responding with a delete_relation JSON.
        expected_repair = [
            {
                "action": "delete_relation",
                "source": "Beekeeper",
                "target": "Mars",
                "reason": "Not supported by source text.",
            }
        ]
        # Use reflection_llm_model_func as ACEReflector now uses asymmetric routing
        rag_mock.reflection_llm_model_func = AsyncMock(
            return_value=json.dumps(expected_repair)
        )
        rag_mock.reflection_llm_model_name = "test-reflection-model"

        reflector = ACEReflector(rag_mock)

        # Mock query context data
        query = "Do beekeepers go to Mars?"
        generation_result = {
            "response": "Beekeepers do not go to Mars usually.",
            "context_data": {
                "chunks": [{"content": "Beekeepers keep bees."}],
                "relationships": [
                    {
                        "src_id": "Beekeeper",
                        "tgt_id": "Mars",
                        "description": "Beekeepers fly to Mars on weekends.",
                    }
                ],
                "entities": [],
            },
        }

        # Run reflection
        repairs = await reflector.reflect_graph_issues(query, generation_result)

        # Verify
        self.assertEqual(len(repairs), 1)
        self.assertEqual(repairs[0]["action"], "delete_relation")
        self.assertEqual(repairs[0]["source"], "Beekeeper")
        self.assertEqual(repairs[0]["target"], "Mars")

        logger.info(
            "TestACEReflector passed: Correctly identified hallucinated relation."
        )


class TestACECurator(unittest.IsolatedAsyncioTestCase):
    async def test_apply_repairs_valid_delete_relation(self):
        """
        Test that apply_repairs successfully calls adelete_relation on the RAG instance
        when processing a 'delete_relation' repair action.
        """
        # Mock LightRAG instance and playbook
        rag_mock = MagicMock()
        rag_mock.adelete_relation = (
            AsyncMock()
        )  # This is the key method we expect to be called

        playbook_mock = MagicMock()

        curator = ACECurator(rag_mock, playbook_mock)

        # Define repair action
        repairs = [
            {"action": "delete_relation", "source": "Beekeeper", "target": "Mars"}
        ]

        # Apply repairs
        await curator.apply_repairs(repairs)

        # Verify adelete_relation was called with correct args
        rag_mock.adelete_relation.assert_called_once_with("Beekeeper", "Mars")
        logger.info("TestACECurator passed: Correctly called adelete_relation.")

    async def test_apply_repairs_valid_delete_entity(self):
        """
        Test that apply_repairs successfully calls adelete_entity on the RAG instance
        when processing a 'delete_entity' repair action.
        """
        # Mock LightRAG instance and playbook
        rag_mock = MagicMock()
        rag_mock.adelete_entity = (
            AsyncMock()
        )  # This is the key method we expect to be called

        playbook_mock = MagicMock()

        curator = ACECurator(rag_mock, playbook_mock)

        # Define repair action
        repairs = [{"action": "delete_entity", "name": "Unicorn"}]

        # Apply repairs
        await curator.apply_repairs(repairs)

        # Verify adelete_entity was called with correct args
        rag_mock.adelete_entity.assert_called_once_with("Unicorn")
        logger.info("TestACECurator passed: Correctly called adelete_entity.")


if __name__ == "__main__":
    unittest.main()
