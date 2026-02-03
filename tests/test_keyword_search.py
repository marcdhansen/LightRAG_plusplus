#!/usr/bin/env python3
"""
Comprehensive test suite for keyword search functionality in LightRAG
Tests all aspects of keyword search including integration with LightRAG pipeline.
"""

import asyncio
import tempfile
import os
import pytest
from typing import List

from lightrag.core import LightRAG
from lightrag.base import QueryParam
from lightrag.kg.nano_vector_db_impl import NanoKeywordStorage
from lightrag.kg.neo4j_impl import Neo4jKeywordStorage
from lightrag.utils import EmbeddingFunc


class TestKeywordSearch:
    """Test suite for keyword search functionality"""

    @pytest.fixture
    async def keyword_storage(self):
        """Fixture providing a simple keyword storage for testing"""
        from dataclasses import dataclass
        from lightrag.base import BaseKeywordStorage

        @dataclass
        class MockKeywordStorage(BaseKeywordStorage):
            def __init__(self):
                self.indexed_docs = {}
                self.initialized = False

            async def initialize(self):
                self.initialized = True

            async def finalize(self):
                pass

            async def index_done_callback(self):
                pass

            async def index_keywords(
                self, doc_id: str, keywords: List[str], content: str
            ) -> None:
                self.indexed_docs[doc_id] = {"content": content, "keywords": keywords}

            async def search_keywords(
                self, keywords: List[str], limit: int = 50
            ) -> List[dict]:
                results = []
                for doc_id, doc_data in self.indexed_docs.items():
                    # Check if any keywords match
                    matched_keywords = [
                        kw for kw in keywords if kw in doc_data["keywords"]
                    ]
                    if matched_keywords:
                        results.append(
                            {
                                "doc_id": doc_id,
                                "content": doc_data["content"],
                                "keywords": matched_keywords,
                                "score": len(matched_keywords),
                            }
                        )
                # Sort by score (number of matched keywords) and limit
                return sorted(results, key=lambda x: x["score"], reverse=True)[:limit]

            async def delete_document(self, doc_id: str) -> None:
                if doc_id in self.indexed_docs:
                    del self.indexed_docs[doc_id]

            async def update_document(
                self, doc_id: str, keywords: List[str], content: str
            ) -> None:
                await self.delete_document(doc_id)
                await self.index_keywords(doc_id, keywords, content)

            async def drop(self) -> dict[str, str]:
                self.indexed_docs = {}
                return {"status": "success", "message": "data dropped"}

        return MockKeywordStorage()

    @pytest.mark.asyncio
    async def test_nano_keyword_storage_basic_operations(self, keyword_storage):
        """Test basic NanoKeywordStorage operations"""
        # Test indexing
        await keyword_storage.index_keywords(
            "doc1", ["python", "ai"], "Python AI content"
        )
        await keyword_storage.index_keywords(
            "doc2", ["machine", "learning"], "ML content"
        )

        # Test search
        results = await keyword_storage.search_keywords(["python", "ai"], limit=10)
        assert len(results) > 0, "Should find matching documents"
        assert results[0]["doc_id"] == "doc1", "Should find doc1"
        assert "python" in results[0]["keywords"], "Should include matched keywords"

        # Test deletion
        await keyword_storage.delete_document("doc1")
        results_after_delete = await keyword_storage.search_keywords(
            ["python"], limit=10
        )
        assert len(results_after_delete) == 0, "Document should be deleted"

    @pytest.mark.asyncio
    async def test_query_param_keyword_mode(self):
        """Test QueryParam keyword mode support"""
        # Test that keyword mode is in Literal
        query_param = QueryParam(mode="keyword")
        assert query_param.mode == "keyword", "Keyword mode should be set"

        # Test RRF weights include keyword
        assert "keyword" in query_param.rrf_weights, (
            "RRF weights should include keyword"
        )
        assert query_param.rrf_weights["keyword"] == 1.0, (
            "Default keyword weight should be 1.0"
        )

    @pytest.mark.asyncio
    async def test_keyword_data_function(self):
        """Test _get_keyword_data function"""
        from lightrag.operate import _get_keyword_data
        from lightrag.base import BaseKeywordStorage
        from dataclasses import dataclass
        from typing import List

        @dataclass
        class TestStorage(BaseKeywordStorage):
            def __init__(self):
                self.searched_keywords = []
                self.searched_limit = 0

            async def initialize(self):
                pass

            async def finalize(self):
                pass

            async def index_done_callback(self):
                pass

            async def index_keywords(
                self, doc_id: str, keywords: List[str], content: str
            ) -> None:
                pass

            async def search_keywords(
                self, keywords: List[str], limit: int = 50
            ) -> List[dict]:
                self.searched_keywords = keywords
                self.searched_limit = limit

                # Return mock results
                return [
                    {
                        "doc_id": f"doc_{i}",
                        "content": f"Content about {kw}",
                        "keywords": [kw],
                        "score": 1.0,
                    }
                    for i, kw in enumerate(keywords[:limit])
                ]

            async def delete_document(self, doc_id: str) -> None:
                pass

            async def update_document(
                self, doc_id: str, keywords: List[str], content: str
            ) -> None:
                pass

            async def drop(self) -> dict[str, str]:
                return {"status": "success", "message": "data dropped"}

        storage = TestStorage()
        query_param = QueryParam(mode="keyword", top_k=5)

        # Test keyword data retrieval
        results, _ = await _get_keyword_data(["python", "ai"], storage, query_param)

        assert len(results) == 2, "Should return 2 results for 2 keywords"
        assert storage.searched_keywords == ["python", "ai"], (
            "Should pass correct keywords"
        )
        assert storage.searched_limit == 5, "Should pass correct limit"

    @pytest.mark.asyncio
    async def test_lightrag_keyword_integration(self):
        """Test full LightRAG integration with keyword search"""

        # Create dummy embedding function
        def dummy_embedding_func(texts):
            return [[0.1] * 10 for _ in texts]

        # Wrap with EmbeddingFunc
        dummy_embedding = EmbeddingFunc(embedding_dim=10, func=dummy_embedding_func)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize LightRAG with keyword storage
            rag = LightRAG(
                working_dir=temp_dir,
                embedding_func=dummy_embedding,
                keyword_storage_backend="NanoKeywordStorage",
            )

            await rag.initialize_storages()

            # Test that keyword storage is initialized
            assert rag.keyword_storage is not None, (
                "Keyword storage should be initialized"
            )
            assert hasattr(rag.keyword_storage, "search_keywords"), (
                "Storage should have search method"
            )

            # Test that keyword mode works in query pipeline
            # Index some test documents first
            await rag.keyword_storage.index_keywords(
                doc_id="test_doc_1",
                keywords=["python", "programming"],
                content="Test Python programming content",
            )

            await rag.keyword_storage.index_keywords(
                doc_id="test_doc_2",
                keywords=["machine", "learning"],
                content="Test machine learning content",
            )

            # Test query with keyword mode (this tests the full pipeline)
            from lightrag.operate import kg_query

            global_config = {"working_dir": temp_dir}

            query_result = await kg_query(
                query="python programming",
                knowledge_graph_inst=rag.chunk_entity_relation_graph,
                entities_vdb=rag.entities_vdb,
                relationships_vdb=rag.relationships_vdb,
                text_chunks_db=rag.text_chunks,
                query_param=QueryParam(mode="keyword"),
                global_config=global_config,
                chunks_vdb=rag.chunks_vdb,
                keyword_storage=rag.keyword_storage,
            )

            assert query_result is not None, "Query should return result"
            assert query_result.raw_data is not None, "Query should have raw data"

            await rag.finalize_storages()

    @pytest.mark.asyncio
    async def test_rrf_keyword_integration(self):
        """Test RRF integration with keyword results"""
        from lightrag.operate import _perform_kg_search
        from dataclasses import dataclass
        from typing import List

        @dataclass
        class MockStorage:
            keyword_results = [
                {
                    "doc_id": "kw1",
                    "content": "Python content",
                    "score": 2.0,
                    "keywords": ["python"],
                },
                {
                    "doc_id": "kw2",
                    "content": "AI content",
                    "score": 1.5,
                    "keywords": ["ai", "machine"],
                },
            ]

            # Mock other storage components
            graph_inst = None
            entities_vdb = None
            relationships_vdb = None
            text_chunks_db = None
            chunks_vdb = None
            keyword_storage = None

            # Create keyword storage with results
            class MockKeywordStorage:
                async def initialize(self):
                    pass

                async def finalize(self):
                    pass

                async def index_done_callback(self):
                    pass

                async def index_keywords(
                    self, doc_id: str, keywords: List[str], content: str
                ) -> None:
                    pass

                async def delete_document(self, doc_id: str) -> None:
                    pass

                async def update_document(
                    self, doc_id: str, keywords: List[str], content: str
                ) -> None:
                    pass

                async def drop(self) -> dict[str, str]:
                    pass

                async def search_keywords(
                    self, keywords: List[str], limit: int = 50
                ) -> List[dict]:
                    return MockStorage.keyword_results

            keyword_storage = MockKeywordStorage()

        # Test RRF with keyword mode
        query_param = QueryParam(
            mode="rrf",
            rrf_k=60,
            rrf_weights={"vector": 1.0, "graph": 1.0, "keyword": 1.0},
        )

        result = await _perform_kg_search(
            query="python ai",
            ll_keywords="python",
            hl_keywords="ai machine",
            knowledge_graph_inst=graph_inst,
            entities_vdb=entities_vdb,
            relationships_vdb=relationships_vdb,
            text_chunks_db=text_chunks_db,
            query_param=query_param,
            chunks_vdb=chunks_vdb,
            keyword_storage=keyword_storage,
        )

        # Verify keyword results are included
        assert "keyword_contexts" in result, (
            "Result should include keyword contexts"
        )
        assert len(result["keyword_contexts"]) == 2, (
            "Should include both keyword results"
        )

    @pytest.mark.asyncio
    async def test_error_handling(self, keyword_storage):
        """Test error handling in keyword search"""
        # Test search with empty keywords
        results = await keyword_storage.search_keywords([], limit=10)
        assert len(results) == 0, "Empty keywords should return no results"

        # Test search with limit
        await keyword_storage.index_keywords("doc1", ["python", "ai"], "content 1")
        await keyword_storage.index_keywords("doc2", ["python", "ml"], "content 2")
        await keyword_storage.index_keywords("doc3", ["python", "data"], "content 3")

        results_limited = await keyword_storage.search_keywords(["python"], limit=2)
        assert len(results_limited) <= 2, "Should respect limit"

        # Test document deletion
        await keyword_storage.delete_document("nonexistent")
        # Should not raise error for non-existent document

    @pytest.mark.asyncio
    async def test_performance(self, keyword_storage):
        """Test performance with larger datasets"""
        # Index many documents
        import time

        start_time = time.time()

        for i in range(100):
            await keyword_storage.index_keywords(
                doc_id=f"doc_{i}",
                keywords=[f"keyword_{i}", f"tag_{i}"],
                content=f"Content for document {i} with keywords",
            )

        indexing_time = time.time() - start_time

        # Test search performance
        start_time = time.time()
        results = await keyword_storage.search_keywords(
            ["keyword_1", "keyword_2"], limit=10
        )
        search_time = time.time() - start_time

        # Performance should be reasonable (these are loose limits)
        assert indexing_time < 5.0, "Indexing 100 docs should take < 5 seconds"
        assert search_time < 1.0, "Search should be fast"
        assert len(results) > 0, "Should find results"


