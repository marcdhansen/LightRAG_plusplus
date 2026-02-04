import json
import subprocess
import sys
from typing import Any


class TaskAnalyzer:
    def __init__(self, limit: int = 0):
        self.limit = limit

    def get_ready_tasks(self) -> list[dict[str, Any]]:
        """Fetch ready tasks from Beads in JSON format."""
        cmd = ["bd", "ready", "--json", f"--limit={self.limit}"]
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            return json.loads(output)
        except subprocess.CalledProcessError as e:
            print(f"Error running bd command: {e.output.decode()}", file=sys.stderr)
            return []
        except json.JSONDecodeError:
            print("Error decoding JSON from Beads.", file=sys.stderr)
            return []

    def format_markdown(self) -> str:
        """Format the task list into a clean Markdown representation."""
        tasks = self.get_ready_tasks()
        if not tasks:
            return "No ready tasks found."

        # Group by priority
        by_priority = {}
        for task in tasks:
            p = task.get("priority", 4)
            if p not in by_priority:
                by_priority[p] = []
            by_priority[p].append(task)

        output = ["# 🎯 LightRAG: Ready Tasks Analysis", ""]

        # Summary counts
        total = len(tasks)
        in_progress_count = sum(1 for t in tasks if t.get("status") == "in_progress")
        output.append(
            f"**Total Ready Issues**: {total} | **In Progress**: {in_progress_count}"
        )
        output.append("")

        for priority in sorted(by_priority.keys()):
            output.append(f"## Priority P{priority}")
            output.append("| ID | Status | Title | Type |")
            output.append("| :--- | :--- | :--- | :--- |")

            for task in by_priority[priority]:
                status = task.get("status", "open")
                if status == "in_progress":
                    status_str = "**IN PROGRESS**"
                else:
                    status_str = status
                tid = task.get("id", "N/A")
                title = task.get("title", "No Title")
                ttype = task.get("issue_type", "task")
                output.append(f"| {tid} | {status_str} | {title} | {ttype} |")
            output.append("")

        return "\n".join(output)


if __name__ == "__main__":
    analyzer = TaskAnalyzer()
    print(analyzer.format_markdown())
