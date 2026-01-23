import asyncio
import httpx
import os
import sys
import time
import pytest

pytestmark = pytest.mark.heavy

# Configuration
BASE_URL = "http://localhost:9621"
TEST_DOCS_DIR = "test_documents"
POLL_INTERVAL = 2  # seconds
MAX_RETRIES = 600  # 600 * 2 = 1200 seconds = 20 minutes max wait per file

async def upload_and_process_file(client, file_path):
    filename = os.path.basename(file_path)
    print(f"\n--- Processing: {filename} ({os.path.getsize(file_path)} bytes) ---")
    
    # 1. Upload
    print(f"Uploading {filename}...")
    try:
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "application/octet-stream")}
            response = await client.post(f"{BASE_URL}/documents/upload", files=files)
            
        if response.status_code != 200:
            print(f"Error: Upload failed with status {response.status_code}: {response.text}")
            return False
            
        data = response.json()
        track_id = data.get("track_id")
        
        if not track_id:
            # Handle duplicate or immediate error case if API returns different structure
            print(f"Warning: No track_id returned. Response: {data}")
            if data.get("status") == "duplicated":
                 print(f"Skipping duplicate file: {filename}")
                 return True
            return False

        print(f"Upload successful. Track ID: {track_id}")
        
    except Exception as e:
        print(f"Exception during upload: {e}")
        return False

    # 2. Poll Status
    print("Waiting for processing...")
    start_time = time.time()
    
    for i in range(MAX_RETRIES):
        try:
            status_resp = await client.get(f"{BASE_URL}/documents/track_status/{track_id}")
            if status_resp.status_code != 200:
                print(f"Error fetching status: {status_resp.status_code}")
                await asyncio.sleep(POLL_INTERVAL)
                continue
                
            status_data = status_resp.json()
            documents = status_data.get("documents", [])
            
            if not documents:
                # Should not happen if upload was successful
                print("No documents found in track status.")
                await asyncio.sleep(POLL_INTERVAL)
                continue

            # Check aggregate status
            all_processed = True
            any_failed = False
            failed_docs = []
            
            processed_count = 0
            pending_count = 0
            
            for doc in documents:
                status = doc.get("status")
                if status == "processed":
                    processed_count += 1
                elif status == "failed":
                    any_failed = True
                    failed_docs.append(doc.get("file_path", "unknown"))
                    all_processed = False
                else:
                    pending_count += 1
                    all_processed = False
            
            elapsed = time.time() - start_time
            sys.stdout.write(f"\rStatus: {processed_count}/{len(documents)} processed, {pending_count} pending (Elapsed: {elapsed:.1f}s)")
            sys.stdout.flush()
            
            if any_failed:
                print(f"\nFAILURE: The following documents failed: {', '.join(failed_docs)}")
                return False
                
            if all_processed:
                print(f"\nSUCCESS: {filename} processed successfully.")
                return True
                
            await asyncio.sleep(POLL_INTERVAL)
            
        except Exception as e:
            print(f"\nException during polling: {e}")
            return False

    print(f"\nTimeout waiting for {filename}")
    return False



@pytest.mark.asyncio
@pytest.mark.integration
async def test_fail_fast_integration():
    if not os.path.exists(TEST_DOCS_DIR):
        print(f"Error: Directory '{TEST_DOCS_DIR}' not found.")
        # Skip checking for exit code, just assert
        assert False, f"Directory '{TEST_DOCS_DIR}' not found."

    # 1. Collect and Sort Files
    files = []
    for f in os.listdir(TEST_DOCS_DIR):
        full_path = os.path.join(TEST_DOCS_DIR, f)
        if os.path.isfile(full_path) and not f.startswith('.'):
            files.append((full_path, os.path.getsize(full_path)))
    
    # Sort by size (ascending) -> Fail Fast approach
    files.sort(key=lambda x: x[1])
    
    if not files:
        print("No files found to test.")
        return

    print(f"Found {len(files)} files. Sorted by size:")
    for path, size in files:
        print(f" - {os.path.basename(path)}: {size} bytes")

    # 2. Process Sequentially
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Check server health first
        try:
            resp = await client.get(f"{BASE_URL}/auth-status")
            if resp.status_code != 200:
                assert False, "Server is not healthy or accessible."
        except Exception:
            assert False, "Cannot connect to server. Is it running?"

        for path, size in files:
            success = await upload_and_process_file(client, path)
            assert success, f"Processing failed for {path}"
    
    print("\nAll documents processed successfully!")

