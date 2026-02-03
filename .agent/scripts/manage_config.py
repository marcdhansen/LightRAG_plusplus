#!/usr/bin/env python3

"""
Centralized Configuration Management System
Provides unified configuration management across agent environments
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ConfigItem:
    """Single configuration item"""

    key: str
    value: Any
    source: str  # 'global', 'project', 'user', 'default'
    description: str
    category: str
    last_modified: str | None = None


class ConfigManager:
    """Centralized configuration management system"""

    def __init__(self):
        self.agent_global = Path.home() / ".agent"
        self.project_agent = Path(".agent")
        self.user_config = Path.home() / ".gemini"

        # Configuration sources in priority order
        self.sources = [
            ("default", "Built-in defaults"),
            ("global", "Universal agent configuration"),
            ("project", "Project-specific configuration"),
            ("user", "User-specific overrides"),
        ]

        self.config: dict[str, ConfigItem] = {}

    def load_all_configs(self) -> dict[str, ConfigItem]:
        """Load all configuration from all sources"""
        print("🔧 Loading configuration from all sources...")

        self.config.clear()

        # Load in priority order (defaults first, user overrides last)
        for source_name, description in self.sources:
            self._load_from_source(source_name, description)

        print(f"📊 Loaded {len(self.config)} configuration items")
        return self.config

    def _load_from_source(self, source: str, description: str):
        """Load configuration from specific source"""
        print(f"   Loading from {description}...")

        if source == "default":
            self._load_defaults()
        elif source == "global":
            self._load_global_config()
        elif source == "project":
            self._load_project_config()
        elif source == "user":
            self._load_user_config()

    def _load_defaults(self):
        """Load built-in default configurations"""
        defaults = {
            "symlink_validation.enabled": ConfigItem(
                key="symlink_validation.enabled",
                value=True,
                source="default",
                description="Enable automated symlink validation",
                category="validation",
            ),
            "skill_discovery.cache_seconds": ConfigItem(
                key="skill_discovery.cache_seconds",
                value=300,
                source="default",
                description="Skill discovery cache duration",
                category="performance",
            ),
            "version_check.interval_hours": ConfigItem(
                key="version_check.interval_hours",
                value=24,
                source="default",
                description="Version consistency check interval",
                category="maintenance",
            ),
        }

        self.config.update(defaults)

    def _load_global_config(self):
        """Load global configuration from ~/.agent/config/"""
        config_dir = self.agent_global / "config"
        if not config_dir.exists():
            return

        config_file = config_dir / "agent.yaml"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    data = yaml.safe_load(f) or {}

                for key, value in data.items():
                    if key not in self.config:  # Respect priority order
                        self.config[key] = ConfigItem(
                            key=key,
                            value=value,
                            source="global",
                            description=f"Global config: {key}",
                            category="imported",
                        )

            except Exception as e:
                print(f"   ⚠️  Error loading global config: {e}")

    def _load_project_config(self):
        """Load project-specific configuration"""
        config_file = self.project_agent / "config" / "project.yaml"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    data = yaml.safe_load(f) or {}

                for key, value in data.items():
                    if key not in self.config:
                        self.config[key] = ConfigItem(
                            key=key,
                            value=value,
                            source="project",
                            description=f"Project config: {key}",
                            category="imported",
                        )

            except Exception as e:
                print(f"   ⚠️  Error loading project config: {e}")

    def _load_user_config(self):
        """Load user-specific configuration"""
        config_file = self.user_config / "agent.yaml"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    data = yaml.safe_load(f) or {}

                for key, value in data.items():
                    # User config overrides everything
                    self.config[key] = ConfigItem(
                        key=key,
                        value=value,
                        source="user",
                        description=f"User override: {key}",
                        category="override",
                    )

            except Exception as e:
                print(f"   ⚠️  Error loading user config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        if key in self.config:
            return self.config[key].value
        return default

    def set(self, key: str, value: Any, source: str = "runtime", description: str = ""):
        """Set configuration value"""
        self.config[key] = ConfigItem(
            key=key,
            value=value,
            source=source,
            description=description,
            category="runtime",
            last_modified=datetime.now().isoformat(),
        )

    def save_user_config(self, key: str, value: Any):
        """Save configuration to user overrides"""
        config_dir = self.user_config
        config_dir = config_dir / "config"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "agent.yaml"

        # Load existing config
        existing = {}
        if config_file.exists():
            try:
                with open(config_file) as f:
                    existing = yaml.safe_load(f) or {}
            except Exception:
                existing = {}

        # Update with new value
        existing[key] = value

        # Save back
        try:
            with open(config_file, "w") as f:
                yaml.dump(existing, f, default_flow_style=False)

            print(f"💾 Saved user config: {key} = {value}")

        except Exception as e:
            print(f"   ❌ Error saving user config: {e}")

    def get_source(self, key: str) -> str:
        """Get the source of a configuration value"""
        return self.config.get(
            key, ConfigItem(key, "", "default", "default", "")
        ).source

    def list_by_category(self, category: str) -> list[ConfigItem]:
        """List all configuration items in a category"""
        return [item for item in self.config.values() if item.category == category]

    def list_by_source(self, source: str) -> list[ConfigItem]:
        """List all configuration items from a source"""
        return [item for item in self.config.values() if item.source == source]

    def validate_dependencies(self) -> list[str]:
        """Validate that all required configurations are present"""
        print("🔍 Validating configuration dependencies...")

        # Check for required directories and files
        required = [
            (self.agent_global / "skills", "Global skills directory"),
            (self.agent_global / "rules", "Global rules directory"),
            (self.project_agent, "Project directory exists"),
        ]

        missing = []
        for path, description in required:
            if not path.exists():
                missing.append(f"{description}: {path}")

        if missing:
            print("❌ Missing required items:")
            for item in missing:
                print(f"   {item}")
        else:
            print("✅ All configuration dependencies satisfied")

        return missing

    def generate_config_file(self, output_path: Path):
        """Generate merged configuration file"""
        config_data = {
            "generated_at": datetime.now().isoformat(),
            "sources_used": [
                source
                for source, _ in self.sources
                if any(item.source == source for item in self.config.values())
            ],
            "total_items": len(self.config),
            "configuration": {},
        }

        for key, item in self.config.items():
            config_data["configuration"][key] = {
                "value": item.value,
                "source": item.source,
                "description": item.description,
                "category": item.category,
            }

        with open(output_path, "w") as f:
            json.dump(config_data, f, indent=2)

        print(f"📝 Generated configuration file: {output_path}")


def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Centralized Configuration Management")
    parser.add_argument("--load", action="store_true", help="Load all configurations")
    parser.add_argument("--get", help="Get specific configuration value")
    parser.add_argument(
        "--set", nargs=2, metavar=("KEY", "VALUE"), help="Set configuration value"
    )
    parser.add_argument(
        "--save", nargs=2, metavar=("KEY", "VALUE"), help="Save to user config"
    )
    parser.add_argument("--list-category", help="List configurations by category")
    parser.add_argument(
        "--validate", action="store_true", help="Validate configuration dependencies"
    )
    parser.add_argument("--generate", help="Generate merged configuration file")

    args = parser.parse_args()

    manager = ConfigManager()

    if args.load:
        manager.load_all_configs()
        manager.print_summary()

    elif args.get:
        manager.load_all_configs()
        value = manager.get(args.get)
        source = manager.get_source(args.get)
        print(f"{args.get} = {value} (source: {source})")

    elif args.set:
        key, value = args.set
        manager.load_all_configs()  # Load existing first
        manager.set(key, value, "runtime", f"Command line set: {key}")
        print(f"Set {key} = {value}")

    elif args.save:
        key, value = args.save
        manager.save_user_config(key, value)

    elif args.list_category:
        manager.load_all_configs()
        items = manager.list_by_category(args.list_category)
        for item in items:
            source_marker = {
                "global": "🌐",
                "project": "🏢",
                "user": "👤",
                "default": "⚙️",
                "runtime": "🔧",
            }.get(item.source, "❓")

            print(f"  {source_marker} {item.key} = {item.value} ({item.source})")

    elif args.validate:
        missing = manager.validate_dependencies()
        if missing:
            exit(1)

    elif args.generate:
        manager.load_all_configs()
        manager.generate_config_file(Path(args.generate))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
