#!/usr/bin/env python3

"""
Dynamic Skill Discovery System
Automatically discovers and registers skills from multiple sources for cross-agent compatibility
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SkillInfo:
    """Information about a discovered skill"""

    name: str
    path: str
    source: str  # 'global', 'project', 'provider'
    description: str
    version: Optional[str] = None
    dependencies: Optional[List[str]] = None
    skill_type: str = "unknown"  # 'command', 'library', 'workflow'


class SkillDiscovery:
    """Dynamic skill discovery and registry system"""

    def __init__(self):
        self.agent_global = Path.home() / ".agent"
        self.project_agent = Path(".agent")
        self.provider_configs = Path.home() / ".gemini"

        # Initialize registry
        self.registry: Dict[str, SkillInfo] = {}

    def discover_skills(self) -> Dict[str, SkillInfo]:
        """Discover skills from all sources"""
        print("🔍 Discovering skills from multiple sources...")

        # Clear registry
        self.registry.clear()

        # Discover from global ~/.agent/skills/
        self._discover_from_directory(self.agent_global / "skills", "global")

        # Discover from project-local .agent/skills/
        if self.project_agent.exists():
            self._discover_from_directory(self.project_agent / "skills", "project")

        # Discover from provider configs
        self._discover_from_providers()

        print(f"📊 Discovered {len(self.registry)} skills total")
        return self.registry

    def _discover_from_directory(self, skills_dir: Path, source: str):
        """Discover skills from a directory"""
        if not skills_dir.exists():
            return

        for skill_path in skills_dir.iterdir():
            if skill_path.is_dir():
                skill_info = self._parse_skill_directory(skill_path, source)
                if skill_info:
                    self.registry[skill_info.name] = skill_info

    def _parse_skill_directory(
        self, skill_path: Path, source: str
    ) -> Optional[SkillInfo]:
        """Parse a skill directory and extract information"""
        skill_file = skill_path / "SKILL.md"

        if not skill_file.exists():
            print(f"⚠️  No SKILL.md found in {skill_path}")
            return None

        try:
            with open(skill_file, "r") as f:
                content = f.read()

            # Parse YAML frontmatter
            if content.startswith("---"):
                parts = content.split("---")
                if len(parts) >= 3:
                    try:
                        frontmatter = yaml.safe_load(parts[1])
                        return SkillInfo(
                            name=skill_path.name,
                            path=str(skill_path),
                            source=source,
                            description=frontmatter.get(
                                "description", "No description"
                            ),
                            version=frontmatter.get("version"),
                            dependencies=frontmatter.get("dependencies", []),
                            skill_type=frontmatter.get("type", "command"),
                        )
                    except yaml.YAMLError as e:
                        print(f"⚠️  YAML error in {skill_file}: {e}")

            return SkillInfo(
                name=skill_path.name,
                path=str(skill_path),
                source=source,
                description="Skill without frontmatter",
                skill_type="directory",
            )

        except Exception as e:
            print(f"⚠️  Error parsing {skill_file}: {e}")
            return None

    def _discover_from_providers(self):
        """Discover skills from provider-specific configurations"""
        # Check for provider-specific skill directories
        for provider_dir in [self.provider_configs, Path.home() / ".antigravity"]:
            if provider_dir.exists():
                skills_dir = provider_dir / "skills"
                if skills_dir.exists():
                    self._discover_from_directory(skills_dir, "provider")

    def get_skill(self, name: str) -> Optional[SkillInfo]:
        """Get skill by name (supports kebab-case/camelCase conversion)"""
        # Try exact match first
        if name in self.registry:
            return self.registry[name]

        # Try kebab-case conversion
        kebab_name = name.replace("_", "-")
        if kebab_name in self.registry:
            return self.registry[kebab_name]

        # Try camelCase conversion
        camel_name = name.replace("-", "_")
        if camel_name in self.registry:
            return self.registry[camel_name]

        return None

    def list_skills(self, source: Optional[str] = None) -> List[SkillInfo]:
        """List skills, optionally filtered by source"""
        skills = list(self.registry.values())
        if source:
            skills = [s for s in skills if s.source == source]
        return sorted(skills, key=lambda x: x.name)

    def validate_dependencies(self) -> Dict[str, List[str]]:
        """Validate that all skill dependencies are available"""
        print("🔗 Validating skill dependencies...")

        missing_deps = {}
        for name, skill in self.registry.items():
            if skill.dependencies:
                missing = []
                for dep in skill.dependencies:
                    if not self.get_skill(dep):
                        missing.append(dep)
                if missing:
                    missing_deps[name] = missing

        if missing_deps:
            print(f"❌ Missing dependencies found:")
            for skill_name, deps in missing_deps.items():
                print(f"   {skill_name}: {', '.join(deps)}")
        else:
            print("✅ All skill dependencies satisfied")

        return missing_deps

    def generate_registry_file(self, output_path: Path):
        """Generate a JSON registry file for fast lookups"""
        registry_data = {
            "generated_at": datetime.now().isoformat(),
            "total_skills": len(self.registry),
            "skills": {},
        }

        for name, skill in self.registry.items():
            registry_data["skills"][name] = {
                "name": skill.name,
                "path": skill.path,
                "source": skill.source,
                "description": skill.description,
                "version": skill.version,
                "type": skill.skill_type,
                "dependencies": skill.dependencies or [],
            }

        with open(output_path, "w") as f:
            json.dump(registry_data, f, indent=2)

        print(f"📝 Generated skill registry: {output_path}")

    def print_summary(self):
        """Print discovery summary"""
        print("\n📋 Skill Discovery Summary:")
        print("=" * 50)

        # Group by source
        by_source = {}
        for skill in self.registry.values():
            if skill.source not in by_source:
                by_source[skill.source] = []
            by_source[skill.source].append(skill)

        for source in ["global", "project", "provider"]:
            if source in by_source:
                print(f"\n🌐 {source.title()} Skills ({len(by_source[source])}):")
                for skill in by_source[source]:
                    status = "✅" if skill.version else "⚠️"
                    print(f"   {status} {skill.name} (v{skill.version or 'unknown'})")
                    print(f"      📍 {skill.path}")
                    if skill.dependencies:
                        print(f"      🔗 Dependencies: {', '.join(skill.dependencies)}")

        print(f"\n📊 Total: {len(self.registry)} skills discovered")


def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Dynamic Skill Discovery System")
    parser.add_argument("--discover", action="store_true", help="Discover all skills")
    parser.add_argument(
        "--list", help="List skills from source (global/project/provider)"
    )
    parser.add_argument("--get", help="Get specific skill information")
    parser.add_argument(
        "--validate-deps", action="store_true", help="Validate skill dependencies"
    )
    parser.add_argument("--generate-registry", help="Generate JSON registry file")
    parser.add_argument(
        "--summary", action="store_true", help="Print discovery summary"
    )

    args = parser.parse_args()

    discovery = SkillDiscovery()

    if args.discover:
        discovery.discover_skills()
        if args.summary:
            discovery.print_summary()

    elif args.list:
        discovery.discover_skills()
        skills = discovery.list_skills(args.list)
        for skill in skills:
            print(f"{skill.name}: {skill.description}")

    elif args.get:
        discovery.discover_skills()
        skill = discovery.get_skill(args.get)
        if skill:
            print(f"Skill: {skill.name}")
            print(f"Path: {skill.path}")
            print(f"Source: {skill.source}")
            print(f"Type: {skill.skill_type}")
            print(f"Description: {skill.description}")
            if skill.version:
                print(f"Version: {skill.version}")
        else:
            print(f"Skill '{args.get}' not found")

    elif args.validate_deps:
        discovery.discover_skills()
        missing = discovery.validate_dependencies()
        if missing:
            exit(1)

    elif args.generate_registry:
        discovery.discover_skills()
        discovery.generate_registry_file(Path(args.generate_registry))

    elif args.summary:
        discovery.discover_skills()
        discovery.print_summary()


if __name__ == "__main__":
    main()
