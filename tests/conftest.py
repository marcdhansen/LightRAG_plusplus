"""
Pytest configuration for LightRAG tests.

This file provides command-line options and fixtures for test configuration.
"""

import importlib
import os
import sys

import pytest


@pytest.fixture(autouse=True)
def reset_shared_storage_locks():
    """
    Reset shared storage locks to prevent asyncio loop mismatch errors.
    This fixture runs for every test to ensure clean state.
    """
    try:
        import lightrag.kg.shared_storage as shared_storage

        if shared_storage._storage_keyed_lock:
            # Clear internal async lock cache as they are bound to specific event loops
            shared_storage._storage_keyed_lock._async_lock.clear()
            shared_storage._storage_keyed_lock._async_lock_count.clear()
            shared_storage._storage_keyed_lock._async_lock_cleanup_data.clear()

            # Reset cleanup timers
            shared_storage._storage_keyed_lock._earliest_async_cleanup_time = None
            shared_storage._storage_keyed_lock._last_async_cleanup_time = None
    except ImportError:
        pass  # Module might not be importable in some contexts, skip


@pytest.fixture
async def storage():
    """
    Fixture to initialize and yield a graph storage instance.
    This fixture ensures clean setup and teardown for graph tests.
    """
    from lightrag.kg import STORAGES
    from lightrag.kg.shared_storage import initialize_share_data

    # Use NetworkX as default for tests if not specified
    graph_storage_type = os.getenv("LIGHTRAG_GRAPH_STORAGE", "NetworkXStorage")

    # Initialize shared data (locks)
    initialize_share_data()

    # Dynamically import storage class
    module_path = STORAGES.get(graph_storage_type)
    if not module_path:
        pytest.skip(f"Unknown storage type: {graph_storage_type}")

    try:
        module = importlib.import_module(module_path, package="lightrag")
        storage_class = getattr(module, graph_storage_type)
    except (ImportError, AttributeError) as e:
        pytest.skip(f"Failed to import {graph_storage_type}: {e}")

    # Mock embedding func
    async def mock_embedding_func(texts):
        import numpy as np

        return np.random.rand(len(texts), 10)

    global_config = {
        "embedding_batch_num": 10,
        "vector_db_storage_cls_kwargs": {"cosine_better_than_threshold": 0.5},
        "working_dir": "./test_rag_storage",
    }

    storage_instance = storage_class(
        namespace="test_graph",
        workspace="test_workspace",
        global_config=global_config,
        embedding_func=mock_embedding_func,
    )

    await storage_instance.initialize()
    yield storage_instance

    # Cleanup (if supported by storage)
    if hasattr(storage_instance, "drop"):
        await storage_instance.drop()


