import pytest
import subprocess
import time
import os
import sys


@pytest.fixture(scope="session")
def server_process():
    """Starts the LightRAG server for the duration of the test session."""
    print("\nStarting LightRAG server for UI tests...")

    # Define port
    port = 9622  # Use a different port than default to avoid conflicts

    # Start the server process with NetworkXStorage to avoid Memgraph/Docker dependency for UI tests
    env = os.environ.copy()
    env["LIGHTRAG_GRAPH_STORAGE"] = "NetworkXStorage"

    process = subprocess.Popen(
        [sys.executable, "-m", "lightrag.api.lightrag_server", "--port", str(port)],
        cwd=os.path.join(os.path.dirname(__file__), "../../"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    # Wait for server to be ready (poll /health endpoint)
    # We'll use a simple retry loop with curl for this check inside the fixture
    max_retries = 90
    server_ready = False

    for _ in range(max_retries):
        try:
            # Check if port is listening using curl
            result = subprocess.run(
                ["curl", f"http://localhost:{port}/health"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and '"status":"healthy"' in result.stdout:
                server_ready = True
                break
        except Exception:
            pass
        time.sleep(1)

    if not server_ready:
        process.terminate()
        stdout, stderr = process.communicate()
        pytest.fail(
            f"Server failed to start within timeout.\nStdout: {stdout}\nStderr: {stderr}"
        )

    print(f"Server started on port {port}")

    yield f"http://localhost:{port}"

    # Teardown
    print("\nStopping LightRAG server...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
