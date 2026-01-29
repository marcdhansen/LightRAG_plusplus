import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

# Paths
ROOT_DIR = Path(__file__).parent.parent
EVAL_SCRIPT = ROOT_DIR / "lightrag" / "evaluation" / "eval_rag_quality.py"
SAMPLE_DOCS_DIR = ROOT_DIR / "lightrag" / "evaluation" / "sample_documents"
BASE_URL = "http://localhost:9621"


@pytest.fixture(scope="function")
async def index_sample_documents():
    """Index sample documents before running evaluations."""
    print("\n📥 Indexing sample documents for evaluation...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Check if already indexed or if we should just force it
        # The fixture in conftest.py wipes storage, so we MUST index

        docs = list(SAMPLE_DOCS_DIR.glob("*.md"))
        if not docs:
            pytest.fail(f"No sample documents found in {SAMPLE_DOCS_DIR}")

        for doc_path in docs:
            if doc_path.name == "README.md":
                continue
            with open(doc_path) as f:
                content = f.read()

            resp = await client.post(
                f"{BASE_URL}/documents/text",
                json={"text": content, "file_source": doc_path.name},
            )
            assert (
                resp.status_code == 200
            ), f"Failed to index {doc_path.name}: {resp.text}"
            print(f"   ✅ Indexed {doc_path.name}")

    # Give some time for processing (though ainsert is async on server side,
    # the /upload endpoint in LightRAG usually waits for insertion or at least starts it)
    print("   ⏳ Waiting for graph processing...")
    time.sleep(5)


@pytest.mark.integration
@pytest.mark.requires_api
@pytest.mark.usefixtures("index_sample_documents")
class TestRagasQuality:
    """
    Tiered testing for RAGAS evaluation.

    Light Path: Quick verification of the evaluation pipeline (limit 1).
    Heavy Path: Full evaluation of the system benchmarks.
    """

    @pytest.mark.light
    def test_ragas_light(self):
        """
        Verify RAGAS pipeline is functional with a single test case.
        This confirms Langfuse integration and Judge LLM connectivity.
        """
        print("\n🚀 Running Light RAGAS Evaluation (limit=1)...")

        cmd = [sys.executable, str(EVAL_SCRIPT), "--limit", "1"]

        # Use a more robust subprocess call to ensure output is captured
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(ROOT_DIR),
        )

        stdout_lines = []
        for line in process.stdout:
            print(line, end="")
            stdout_lines.append(line)

        process.wait()
        full_output = "".join(stdout_lines)

        if process.returncode != 0:
            print(f"\n❌ RAGAS Light failed with exit code {process.returncode}")
            pytest.fail("RAGAS Light evaluation script failed")

        assert "EVALUATION COMPLETE" in full_output
        assert "Successful:     1" in full_output

    @pytest.mark.heavy
    @pytest.mark.benchmark
    def test_ragas_heavy(self):
        """
        Run full RAGAS evaluation on the standard sample dataset.
        This takes several minutes and provides a comprehensive quality score.
        """
        print("\n🚀 Running Heavy RAGAS Evaluation (full dataset)...")

        cmd = [sys.executable, str(EVAL_SCRIPT)]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(ROOT_DIR),
        )

        stdout_lines = []
        for line in process.stdout:
            print(line, end="")
            stdout_lines.append(line)

        process.wait()
        full_output = "".join(stdout_lines)

        if process.returncode != 0:
            print(f"\n❌ RAGAS Heavy failed with exit code {process.returncode}")
            pytest.fail("RAGAS Heavy evaluation script failed")

        assert "EVALUATION COMPLETE" in full_output
        assert "Failed:         0" in full_output
