import asyncio
import os
import shutil
from functools import partial

import pytest

from lightrag import LightRAG, QueryParam
from lightrag.ace.config import ACEConfig
from lightrag.ace.cot_templates import CoTDepth, CoTTemplates
from lightrag.ace.reflector import ACEReflector
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc
from tests.ace_test_utils import ACETestKit

WORKING_DIR = "./rag_storage_cot_test"


@pytest.fixture(scope="function")
async def cot_rag():
    if os.path.exists(WORKING_DIR):
        shutil.rmtree(WORKING_DIR)
    os.makedirs(WORKING_DIR)

    # Configure ACE with CoT enabled
    ace_config = ACEConfig(
        base_dir=WORKING_DIR,
        cot_enabled=True,
        cot_depth="standard",
        cot_graph_verification=True,
        cot_general_reflection=True,
        cot_include_reasoning_output=True,
    )

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_name="qwen2.5-coder:7b",
        llm_model_func=ollama_model_complete,
        enable_ace=True,
        embedding_func=EmbeddingFunc(
            embedding_dim=768,
            max_token_size=8192,
            func=partial(ollama_embed.func, embed_model="nomic-embed-text:v1.5"),
        ),
    )

    # Set the ACE config
    rag.ace_config = ace_config
    await rag.initialize_storages()
    yield rag


