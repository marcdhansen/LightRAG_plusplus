#!/usr/bin/env python3
"""
Cross-agent slash command support for OpenViking.
Bridges file-based commands in ~/.agent/commands/ to OpenViking API.

Commands are simple markdown files with YAML frontmatter:
---
description: short description of the command
---
Instructions for the agent to follow when this command is invoked.
"""
from pathlib import Path
from typing import Dict, List, Optional
import re
import logging

try:
    import yaml
except ImportError:
    # Fallback if PyYAML not available
    yaml = None

logger = logging.getLogger(__name__)

# Default commands directory - can be overridden
DEFAULT_COMMANDS_DIR = Path.home() / ".agent" / "commands"


class CommandRegistry:
    """
    Registry for cross-agent slash commands.
    
    Scans ~/.agent/commands/ for markdown files and makes them available
    via the OpenViking API.
    """
    
    def __init__(self, commands_dir: Optional[Path] = None):
        self.commands_dir = commands_dir or DEFAULT_COMMANDS_DIR
        self.commands: Dict[str, dict] = {}
        self._last_scan_time: Optional[float] = None
        self.reload()
    
    def reload(self) -> int:
        """
        Scan the commands directory for available commands.
        
        Returns:
            Number of commands loaded
        """
        self.commands = {}
        
        if not self.commands_dir.exists():
            logger.warning(f"Commands directory does not exist: {self.commands_dir}")
            return 0
        
        for cmd_file in self.commands_dir.glob("*.md"):
            try:
                name = cmd_file.stem  # e.g., "next" from "next.md"
                content = cmd_file.read_text(encoding="utf-8")
                
                # Parse YAML frontmatter
                frontmatter, instructions = self._parse_frontmatter(content)
                
                self.commands[name] = {
                    "name": name,
                    "description": frontmatter.get("description", ""),
                    "instructions": instructions,
                    "path": str(cmd_file),
                    "frontmatter": frontmatter
                }
                logger.debug(f"Loaded command: /{name}")
                
            except Exception as e:
                logger.error(f"Failed to load command from {cmd_file}: {e}")
        
        logger.info(f"Loaded {len(self.commands)} commands from {self.commands_dir}")
        return len(self.commands)
    
    def _parse_frontmatter(self, content: str) -> tuple:
        """
        Parse YAML frontmatter from markdown content.
        
        Args:
            content: Raw markdown file content
            
        Returns:
            Tuple of (frontmatter_dict, instructions_str)
        """
        # Match YAML frontmatter pattern: ---\n...\n---\n
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
        
        if match:
            frontmatter_raw = match.group(1)
            instructions = match.group(2).strip()
            
            # Parse YAML if available
            if yaml:
                try:
                    frontmatter = yaml.safe_load(frontmatter_raw) or {}
                except yaml.YAMLError as e:
                    logger.warning(f"Failed to parse YAML frontmatter: {e}")
                    frontmatter = {}
            else:
                # Simple fallback parsing for description
                frontmatter = {}
                for line in frontmatter_raw.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip()
            
            return frontmatter, instructions
        
        # No frontmatter found - treat entire content as instructions
        return {}, content.strip()
    
    def get_command(self, name: str) -> Optional[dict]:
        """
        Retrieve a command by name.
        
        Args:
            name: Command name (with or without leading /)
            
        Returns:
            Command dict or None if not found
        """
        # Strip leading slash if present
        clean_name = name.lstrip("/")
        return self.commands.get(clean_name)
    
    def list_commands(self) -> List[dict]:
        """
        List all available commands.
        
        Returns:
            List of command summaries (name and description)
        """
        return [
            {
                "name": f"/{name}",
                "description": cmd["description"]
            }
            for name, cmd in sorted(self.commands.items())
        ]
    
    def search_commands(self, query: str) -> List[dict]:
        """
        Search commands by name or description.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching commands
        """
        query_lower = query.lower()
        results = []
        
        for name, cmd in self.commands.items():
            if (query_lower in name.lower() or 
                query_lower in cmd["description"].lower() or
                query_lower in cmd["instructions"].lower()):
                results.append({
                    "name": f"/{name}",
                    "description": cmd["description"],
                    "instructions": cmd["instructions"]
                })
        
        return results


# Module-level singleton for convenience
_default_registry: Optional[CommandRegistry] = None


def get_registry() -> CommandRegistry:
    """Get or create the default command registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = CommandRegistry()
    return _default_registry


def reload_commands() -> int:
    """Reload commands from disk."""
    return get_registry().reload()


def get_command(name: str) -> Optional[dict]:
    """Get a command by name."""
    return get_registry().get_command(name)


def list_commands() -> List[dict]:
    """List all available commands."""
    return get_registry().list_commands()


if __name__ == "__main__":
    # Test the command registry
    import json
    
    logging.basicConfig(level=logging.DEBUG)
    
    registry = CommandRegistry()
    
    print(f"\n📂 Commands directory: {registry.commands_dir}")
    print(f"📋 Loaded {len(registry.commands)} commands\n")
    
    for cmd in registry.list_commands():
        print(f"  {cmd['name']}: {cmd['description']}")
    
    print("\n🔍 Testing command retrieval:")
    for test_name in ["/next", "rtb", "/nonexistent"]:
        cmd = registry.get_command(test_name)
        if cmd:
            print(f"  ✅ Found: {test_name}")
            print(f"     Instructions: {cmd['instructions'][:50]}...")
        else:
            print(f"  ❌ Not found: {test_name}")
