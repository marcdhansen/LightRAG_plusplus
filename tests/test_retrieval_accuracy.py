import httpx
import pytest

pytestmark = pytest.mark.heavy

# Configuration
BASE_URL = "http://localhost:9621"


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.requires_api
class TestRetrievalAccuracy:
    """
    Test suite to verify that the RAG system can accurately retrieve information
    from the diverse set of restored test documents.
    """

    @pytest.fixture(autouse=True)
    async def setup_check(self):
        """Ensure server is healthy before running tests."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{BASE_URL}/health")
                assert resp.status_code == 200, "Server is not healthy"
            except Exception as e:
                pytest.fail(f"Could not connect to LightRAG server: {e}")

    @pytest.mark.parametrize(
        "question, expected_phrases, doc_context",
        [
            # Literature: A Tale of Two Cities
            (
                "What was the season of Light?",
                ["season of Light", "epoch of belief"],
                "tale_of_two_cities.txt",
            ),
            (
                "What was the epoch of incredulity?",
                ["epoch of incredulity"],
                "tale_of_two_cities.txt",
            ),
            # Movie: The Terminator
            (
                "Who did Skynet send back to 1984?",
                ["Terminator", "cyborg"],
                "terminator.txt",
            ),
            ("Who is the mother of John Connor?", ["Sarah Connor"], "terminator.txt"),
            # Technical: LightRAG Documentation (General Knowledge from docs)
            (
                "What database is used for graph storage?",
                ["Memgraph", "Neo4j"],
                "LightRAG Docs",
            ),
            # BCBC: Building Code Project (Restored Text)
            (
                "What are the criteria used to filter building codes?",
                [
                    "Usage",
                    "Square Footage",
                    "Storeys",
                    "Construction Type",
                    "Sprinklered",
                ],
                "bcbc_restored.txt",
            ),
            (
                "What is the primary purpose of the Digitization project?",
                ["digitize", "British Columbia Building Code", "BCBC", "accessibility"],
                "bcbc_restored.txt",
            ),
            # Multi-Hop / Reasoning: Terminator Logic
            (
                "Why did Skynet target the woman played by Linda Hamilton?",
                ["John Connor", "son", "mother", "save mankind", "future"],
                "terminator.txt",
            ),
            (
                "What event causes the antagonist to become self-aware?",
                ["Skynet", "nuclear", "holocaust"],
                "terminator.txt",
            ),
        ],
    )
    async def test_retrieval_accuracy(self, question, expected_phrases, doc_context):
        """
        Ask a question and verify the response contains key expected phrases.
        """
        print(f"\n\n❓ Question: {question}")
        print(f"   Context: {doc_context}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            # We use 'mix' mode for best retrieval accuracy
            payload = {"query": question, "mode": "mix", "include_references": True}

            try:
                response = await client.post(f"{BASE_URL}/query", json=payload)

                assert response.status_code == 200, f"Query failed: {response.text}"
                data = response.json()

                # Check response logic
                answer = data.get("response", "")
                if not answer and isinstance(data, str):
                    # Handle case where API might return raw string (unlikely but safe)
                    answer = data

                print(
                    f"🗣️  Answer: {answer[:200]}..."
                    if len(answer) > 200
                    else f"🗣️  Answer: {answer}"
                )

                # Verification
                found_any = False
                missing_phrases = []

                # Soft check: At least one of the expected phrases should be present
                # OR if exact match isn't found, we might manually review.
                # For test automation, we assert at least one key phrase is found.

                answer_lower = answer.lower()

                for phrase in expected_phrases:
                    if phrase.lower() in answer_lower:
                        found_any = True
                    else:
                        missing_phrases.append(phrase)

                if not found_any:
                    print(f"❌ Failed to find any of: {expected_phrases}")
                    pytest.fail(
                        f"Answer did not contain expected key phrases. Answer: {answer}"
                    )
                else:
                    print("✅ Verified key phrases present.")

            except Exception as e:
                pytest.fail(f"Exception during query: {e}")
