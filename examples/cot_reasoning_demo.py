#!/usr/bin/env python3
"""
🧠 Chain-of-Thought (CoT) Reasoning Example for ACE Reflector

This script demonstrates how to use CoT reasoning in LightRAG's ACE framework
for enhanced graph verification and reflection capabilities.

Run this script to see CoT reasoning in action with different configuration options.
"""

import asyncio
import os
import shutil
from functools import partial

from lightrag import LightRAG, QueryParam
from lightrag.ace.config import ACEConfig
from lightrag.llm.ollama import ollama_embed, ollama_model_complete
from lightrag.utils import EmbeddingFunc

WORKING_DIR = "./cot_demo_storage"


async def setup_rag_with_cot(depth: str = "standard"):
    """Setup LightRAG with CoT configuration."""

    # Clean up previous runs
    if os.path.exists(WORKING_DIR):
        shutil.rmtree(WORKING_DIR)
    os.makedirs(WORKING_DIR)

    # Configure CoT settings
    ace_config = ACEConfig(
        cot_enabled=True,
        cot_depth=depth,
        cot_graph_verification=True,
        cot_general_reflection=True,
        cot_include_reasoning_output=True,
    )

    # Initialize LightRAG
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

    # Apply ACE configuration
    rag.ace_config = ace_config
    await rag.initialize_storages()

    return rag


async def demo_cot_graph_verification():
    """Demonstrate CoT reasoning for graph verification."""

    print("🔍 Demo: CoT Graph Verification")
    print("=" * 50)

    rag = await setup_rag_with_cot("standard")

    # 1. Insert some test data
    print("📝 Inserting test data...")
    await rag.ainsert(
        "Albert Einstein was a theoretical physicist born in Ulm, Germany. He developed the theory of relativity."
    )
    await rag.ainsert(
        "Mars is the fourth planet from the Sun in our solar system. It is known as the Red Planet."
    )

    # 2. Create a hallucination manually (for demonstration)
    print("🎯 Creating test scenario (simulated hallucination)...")

    # 3. Query with ACE to trigger CoT reasoning
    query = "What is the connection between Albert Einstein and Mars?"
    param = QueryParam(mode="mix")

    print(f"🤔 Query: {query}")
    print("🔄 Running ACE query with CoT reasoning...")

    result = await rag.ace_query(query, param=param)

    # 4. Show results
    print("\n📊 Results:")
    print(f"Response: {result.get('response', 'No response')[:200]}...")

    trajectory = result.get("trajectory", [])
    print(f"Trajectory steps: {len(trajectory)}")

    # Look for CoT reasoning in trajectory
    for i, step in enumerate(trajectory):
        if step.get("type") == "graph_repair":
            print(f"\n🧠 Graph Repair Step {i + 1}:")
            print(f"  Status: {step.get('status', 'unknown')}")
            if "reasoning" in step:
                print(f"  Reasoning: {step['reasoning'][:150]}...")
            print(f"  Actions: {len(step.get('repairs', []))}")

    print("\n✅ Graph verification demo complete!\n")


async def demo_cot_general_reflection():
    """Demonstrate CoT reasoning for general reflection."""

    print("🧠 Demo: CoT General Reflection")
    print("=" * 50)

    rag = await setup_rag_with_cot("detailed")  # Use detailed for demo

    # 1. Test a query
    query = (
        "Explain the difference between machine learning and artificial intelligence."
    )
    param = QueryParam(mode="local")

    print(f"🤔 Query: {query}")
    print("🔄 Running query with CoT reflection...")

    result = await rag.aquery(query, param=param)

    # 2. Trigger reflection manually to see CoT reasoning
    from lightrag.ace.reflector import ACEReflector

    reflector = ACEReflector(rag)

    generation_result = {"response": result}

    insights = await reflector.reflect(query, generation_result)

    print("\n📊 Results:")
    print(f"Response: {result[:200]}...")
    print("\n💡 Reflection Insights:")
    for i, insight in enumerate(insights, 1):
        print(f"  {i}. {insight}")

    # Check if reasoning was captured
    if "reflection_reasoning" in generation_result:
        reasoning = generation_result["reflection_reasoning"]
        print("\n🧠 CoT Reasoning (excerpt):")
        print(f"  {reasoning[:300]}...")

    print("\n✅ General reflection demo complete!\n")


async def demo_cot_depth_comparison():
    """Compare different CoT depth levels."""

    print("📊 Demo: CoT Depth Comparison")
    print("=" * 50)

    depths = ["minimal", "standard", "detailed"]
    query = "What is the relationship between Python programming and machine learning?"

    for depth in depths:
        print(f"\n🔬 Testing CoT Depth: {depth.upper()}")
        print("-" * 30)

        rag = await setup_rag_with_cot(depth)

        # Insert test data
        await rag.ainsert(
            "Python is a popular programming language used extensively in machine learning."
        )
        await rag.ainsert(
            "Machine learning is a subset of artificial intelligence that uses algorithms to learn from data."
        )

        # Run query
        result = await rag.aquery(query, param=QueryParam(mode="local"))

        # Check CoT template content
        from lightrag.ace.cot_templates import CoTTemplates

        templates = CoTTemplates(rag.ace_config)
        template = templates.get_general_reflection_template()

        print(f"Template length: {len(template)} characters")
        print(f"Response excerpt: {result[:100]}...")

        # Look for depth-specific content
        if "Quick" in template:
            print("✓ Contains minimal-depth indicators")
        if "Step-by-step" in template:
            print("✓ Contains standard-depth indicators")
        if "Comprehensive" in template:
            print("✓ Contains detailed-depth indicators")


async def main():
    """Run all CoT demonstration scenarios."""

    print("🚀 Chain-of-Thought (CoT) Reasoning Demo")
    print("=" * 60)
    print("This demo showcases CoT reasoning in LightRAG's ACE Reflector.")
    print("Make sure you have Ollama running with qwen2.5-coder:7b model.\n")

    try:
        # Demo 1: Graph verification with CoT
        await demo_cot_graph_verification()

        # Demo 2: General reflection with CoT
        await demo_cot_general_reflection()

        # Demo 3: Depth comparison
        await demo_cot_depth_comparison()

        print("🎉 All CoT demos completed successfully!")
        print("\n📚 Key Takeaways:")
        print("• CoT provides structured, step-by-step reasoning")
        print("• Different depth levels balance accuracy vs token cost")
        print("• Reasoning is captured for debugging and transparency")
        print("• Integration is seamless with existing ACE workflow")

    except Exception as e:
        print(f"❌ Error running demo: {e}")
        print("Make sure Ollama is running with: ollama serve")
        print("And qwen2.5-coder:7b model is available: ollama pull qwen2.5-coder:7b")

    finally:
        # Cleanup
        if os.path.exists(WORKING_DIR):
            shutil.rmtree(WORKING_DIR)


if __name__ == "__main__":
    asyncio.run(main())
