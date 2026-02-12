#!/usr/bin/env python3
"""
Embedding Performance Test and Profiling

This script helps identify bottlenecks in the LightRAG embedding pipeline
by measuring performance with different document sizes and configurations.
"""

import asyncio
import time
import os
from typing import List
from lightrag import LightRAG
from lightrag.constants import (
    DEFAULT_EMBEDDING_FUNC_MAX_ASYNC,
    DEFAULT_EMBEDDING_BATCH_NUM,
    DEFAULT_EMBEDDING_TIMEOUT,
)


async def test_embedding_performance():
    """Test embedding performance with different document sizes"""
    print("🔍 LightRAG Embedding Performance Test")
    print(f"Configuration:")
    print(f"  - Max async workers: {DEFAULT_EMBEDDING_FUNC_MAX_ASYNC}")
    print(f"  - Batch size: {DEFAULT_EMBEDDING_BATCH_NUM}")
    print(f"  - Timeout: {DEFAULT_EMBEDDING_TIMEOUT}s")
    print()

    # Initialize LightRAG with minimal config for testing
    rag = LightRAG(
        working_dir="./test_rag_storage",
        embedding_func_max_async=DEFAULT_EMBEDDING_FUNC_MAX_ASYNC,
        embedding_batch_num=DEFAULT_EMBEDDING_BATCH_NUM,
        default_embedding_timeout=DEFAULT_EMBEDDING_TIMEOUT,
    )

    # Test documents of different sizes
    test_docs = [
        (
            "Small (1KB)",
            "This is a small test document for basic performance testing." * 100,
        ),
        (
            "Medium (10KB)",
            "This is a medium-sized document that should take reasonable time to process."
            * 1000,
        ),
        (
            "Large (100KB)",
            "This is a large document that may reveal performance bottlenecks." * 10000,
        ),
        (
            "Very Large (1MB)",
            "This is a very large document that tests upper limits of the system."
            * 100000,
        ),
    ]

    results = []

    for doc_name, content in test_docs:
        print(f"\n📊 Testing {doc_name} document ({len(content):,} characters)")

        try:
            start_time = time.time()

            # Insert document using insert method
            result = await rag.ainsert(content)

            end_time = time.time()
            duration = end_time - start_time

            print(f"⏱️  Duration: {duration:.2f}s")
            print(f"📈 Throughput: {len(content) / duration:.0f} chars/s")

            results.append(
                {
                    "doc_size": len(content),
                    "duration": duration,
                    "throughput": len(content) / duration,
                    "status": "success"
                    if result and result.get("success")
                    else "failed",
                }
            )

        except Exception as e:
            print(f"❌ Error: {e}")
            results.append(
                {
                    "doc_size": len(content),
                    "duration": 0,
                    "throughput": 0,
                    "status": "error",
                    "error": str(e),
                }
            )

    # Summary analysis
    print(f"\n📊 PERFORMANCE ANALYSIS")
    print("=" * 50)

    successful_results = [r for r in results if r["status"] == "success"]
    if successful_results:
        avg_throughput = sum(r["throughput"] for r in successful_results) / len(
            successful_results
        )
        max_throughput = max(r["throughput"] for r in successful_results)
        min_throughput = min(r["throughput"] for r in successful_results)

        print(f"✅ Successful embeddings: {len(successful_results)}/{len(results)}")
        print(f"📈 Average throughput: {avg_throughput:.0f} chars/s")
        print(f"📈 Max throughput: {max_throughput:.0f} chars/s")
        print(f"📉 Min throughput: {min_throughput:.0f} chars/s")

        # Analyze performance patterns
        large_doc_results = [r for r in successful_results if r["doc_size"] >= 10000]
        if large_doc_results:
            large_avg_throughput = sum(
                r["throughput"] for r in large_doc_results
            ) / len(large_doc_results)
            print(f"📊 Large document throughput: {large_avg_throughput:.0f} chars/s")

            # Performance assessment
            if large_avg_throughput < 1000:  # Less than 1KB/s
                print("🚨 PERFORMANCE ISSUE DETECTED")
                print(
                    "   Large documents processing < 1KB/s indicates significant bottlenecks"
                )
                print(
                    "   Expected: Large documents should process faster due to batching"
                )
            elif large_avg_throughput < 5000:  # Less than 5KB/s
                print("⚠️  Moderate performance")
                print("   Large documents processing 5-10KB/s - room for improvement")
            else:
                print("✅ Good performance")
                print("   Large documents processing > 10KB/s - acceptable")
    else:
        print("❌ No successful embeddings to analyze")

    # Cleanup
    import shutil

    if os.path.exists("./test_rag_storage"):
        shutil.rmtree("./test_rag_storage")
        print("🧹 Cleaned up test storage")

    return results


if __name__ == "__main__":
    asyncio.run(test_embedding_performance())
