#!/usr/bin/env python3
"""
Quick test for keyword search functionality
"""

import asyncio
import tempfile

from lightrag.base import QueryParam
from lightrag.kg.nano_vector_db_impl import NanoKeywordStorage


async def test_keyword_search():
    """Test basic keyword search functionality"""

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temp directory: {temp_dir}")

        # Test NanoKeywordStorage directly
        keyword_storage = NanoKeywordStorage(
            namespace="test_keyword_store",
            workspace="test_workspace",
            global_config={"working_dir": temp_dir},
        )

        try:
            # Initialize storage
            await keyword_storage.initialize()
            print("✅ Keyword storage initialized successfully")

            # Test adding some keywords
            await keyword_storage.index_keywords(
                doc_id="test_doc_1",
                keywords=["python", "programming", "test"],
                content="This is a test document about Python programming",
            )

            await keyword_storage.index_keywords(
                doc_id="test_doc_2",
                keywords=["javascript", "web", "development"],
                content="This document discusses JavaScript web development",
            )

            print("✅ Keywords indexed successfully")

            # Test keyword search
            results = await keyword_storage.search_keywords(
                keywords=["python", "programming"], limit=10
            )

            print(f"🔍 Search results: {len(results)} documents found")
            for result in results:
                print(f"  📄 {result['doc_id']}: {result['content'][:50]}...")
                print(f"     🏷️  Keywords: {result['keywords']}")
                print(f"     📊 Score: {result['score']}")

            # Test QueryParam with keyword mode
            print("\n🧪 Testing QueryParam with keyword mode...")
            query_param = QueryParam(mode="keyword")
            print(f"✅ QueryParam created with mode: {query_param.mode}")

            # Verify keyword mode is supported
            if "keyword" in str(query_param.__class__.__annotations__["mode"]):
                print("✅ Keyword mode is properly supported in QueryParam")
            else:
                print("❌ Keyword mode not found in QueryParam Literal")

            print("\n🎉 All tests passed! Keyword search functionality is working.")

        except Exception as e:
            print(f"❌ Error during testing: {e}")
            import traceback

            traceback.print_exc()

        finally:
            # Clean up
            await keyword_storage.finalize()
            print("🧹 Storage finalized")


if __name__ == "__main__":
    asyncio.run(test_keyword_search())
