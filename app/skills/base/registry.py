"""Skill registry and loader."""

from typing import Dict, Type
from app.skills.base.skill import BaseSkill


class SkillRegistry:
    """Registry for managing available skills."""

    def __init__(self):
        """Initialize registry."""
        self._skills: Dict[str, Type[BaseSkill]] = {}

    def register(self, skill_class: Type[BaseSkill]) -> None:
        """Register a skill class.
        
        Args:
            skill_class: Skill class to register
        """
        self._skills[skill_class.__name__] = skill_class

    def get(self, skill_name: str) -> Type[BaseSkill]:
        """Get skill class by name.
        
        Args:
            skill_name: Name of skill to retrieve
            
        Returns:
            Skill class
            
        Raises:
            ValueError: If skill not found
        """
        if skill_name not in self._skills:
            available = ", ".join(self._skills.keys())
            raise ValueError(
                f"Skill '{skill_name}' not found. Available skills: {available}"
            )
        return self._skills[skill_name]

    def instantiate(self, skill_name: str, **kwargs) -> BaseSkill:
        """Instantiate a skill.
        
        Args:
            skill_name: Name of skill to instantiate
            **kwargs: Keyword arguments to pass to skill constructor
            
        Returns:
            Instantiated skill
        """
        skill_class = self.get(skill_name)
        return skill_class(**kwargs)

    def list_available(self) -> list[str]:
        """List all available skills."""
        return list(self._skills.keys())


# Global registry instance
_registry = SkillRegistry()


def get_registry() -> SkillRegistry:
    """Get the global skill registry."""
    return _registry
