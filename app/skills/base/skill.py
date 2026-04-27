"""Base skill interface - compatible with agentic-cowork-hub."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseSkill(ABC):
    """Base class for all skills.
    
    This interface is designed to be compatible with agentic-cowork-hub skills.
    Skills are reusable units of work that can be imported and used by agents.
    """

    def __init__(self, name: str, description: str = "", version: str = "0.1.0"):
        """Initialize skill.
        
        Args:
            name: Unique identifier for the skill
            description: Human-readable description
            version: Skill version
        """
        self.name = name
        self.description = description
        self.version = version

    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill.
        
        Args:
            input_data: Input parameters as dictionary
            
        Returns:
            Output as dictionary
        """
        pass

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data. Override in subclass if needed."""
        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, version={self.version})"
