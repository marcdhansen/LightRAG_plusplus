import json
import logging
import os
from dataclasses import asdict, dataclass, field
from typing import Any

from .config import ACEConfig

logger = logging.getLogger(__name__)


@dataclass
class PlaybookContent:
    core_directives: list[str] = field(default_factory=list)
    strategies: dict[str, str] = field(default_factory=dict)
    lessons_learned: list[str] = field(default_factory=list)

    # Metadata for tracking evolution
    version: int = 1
    last_updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Converts the PlaybookContent instance into a dictionary."""
        return asdict(self)


class ContextPlaybook:
    """
    Manages the persistent state of the agent's context (Playbook).
    This includes directives, strategies, and lessons learned.
    """

    def __init__(self, config: ACEConfig | None = None):
        self.config = config or ACEConfig()
        self.content = PlaybookContent()
        self.config.ensure_base_dir()
        self._load()

    def _load(self):
        """Loads the playbook from disk."""
        path = self.config.get_playbook_full_path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                    # Convert dict back to PlaybookContent dataclass
                    self.content = PlaybookContent(**data)
                logger.info(f"Loaded Context Playbook from {path}")
            except Exception as e:
                logger.error(f"Failed to load playbook: {e}. Starting fresh.")
                self._initialize_defaults()
        else:
            logger.info("No existing playbook found. Initializing defaults.")
            self._initialize_defaults()
            self.save()

    def _initialize_defaults(self):
        """Sets default directives if no existing playbook is found."""
        self.content.core_directives = [
            "Always answer based on the retrieved context.",
            "If the context is insufficient, state what is missing.",
            "Maintain a helpful and professional tone.",
        ]
        self.content.strategies = {
            "query_handling": "Decompose complex queries into sub-questions.",
            "error_recovery": "If extraction fails, fallback to keyword search.",
        }
        self.content.lessons_learned = []
        self.content.version = 1

    def save(self):
        """Persists the current playbook to disk."""
        path = self.config.get_playbook_full_path()
        try:
            with open(path, "w") as f:
                json.dump(asdict(self.content), f, indent=2)
            logger.info(f"Saved Context Playbook to {path}")
        except Exception as e:
            logger.error(f"Failed to save playbook: {e}")

    def render(self) -> str:
        """
        Renders the playbook into a string format suitable for LLM context.
        """
        sections = []

        sections.append("### Core Directives")
        for directive in self.content.core_directives:
            sections.append(f"- {directive}")

        sections.append("\n### Operational Strategies")
        for name, strategy in self.content.strategies.items():
            sections.append(f"- **{name}**: {strategy}")

        if self.content.lessons_learned:
            sections.append("\n### Lessons Learned")
            for lesson in self.content.lessons_learned[
                -self.config.max_history_items :
            ]:
                sections.append(f"- {lesson}")

        return "\n".join(sections)

    def add_lesson(self, lesson: str):
        """Adds a new lesson and saves."""
        if lesson not in self.content.lessons_learned:
            self.content.lessons_learned.append(lesson)
            self.save()

    def update_strategy(self, name: str, description: str):
        """Updates or adds a strategy and saves."""
        self.content.strategies[name] = description
        self.save()
