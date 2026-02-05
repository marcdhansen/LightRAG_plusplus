"""
Tests for Universal Skill Resolver.
"""

import pytest

from lightrag.core.skill_resolver import SkillNotFoundError, UniversalSkillResolver


def test_resolver_initialization():
    """Test that the resolver initializes with default locations."""
    resolver = UniversalSkillResolver()
    assert len(resolver.skill_locations) >= 2
    assert any("gemini" in loc for loc in resolver.skill_locations)
    assert any(".agent/skills" in loc for loc in resolver.skill_locations)


def test_get_location_type():
    """Test location type identification."""
    resolver = UniversalSkillResolver()
    assert resolver._get_location_type("~/.gemini/antigravity/skills/") == "global"
    assert resolver._get_location_type(".agent/skills/") == "local"
    assert resolver._get_location_type("/usr/local/share/lightrag/skills/") == "system"
    assert resolver._get_location_type("./skills/") == "project"


def test_fallback_strategies_present():
    """Test that default fallback strategies are registered."""
    resolver = UniversalSkillResolver()
    assert "return-to-base" in resolver.fallback_strategies
    assert "reflect" in resolver.fallback_strategies
    assert "mission-debriefing" in resolver.fallback_strategies


def test_require_skill_not_found():
    """Test that requiring an unknown skill raises SkillNotFoundError."""
    resolver = UniversalSkillResolver()
    # We use a name that is unlikely to exist and doesn't have a fallback
    with pytest.raises(SkillNotFoundError):
        resolver.require_skill("non-existent-skill-without-fallback")


def test_mission_feasibility_check():
    """Test the feasibility assessment logic."""
    resolver = UniversalSkillResolver()
    # Mock find_skill to simulate skill availability
    original_find = resolver.find_skill
    try:
        resolver.find_skill = lambda x: {"path": "mock"} if x == "skill1" else None

        feasible, missing = resolver.assess_mission_feasibility(["skill1"])
        assert feasible is True
        assert len(missing) == 0

        feasible, missing = resolver.assess_mission_feasibility(["skill1", "skill2"])
        assert feasible is False
        assert "skill2" in missing
    finally:
        resolver.find_skill = original_find
