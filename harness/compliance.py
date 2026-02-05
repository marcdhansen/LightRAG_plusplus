import subprocess
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class ContextCheck(BaseModel):
    roadmap_exists: bool
    implementation_plan_exists: bool
    missing_docs: list[str] = Field(default_factory=list)


class ApprovalCheck(BaseModel):
    approved: bool
    timestamp: str | None = None
    age_hours: float = 0.0
    stale: bool = False


def check_planning_docs(project_root: Path) -> ContextCheck:
    # Try multiple common locations
    roadmap_locations = [
        project_root / ".agent/rules/ROADMAP.md",
        project_root / ".agent/ROADMAP.md",
        project_root / "ROADMAP.md",
    ]
    impl_locations = [
        project_root / ".agent/rules/ImplementationPlan.md",
        project_root / ".agent/ImplementationPlan.md",
        project_root / "ImplementationPlan.md",
    ]

    roadmap_exists = any(p.exists() for p in roadmap_locations)
    impl_exists = any(p.exists() for p in impl_locations)

    missing = []
    if not roadmap_exists:
        missing.append("ROADMAP.md")
    if not impl_exists:
        missing.append("ImplementationPlan.md")

    return ContextCheck(
        roadmap_exists=roadmap_exists,
        implementation_plan_exists=impl_exists,
        missing_docs=missing,
    )


def check_approval(max_hours: int = 4) -> ApprovalCheck:
    task_paths = [Path(".agent/task.md"), Path("task.md")]

    # Check brain directory (most recent)
    brain_dir = Path.home() / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        session_dirs = sorted(
            [d for d in brain_dir.iterdir() if d.is_dir()],
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )[:3]
        for d in session_dirs:
            task_paths.append(d / "task.md")

    for path in task_paths:
        if path.exists():
            content = path.read_text()
            if (
                "## Approval" in content
                or "👍 APPROVED" in content
                or "[x]" in content.lower()
            ):
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
                age = (datetime.now() - mtime).total_seconds() / 3600
                return ApprovalCheck(
                    approved=True,
                    timestamp=mtime.isoformat(),
                    age_hours=age,
                    stale=age > max_hours,
                )
    return ApprovalCheck(approved=False)


def check_beads_available() -> bool:
    try:
        subprocess.run(["bd", "--version"], capture_output=True, check=True)
        return True
    except Exception:
        return False