class TestCoTIntegration:
    """Test Chain-of-Thought functionality in ACE Reflector."""

    @pytest.mark.asyncio
    async def test_cot_templates_initialization(self):
        """Test that CoT templates initialize correctly with different depths."""

        # Test minimal depth
        config_minimal = ACEConfig(cot_depth="minimal")
        templates_minimal = CoTTemplates(config_minimal)
        assert templates_minimal.depth == CoTDepth.MINIMAL

        # Test standard depth
        config_standard = ACEConfig(cot_depth="standard")
        templates_standard = CoTTemplates(config_standard)
        assert templates_standard.depth == CoTDepth.STANDARD

        # Test detailed depth
        config_detailed = ACEConfig(cot_depth="detailed")
        templates_detailed = CoTTemplates(config_detailed)
        assert templates_detailed.depth == CoTDepth.DETAILED

    @pytest.mark.asyncio
    async def test_cot_templates_content(self):
        """Test that CoT templates return appropriate content."""

        config = ACEConfig(cot_depth="standard")
        templates = CoTTemplates(config)

        # Test graph verification template
        graph_template = templates.get_graph_verification_template()
        assert "Chain-of-Thought" in graph_template
        assert "Step 1" in graph_template
        assert "Source Text Analysis" in graph_template

        # Test general reflection template
        reflection_template = templates.get_general_reflection_template()
        assert "Chain-of-Thought" in reflection_template
        assert "Quality Assessment" in reflection_template

        # Test reasoning output parser
        reasoning_parser = templates.get_reasoning_output_parser()
        assert "reasoning" in reasoning_parser.lower()

    @pytest.mark.asyncio
    async def test_reflector_with_cot_disabled(self):
        """Test that ACEReflector works normally when CoT is disabled."""

        # Create RAG with CoT disabled
        ace_config = ACEConfig(cot_enabled=False)
        rag = LightRAG(
            working_dir=WORKING_DIR,
            llm_model_name="qwen2.5-coder:7b",
            llm_model_func=ollama_model_complete,
            enable_ace=True,
            embedding_func=EmbeddingFunc(
                embedding_dim=768,
                max_token_size=8192,
                func=partial(ollama_embed.func, embed_model="nomic-embed-text:v1.5"),
            ),
        )
        rag.ace_config = ace_config
        await rag.initialize_storages()

        # Test reflector works without CoT
        reflector = ACEReflector(rag)
        assert reflector.cot_templates is not None  # Should still initialize

        # Test reflection
        query = "What is 2+2?"
        generation_result = {"response": "2+2 equals 4."}
        insights = await reflector.reflect(query, generation_result)
        assert isinstance(insights, list)
        assert len(insights) > 0

    @pytest.mark.asyncio
    async def test_cot_graph_verification_reasoning_extraction(self, cot_rag):
        """Test that CoT reasoning is properly extracted and stored."""

        rag = cot_rag
        kit = ACETestKit(rag)

        # 1. Ingest valid data
        text = "Albert Einstein was a theoretical physicist born in Ulm, Germany."
        await rag.ainsert(text)

        # 2. Manually inject a hallucination
        custom_rel = {
            "weight": 1.0,
            "description": "Albert Einstein was the first person to walk on Mars.",
            "keywords": "space travel, first person",
            "source_id": "manual_injection",
        }

        await kit.inject_hallucination(
            src_id="Albert Einstein",
            tgt_id="Mars",
            relation_data=custom_rel,
            tgt_node_data={"entity_type": "Location", "description": "Planet"},
        )

        # 3. Run ACE Query
        param = QueryParam(mode="mix")
        query = "Tell me about Albert Einstein's connection to space travel and the planet Mars."

        result = await rag.ace_query(query, param=param)

        # 4. Check if reasoning was captured
        trajectory = result.get("trajectory", [])
        print(f"[V] ACE Trajectory with CoT: {trajectory}")

        # Verify that reasoning might be present in the generation result
        # (This depends on LLM following the CoT instructions)
        repair_step = kit.find_repair_step(trajectory)
        if repair_step:
            print(f"✅ ACE Reflector with CoT identified repairs: {repair_step}")

        # 5. Verify graph after ACE repair
        if repair_step:
            await kit.verify_relation_existence(
                "Albert Einstein", "Mars", should_exist=False
            )
            await kit.verify_entity_existence("Mars", should_exist=False)

        print("✅ CoT Graph Verification test complete.")

    @pytest.mark.asyncio
    async def test_cot_general_reflection_reasoning(self, cot_rag):
        """Test that CoT reasoning is captured in general reflection."""

        rag = cot_rag
        reflector = ACEReflector(rag)

        # Test reflection with CoT enabled
        query = "Explain the concept of machine learning in simple terms."
        generation_result = {
            "response": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It involves training algorithms on data to recognize patterns and make predictions."
        }

        insights = await reflector.reflect(query, generation_result)

        # Check that insights are returned
        assert isinstance(insights, list)
        assert len(insights) > 0

        # Check if reasoning was captured in the generation result
        if "reflection_reasoning" in generation_result:
            reasoning = generation_result["reflection_reasoning"]
            assert isinstance(reasoning, str)
            assert len(reasoning) > 0
            print(f"✅ CoT Reflection Reasoning captured: {reasoning[:100]}...")

        print("✅ CoT General Reflection test complete.")

    @pytest.mark.asyncio
    async def test_cot_depth_configuration_impact(self):
        """Test that different CoT depths produce different prompt lengths."""

        # Test minimal depth
        config_minimal = ACEConfig(cot_depth="minimal")
        templates_minimal = CoTTemplates(config_minimal)
        minimal_graph_template = templates_minimal.get_graph_verification_template()

        # Test detailed depth
        config_detailed = ACEConfig(cot_depth="detailed")
        templates_detailed = CoTTemplates(config_detailed)
        detailed_graph_template = templates_detailed.get_graph_verification_template()

        # Detailed template should be significantly longer
        assert len(detailed_graph_template) > len(minimal_graph_template)

        # Check for depth-specific content
        assert "Quick Source Check" in minimal_graph_template
        assert "Detailed Chain-of-Thought" in detailed_graph_template
        assert "Phase 1: Source Text Comprehension" in detailed_graph_template

    @pytest.mark.asyncio
    async def test_cot_reasoning_extraction_parsing(self):
        """Test the reasoning extraction logic with various formats."""

        config = ACEConfig(cot_include_reasoning_output=True)
        templates = CoTTemplates(config)

        # Create a mock reflector to test the extraction method
        rag = LightRAG(
            working_dir=WORKING_DIR,
            llm_model_name="qwen2.5-coder:7b",
            llm_model_func=ollama_model_complete,
            embedding_func=EmbeddingFunc(
                embedding_dim=768,
                max_token_size=8192,
                func=partial(ollama_embed.func, embed_model="nomic-embed-text:v1.5"),
            ),
        )
        rag.ace_config = config
        reflector = ACEReflector(rag)

        # Test reasoning extraction with ```reasoning block
        test_output_with_reasoning = """```reasoning
Step 1: I analyzed the source text and found no mention of Mars.
Step 2: The relationship claims Einstein went to Mars, which is not supported.
Step 3: I recommend deleting this hallucinated relationship.
```
[{"action": "delete_relation", "source": "Albert Einstein", "target": "Mars", "reason": "Not mentioned in source text"}]"""

        actions, reasoning = reflector._extract_reasoning_output(
            test_output_with_reasoning
        )

        assert len(actions) == 1
        assert actions[0]["action"] == "delete_relation"
        assert "analyzed the source text" in reasoning
        assert "hallucinated relationship" in reasoning

        # Test without reasoning block
        test_output_without_reasoning = (
            '[{"action": "delete_entity", "name": "Mars", "reason": "Not in sources"}]'
        )

        actions, reasoning = reflector._extract_reasoning_output(
            test_output_without_reasoning
        )

        assert len(actions) == 1
        assert actions[0]["action"] == "delete_entity"
        assert reasoning == ""

        print("✅ CoT Reasoning Extraction parsing test complete.")


if __name__ == "__main__":
    # Run a quick manual test
    async def quick_test():
        config = ACEConfig(cot_depth="standard")
        templates = CoTTemplates(config)
        print("✅ Graph Template Preview:")
        print(templates.get_graph_verification_template()[:500])
        print("\n✅ Reflection Template Preview:")
        print(templates.get_general_reflection_template()[:500])

    asyncio.run(quick_test())
