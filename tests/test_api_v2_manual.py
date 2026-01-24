import pytest

pytestmark = pytest.mark.heavy
import httpx
import time

# Configuration
TIMEOUT = 300  # 5 minutes specifically for indexing
BASE_URL = "http://localhost:9621"
API_KEY = "your-secure-api-key-here-123"  # Mock key or from env


@pytest.fixture(scope="function")
def uploaded_document():
    """
    Fixture to upload a sample document, wait for processing, yield its ID, and clean up.
    """
    filename = "test_manual_lifecycle_pytest.txt"
    content = "LightRAG is a robust Retrieval-Augmented Generation system using knowledge graphs."

    upload_url = f"{BASE_URL}/documents/upload"
    track_url_template = f"{BASE_URL}/documents/track_status/{{}}"
    delete_url = f"{BASE_URL}/documents/delete_document"

    headers = {"X-API-Key": API_KEY}

    print(f"\n[Fixture] Uploading {filename}...")
    try:
        # Create a temporary file-like object for upload
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
                doc_status = docs[
                    0
                ]  # Assuming single file upload results in single doc entry (or first one)
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

    yield doc_id

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


@pytest.mark.integration
@pytest.mark.requires_api
def test_full_lifecycle_manual(uploaded_document):
    """
    Test the full lifecycle: Upload -> Index -> Query -> cleanup(fixture).
    """
    doc_id = uploaded_document
    assert doc_id is not None, "Document ID should not be None"

    query_url = f"{BASE_URL}/query/data"
    headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}

    # Query for the content we just uploaded
    payload = {"query": "What is LightRAG?", "mode": "mix", "top_k": 5}

    print("\n🚀 Sending query request...")
    try:
        response = httpx.post(query_url, headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()
        data = response.json()

        print(f"✅ Received response status: {data.get('status')}")
        assert data["status"] == "success"

        # Verify our content is potentially found (optional, requires extraction validity)
        # For now, just validating structure as the original test did
        inner_data = data["data"]
        assert "entities" in inner_data
        assert "relationships" in inner_data
        assert "chunks" in inner_data

        # We can check if chunks contain our text

        # This might be empty if the text was too short or extraction failed to produce chunks?
        # "LightRAG is a robust Retrieval-Augmented Generation system using knowledge graphs."
        # It's short. Logic might vary.
        # But we assert response format correctness.

    except Exception as e:
        pytest.fail(f"Query failed: {e}")


if __name__ == "__main__":
    # Allow simple execution
    pytest.main([__file__, "-s", "--run-integration", "--run-manual"])
