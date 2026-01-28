import pytest
import httpx
import time
import json

# Configuration
TIMEOUT = 300  # 5 minutes specifically for indexing
BASE_URL = "http://localhost:9621"
API_KEY = "your-secure-api-key-here-123"

# Mark as heavy and integration test
pytestmark = [pytest.mark.heavy, pytest.mark.integration]


@pytest.fixture(scope="function")
def test_document():
    """
    Fixture to upload a sample document, wait for processing, yield its ID and original content, and clean up.
    """
    filename = "test_document_references_logic.txt"
    # Provide enough content to ensure multiple chunks might be possible,
    # though for a single small sentence it might still be one chunk.
    # We'll provide a few paragraphs.
    content = (
        "Quantum computing is a type of computing that uses the collective properties of quantum states, "
        "such as superposition, interference, and entanglement, to perform calculations. "
        "The fundamental units of quantum information are qubits, which can exist in multiple states simultaneously.\n\n"
        "In contrast to classical computers that use bits (0 or 1), quantum computers leverage quantum bits. "
        "This allows them to solve certain complex problems much faster than traditional supercomputers. "
        "Shor's algorithm for factoring large integers is a famous example of a quantum algorithm that outperforms its classical counterpart.\n\n"
        "LightRAG can index this quantum computing information into a knowledge graph. "
        "It allow users to retrieve specific facts about qubits and quantum algorithms. "
        "The system maintains references to the original document to ensure traceability of information."
    )

    upload_url = f"{BASE_URL}/documents/upload"
    track_url_template = f"{BASE_URL}/documents/track_status/{{}}"
    delete_url = f"{BASE_URL}/documents/delete_document"

    headers = {"X-API-Key": API_KEY}

    print(f"\n[Fixture] Uploading {filename}...")
    try:
        files = {"file": (filename, content, "text/plain")}
        response = httpx.post(upload_url, headers=headers, files=files, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        track_id = data.get("track_id")
        print(f"[Fixture] Upload initiated. Track ID: {track_id}")
    except Exception as e:
        pytest.fail(f"Upload failed: {e}")

    # Poll for completion
    doc_id = None
    start_time = time.time()
    processed = False

    print("[Fixture] Waiting for indexing to complete...")
    while time.time() - start_time < TIMEOUT:
        try:
            status_resp = httpx.get(
                track_url_template.format(track_id), headers=headers, timeout=10.0
            )
            status_resp.raise_for_status()
            status_data = status_resp.json()

            docs = status_data.get("documents", [])
            if docs:
                doc_status = docs[0]
                current_status = doc_status.get("status")
                doc_id = doc_status.get("id")

                if current_status.upper() == "PROCESSED":
                    print(f"[Fixture] Document {doc_id} processed successfully.")
                    processed = True
                    break
                elif current_status.upper() == "FAILED":
                    error = doc_status.get("error_msg", "Unknown error")
                    pytest.fail(f"Document processing failed: {error}")

            time.sleep(2)
        except Exception as e:
            print(f"[Fixture] Warning during polling: {e}")
            time.sleep(2)

    if not processed:
        pytest.fail(f"Timeout waiting for document processing (Track ID: {track_id})")

    yield {"doc_id": doc_id, "content": content}

    # Teardown
    if doc_id:
        print(f"[Fixture] Cleaning up document {doc_id}...")
        try:
            payload = {"doc_ids": [doc_id]}
            del_resp = httpx.request(
                "DELETE", delete_url, headers=headers, json=payload, timeout=30.0
            )
            if del_resp.status_code == 200:
                print("[Fixture] Cleanup successful.")
            else:
                print(f"[Fixture] Cleanup failed: {del_resp.text}")
        except Exception as e:
            print(f"[Fixture] Cleanup failed with exception: {e}")


@pytest.mark.requires_api
def test_document_content_and_reference_streaming(test_document):
    """
    Verify that:
    1. /documents/{doc_id}/content returns the full original content.
    2. /query/stream includes references with chunk contents when requested.
    3. References chunk contents are actual substrings of the original document.
    """
    doc_id = test_document["doc_id"]
    original_content = test_document["content"]
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    # 1. Test Document Content Endpoint
    content_url = f"{BASE_URL}/documents/{doc_id}/content"
    print(f"\n🧪 Testing Document Content Endpoint: GET {content_url}")
    response = httpx.get(content_url, headers=headers, timeout=20.0)
    response.raise_for_status()
    data = response.json()

    assert "content" in data
    assert data["doc_id"] == doc_id
    assert data["content"] == original_content
    print("✅ Full document content matches original")

    # 2. Test Query with References and Chunk Content
    query_url = f"{BASE_URL}/query/stream"
    payload = {
        "query": "What are qubits and how do they relate to quantum algorithms?",
        "mode": "hybrid",
        "top_k": 20,
        "include_references": True,
        "include_chunk_content": True,
        "stream": True,  # Explicitly request stream
    }

    print(f"🧪 Testing Streaming Query with References: POST {query_url}")

    with httpx.stream(
        "POST", query_url, headers=headers, json=payload, timeout=300.0
    ) as response:
        response.raise_for_status()

        found_references = False
        reference_items = []

        for line in response.iter_lines():
            if not line:
                continue

            chunk_data = json.loads(line)
            if "references" in chunk_data:
                found_references = True
                reference_items = chunk_data["references"]
                print(f"Received {len(reference_items)} references in stream")
                break  # We usually get references in the first chunk

        assert found_references, "References not found in streaming response"
        assert len(reference_items) > 0, "Reference list is empty"

        # 3. Verify specifically for our document
        target_ref = None
        for ref in reference_items:
            if ref.get("doc_id") == doc_id:
                target_ref = ref
                break

        if target_ref is None:
            print("\n❌ Target document not found! Retrieved references:")
            for ref in reference_items:
                print(
                    f"   - ID: {ref.get('reference_id')} | DocID: {ref.get('doc_id')} | File: {ref.get('file_path')}"
                )

        assert (
            target_ref is not None
        ), f"Our document {doc_id} was not among the retrieved references"
        assert "content" in target_ref, "Reference missing chunk content"
        assert isinstance(
            target_ref["content"], list
        ), "Reference content should be a list of strings"
        assert len(target_ref["content"]) > 0, "Reference content list is empty"

        print(f"✅ Found doc_id in references with {len(target_ref['content'])} chunks")

        # 4. Verify bits of chunk content are in original document
        for i, chunk_text in enumerate(target_ref["content"]):
            # Note: LightRAG might sanitize or slightly modify text during chunking,
            # so we check if the majority of it exists or use a substring check.
            # Usually it's intact for .txt files.
            assert (
                chunk_text in original_content
            ), f"Chunk {i} text not found in original document!"
            print(f"   Chunk {i} verified as internal substring")

    print("\n🎉 All document content and reference traceability tests passed!")


@pytest.mark.requires_api
def test_query_references_non_streaming(test_document):
    """
    Verify /query (non-streaming) includes references with chunk contents.
    """
    doc_id = test_document["doc_id"]
    original_content = test_document["content"]
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    query_url = f"{BASE_URL}/query"
    payload = {
        "query": "Explain Shor's algorithm in quantum computing.",
        "mode": "mix",
        "top_k": 20,
        "include_references": True,
        "include_chunk_content": True,
    }

    print(f"\n🧪 Testing Non-Streaming Query with References: POST {query_url}")
    response = httpx.post(query_url, headers=headers, json=payload, timeout=300.0)
    response.raise_for_status()
    data = response.json()

    assert "references" in data
    references = data["references"]

    our_ref = next((r for r in references if r["reference_id"] == doc_id), None)

    if our_ref is None:
        print("\n❌ Target document not found! Retrieved references:")
        for ref in references:
            print(f"   - ID: {ref.get('reference_id')} | File: {ref.get('file_path')}")

    assert our_ref is not None, "Our document not found in references"
    assert "content" in our_ref
    assert len(our_ref["content"]) > 0

    for chunk in our_ref["content"]:
        assert chunk in original_content

    print("✅ Non-streaming query references verified")


if __name__ == "__main__":
    pytest.main([__file__, "-s", "--run-integration"])