def pytest_configure(config):
    """Register custom markers for LightRAG tests."""
    config.addinivalue_line(
        "markers", "offline: marks tests as offline (no external dependencies)"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests requiring external services (skipped by default)",
    )
    config.addinivalue_line("markers", "requires_db: marks tests requiring database")
    config.addinivalue_line(
        "markers", "requires_api: marks tests requiring LightRAG API server"
    )
    config.addinivalue_line(
        "markers", "manual: marks tests intended for manual/interactive execution"
    )
    config.addinivalue_line(
        "markers", "light: marks tests as part of the light path (quick verification)"
    )
    config.addinivalue_line(
        "markers",
        "heavy: marks tests as part of the heavy path (benchmarks, full eval)",
    )


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add a prominent LightRAG-specific summary to the terminal output."""
    stats = terminalreporter.stats
    passed = len(stats.get("passed", []))
    failed = len(stats.get("failed", []))
    error = len(stats.get("error", []))
    skipped = len(stats.get("skipped", []))
    total = passed + failed + error + skipped

    # Determine suite name for header
    is_integration = config.getoption("--run-integration")
    is_manual = config.getoption("--run-manual")
    markexpr = config.getoption("markexpr")

    suite_label = "INTEGRATION"  # Default
    if "offline" in markexpr.lower():
        suite_label = "OFFLINE"
    elif "light" in markexpr.lower():
        suite_label = "LIGHT"
    elif "heavy" in markexpr.lower():
        suite_label = "HEAVY"
    elif is_integration and is_manual:
        suite_label = "FULL"
    elif is_manual and not is_integration:
        suite_label = "MANUAL"
    elif not is_integration and not is_manual and not markexpr:
        suite_label = "DEFAULT"

    terminalreporter.ensure_newline()
    terminalreporter.section(f"LightRAG {suite_label} TEST SUMMARY", sep="=", bold=True)

    if total == 0:
        terminalreporter.write_line("No tests were executed.")
        return

    # Helper for colored output
    def write_stat(label, count, color_if_gt=None):
        if count > 0 and color_if_gt:
            terminalreporter.write(f"{label}: ", bold=True)
            terminalreporter.write_line(f"{count}", **{color_if_gt: True, "bold": True})
        else:
            terminalreporter.write_line(f"{label}: {count}")

    write_stat(f"TOTAL {suite_label} SUITE", total)
    write_stat("✅ PASSED", passed, "green" if passed > 0 else None)
    write_stat("❌ FAILED", failed, "red" if failed > 0 else None)
    write_stat("⚠️  ERRORS", error, "red" if error > 0 else None)
    write_stat("⏭️  SKIPPED", skipped, "yellow" if skipped > 0 else None)

    terminalreporter.write_line("-" * 30)
    if exitstatus == 0:
        terminalreporter.write_line("OVERALL STATUS: SUCCESS 🚀", green=True, bold=True)
    else:
        terminalreporter.write_line("OVERALL STATUS: FAILURE 🚨", red=True, bold=True)
    terminalreporter.ensure_newline()


def pytest_addoption(parser):
    """Add custom command-line options for LightRAG tests."""

    parser.addoption(
        "--keep-artifacts",
        action="store_true",
        default=False,
        help="Keep test artifacts (temporary directories and files) after test completion for inspection",
    )

    parser.addoption(
        "--stress-test",
        action="store_true",
        default=False,
        help="Enable stress test mode with more intensive workloads",
    )

    parser.addoption(
        "--test-workers",
        action="store",
        default=3,
        type=int,
        help="Number of parallel workers for stress tests (default: 3)",
    )

    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require external services (database, API server, etc.)",
    )
    parser.addoption(
        "--run-manual",
        action="store_true",
        default=False,
        help="Run manual tests that require human interaction or specific environment state",
    )
    parser.addoption(
        "--run-heavy",
        action="store_true",
        default=False,
        help="Run heavy tests (benchmarks, full evaluations) that take a long time",
    )
    parser.addoption(
        "--run-light",
        action="store_true",
        default=False,
        help="Run only light path tests for quick verification",
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip integration tests by default.

    Integration tests are skipped unless --run-integration flag is provided.
    This allows running offline tests quickly without needing external services.
    """
    skip_integration = pytest.mark.skip(
        reason="Requires external services(DB/API), use --run-integration to run"
    )
    skip_manual = pytest.mark.skip(reason="Manual test, use --run-manual to run")
    skip_heavy = pytest.mark.skip(reason="Heavy/slow test, use --run-heavy to run")
    skip_light = pytest.mark.skip(reason="Not a light test, use --run-light to exclude")

    for item in items:
        if "integration" in item.keywords and not config.getoption("--run-integration"):
            item.add_marker(skip_integration)
        if "manual" in item.keywords and not config.getoption("--run-manual"):
            item.add_marker(skip_manual)
        if "heavy" in item.keywords and not config.getoption("--run-heavy"):
            item.add_marker(skip_heavy)
        if config.getoption("--run-light") and "light" not in item.keywords:
            item.add_marker(skip_light)


@pytest.fixture(scope="session")
def keep_test_artifacts(request):
    """
    Fixture to determine whether to keep test artifacts.

    Priority: CLI option > Environment variable > Default (False)
    """

    # Check CLI option first
    if request.config.getoption("--keep-artifacts"):
        return True

    # Fall back to environment variable
    return os.getenv("LIGHTRAG_KEEP_ARTIFACTS", "false").lower() == "true"


@pytest.fixture(scope="session")
def stress_test_mode(request):
    """
    Fixture to determine whether stress test mode is enabled.

    Priority: CLI option > Environment variable > Default (False)
    """

    # Check CLI option first
    if request.config.getoption("--stress-test"):
        return True

    # Fall back to environment variable
    return os.getenv("LIGHTRAG_STRESS_TEST", "false").lower() == "true"