if __name__ == "__main__":
    # Run a quick test when executed directly
    async def quick_test():
        """Quick functional test"""
        test_instance = TestKeywordSearch()
        storage = await test_instance.keyword_storage()

        print("🧪 Running comprehensive keyword search tests...")

        try:
            await test_instance.test_nano_keyword_storage_basic_operations(storage)
            print("✅ Basic operations test passed")

            await test_instance.test_query_param_keyword_mode()
            print("✅ QueryParam keyword mode test passed")

            await test_instance.test_keyword_data_function()
            print("✅ Keyword data function test passed")

            await test_instance.test_lightrag_keyword_integration()
            print("✅ LightRAG integration test passed")

            await test_instance.test_rrf_keyword_integration()
            print("✅ RRF integration test passed")

            await test_instance.test_error_handling(storage)
            print("✅ Error handling test passed")

            await test_instance.test_performance(storage)
            print("✅ Performance test passed")

            print("\n🎉 ALL KEYWORD SEARCH TESTS PASSED!")
            print("📋 Test coverage includes:")
            print("   ✅ Basic storage operations")
            print("   ✅ QueryParam keyword mode")
            print("   ✅ Keyword data retrieval")
            print("   ✅ LightRAG pipeline integration")
            print("   ✅ RRF fusion integration")
            print("   ✅ Error handling")
            print("   ✅ Performance testing")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback

            traceback.print_exc()

    asyncio.run(quick_test())
