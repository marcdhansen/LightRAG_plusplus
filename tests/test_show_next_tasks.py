import json
from unittest.mock import patch

# The script we are going to implement
from scripts.show_next_tasks import TaskAnalyzer

MOCK_BEADS_DATA = [
    {
        "id": "lightrag-p0",
        "title": "Critical Bug",
        "status": "open",
        "priority": 0,
        "issue_type": "task",
    },
    {
        "id": "lightrag-1sk",
        "title": "In Progress Task",
        "status": "in_progress",
        "priority": 1,
        "issue_type": "task",
    },
    {
        "id": "lightrag-p2",
        "title": "Feature Request",
        "status": "open",
        "priority": 2,
        "issue_type": "task",
    },
]


def test_task_analyzer_categorization():
    analyzer = TaskAnalyzer()

    with patch("subprocess.check_output") as mock_run:
        mock_run.return_value = json.dumps(MOCK_BEADS_DATA).encode("utf-8")

        ready_tasks = analyzer.get_ready_tasks()

        # Verify Categorization
        assert len(ready_tasks) == 3

        in_progress = [t for t in ready_tasks if t["status"] == "in_progress"]
        assert len(in_progress) == 1
        assert in_progress[0]["id"] == "lightrag-1sk"

        # Verify formatting (example check)
        output = analyzer.format_markdown()
        assert "lightrag-1sk" in output
        assert "IN PROGRESS" in output
        assert "P0" in output