@pytest.fixture(scope="session")
def parallel_workers(request):
    """
    Fixture to determine the number of parallel workers for stress tests.

    Priority: CLI option > Environment variable > Default (3)
    """

    # Check CLI option first
    cli_workers = request.config.getoption("--test-workers")
    if cli_workers != 3:  # Non-default value provided
        return cli_workers

    # Fall back to environment variable
    return int(os.getenv("LIGHTRAG_TEST_WORKERS", "3"))


@pytest.fixture(scope="session")
def run_integration_tests(request):
    """
    Fixture to determine whether to run integration tests.

    Priority: CLI option > Environment variable > Default (False)
    """

    # Check CLI option first
    if request.config.getoption("--run-integration"):
        return True

    # Fall back to environment variable
    return os.getenv("LIGHTRAG_RUN_INTEGRATION", "false").lower() == "true"


@pytest.fixture(scope="session", autouse=True)
def check_external_services(request):
    """
    Fixture to check and start external services (Docker, LightRAG server)
    if integration tests are running.

    This fixture runs automatically if --run-integration is set.
    """
    should_run = request.config.getoption("--run-integration")
    # Also check env var to be consistent with run_integration_tests fixture
    # (We duplicate logic slightly to avoid circular deps or complex fixture requests if not needed)
    if not should_run:
        import os

        should_run = os.getenv("LIGHTRAG_RUN_INTEGRATION", "false").lower() == "true"

    if not should_run:
        return

    import os
    import subprocess
    import time
    import urllib.error
    import urllib.request

    print("\n[Fixture] Checking external services for integration tests...")

    # --- 1. Docker Check ---
    print("[Fixture] Checking Docker...")
    docker_running = False
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        docker_running = True
        print("[Fixture] Docker is running.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[Fixture] Docker is NOT running.")

    if not docker_running:
        if sys.platform == "darwin":
            print("[Fixture] Attempting to start Docker Desktop...")
            try:
                subprocess.run(["open", "-a", "Docker"], check=True)
                # Wait for Docker to initialize
                print("[Fixture] Waiting for Docker to start (up to 60s)...")
                for i in range(12):  # 12 * 5s = 60s
                    time.sleep(5)
                    try:
                        subprocess.run(
                            ["docker", "info"],
                            check=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        print("[Fixture] Docker started successfully.")
                        docker_running = True
                        break
                    except subprocess.CalledProcessError:
                        print(f"  ... waiting ({i + 1}/12)")
            except Exception as e:
                print(f"[Fixture] Failed to launch Docker: {e}")
        else:
            print(
                "[Fixture] Auto-start for Docker is only implemented for macOS. Please start Docker manually."
            )

    if not docker_running:
        print(
            "[Fixture] WARNING: Docker is not running. Tests requiring Memgraph/Redis/Postgres may fail."
        )
        # We don't exit here because some integration tests might just need the server, not new docker containers if they are mocked or external.
        # But usually 'requires_db' implies docker.

    # --- 1.5 Postgres Check ---
    # Since we are using docker-compose, we can check/start the whole stack or just postgres
    if docker_running:
        print("[Fixture] Checking Postgres container...")
        try:
            # Check if container exists and is running
            subprocess.run(
                ["docker", "container", "inspect", "lightrag-postgres"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print("[Fixture] Postgres container 'lightrag-postgres' is running.")
        except subprocess.CalledProcessError:
            print(
                "[Fixture] Postgres container not found or not running. Attempting to start via docker-compose..."
            )
            try:
                subprocess.run(
                    ["docker", "compose", "up", "-d", "postgres"], check=True
                )
                print(
                    "[Fixture] Postgres started. Waiting for health check (pg_isready)..."
                )
                # Wait loop for health
                for i in range(12):
                    res = subprocess.run(
                        [
                            "docker",
                            "exec",
                            "lightrag-postgres",
                            "pg_isready",
                            "-U",
                            "postgres",
                        ],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    if res.returncode == 0:
                        print("[Fixture] Postgres is ready!")
                        break
                    time.sleep(2.5)
            except Exception as e:
                print(f"[Fixture] Failed to start Postgres: {e}")

    # --- 2. Server Check ---
    server_url = "http://localhost:9621/health"
    server_running = False
    print(f"[Fixture] Checking LightRAG Server at {server_url}...")

    try:
        with urllib.request.urlopen(server_url, timeout=1) as response:
            if response.status == 200:
                server_running = True
                print("[Fixture] Server is running.")
    except (TimeoutError, urllib.error.URLError, ConnectionRefusedError):
        print("[Fixture] Server is NOT reachable.")

    if not server_running:
        print("[Fixture] Attempting to start LightRAG Server...")
        # Assume we are in the root or can find the right path.
        # The command: uv run lightrag-server
        # We need to run this in the background and ensure it stays alive during session

        try:
            # Determine CWD: The tests are likely running from root or LightRAG/
            # If running `uv run pytest Tests/` from root, CWD is root.
            # `lightrag-server` script assumes it can find 'lightrag' module.
            # We use `uv run lightrag-server` which should handle environment.

            # --- CLEANUP: Wipe storage directory before starting server for a fresh test run ---
            # This ensures no corrupted state from previous runs interferes with tests.
            # We only do this if we are auto-starting the server (implying a test-controlled environment).
            working_dir = os.getenv("WORKING_DIR", "./rag_storage")
            if os.path.exists(working_dir):
                import shutil

                print(f"[Fixture] Cleaning up storage directory: {working_dir}")
                try:
                    shutil.rmtree(working_dir)
                    print("[Fixture] Storage directory wiped.")
                except Exception as e:
                    print(f"[Fixture] Warning: Failed to wipe storage directory: {e}")

            # Start process
            # process = subprocess.Popen(["uv", "run", "lightrag-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Better to show output? Or log to file?

            # We'll use a log file for the server output to avoid cluttering test output
            with open("testing_server_autostart.log", "w") as log_file:
                server_process = subprocess.Popen(
                    ["uv", "run", "lightrag-server"],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,  # Detach slightly so it doesn't get killed instantly (though we want to kill it at end?)
                )

            print(
                f"[Fixture] Server process started (PID: {server_process.pid}). Waiting for health check..."
            )

            # Register cleanup to kill server at end of session
            def cleanup_server():
                print(
                    f"\n[Fixture] Stopping auto-started server (PID: {server_process.pid})..."
                )
                server_process.terminate()
                try:
                    server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_process.kill()
                print("[Fixture] Server stopped.")

            request.addfinalizer(cleanup_server)

            # Wait for healthy
            start_time = time.time()
            while time.time() - start_time < 120:  # 120s timeout
                try:
                    with urllib.request.urlopen(server_url, timeout=1) as response:
                        if response.status == 200:
                            server_running = True
                            print(
                                f"[Fixture] Server is up and healthy! (Took {time.time() - start_time:.1f}s)"
                            )

                            # --- 3. Remote Cleanup ---
                            # Now that server is healthy, trigger a full data wipe to ensure clean test state
                            # This clears everything (Graph, Vector, KV) via the new endpoint
                            print(
                                "[Fixture] Triggering remote data wipe for clean test state..."
                            )
                            try:
                                # We use a POST request to /clear_all_data
                                # Since we don't have 'requests' library guaranteed, use urllib
                                clear_url = "http://localhost:9621/clear_all_data"
                                req = urllib.request.Request(clear_url, method="POST")
                                # If API key is set in env, we must include it
                                api_key = os.getenv("LIGHTRAG_API_KEY")
                                if api_key:
                                    req.add_header("Authorization", f"Bearer {api_key}")

                                with urllib.request.urlopen(
                                    req, timeout=10
                                ) as clear_resp:
                                    if clear_resp.status == 200:
                                        print("[Fixture] Remote data wipe successful.")
                                    else:
                                        print(
                                            f"[Fixture] Warning: Remote data wipe returned status {clear_resp.status}"
                                        )
                            except Exception as e:
                                print(
                                    f"[Fixture] Warning: Failed to trigger remote data wipe: {e}"
                                )

                            break
                except (TimeoutError, urllib.error.URLError, ConnectionRefusedError):
                    time.sleep(1)

            if not server_running:
                print(
                    "[Fixture] ERROR: Server failed to start within 30s. Check 'testing_server_autostart.log' for details."
                )
                # We might want to fail the session here if the server is mandatory for integration tests
                pytest.fail("Auto-started server failed health check.")

        except Exception as e:
            print(f"[Fixture] Failed to start server: {e}")
            pytest.fail(f"Could not auto-start server: {e}")

    # Explicitly verify we made it
    print("[Fixture] Environment check complete.\n")
