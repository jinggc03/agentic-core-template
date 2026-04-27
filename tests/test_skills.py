"""Test skills."""

import pytest

from app.skills.base.skill import BaseSkill
from app.skills.base.registry import get_registry
from app.skills.examples.calculator import CalculatorSkill
from app.skills.examples.text_processor import TextProcessingSkill


def test_base_skill_interface():
    """Test BaseSkill interface."""
    
    class TestSkill(BaseSkill):
        def run(self, input_data: dict) -> dict:
            return {"result": "test"}
    
    skill = TestSkill("test-skill", "Test skill")
    assert skill.name == "test-skill"
    assert skill.version == "0.1.0"


def test_calculator_skill():
    """Test calculator skill."""
    skill = CalculatorSkill()
    
    # Test addition
    result = skill.run({"operation": "add", "a": 2, "b": 3})
    assert result["result"] == 5
    
    # Test subtraction
    result = skill.run({"operation": "subtract", "a": 5, "b": 3})
    assert result["result"] == 2
    
    # Test multiplication
    result = skill.run({"operation": "multiply", "a": 4, "b": 5})
    assert result["result"] == 20
    
    # Test division
    result = skill.run({"operation": "divide", "a": 10, "b": 2})
    assert result["result"] == 5
    
    # Test division by zero
    result = skill.run({"operation": "divide", "a": 10, "b": 0})
    assert "error" in result


def test_text_processor_skill():
    """Test text processor skill."""
    skill = TextProcessingSkill()
    
    # Test uppercase
    result = skill.run({"operation": "uppercase", "text": "hello"})
    assert result["result"] == "HELLO"
    
    # Test lowercase
    result = skill.run({"operation": "lowercase", "text": "HELLO"})
    assert result["result"] == "hello"
    
    # Test reverse
    result = skill.run({"operation": "reverse", "text": "hello"})
    assert result["result"] == "olleh"
    
    # Test length
    result = skill.run({"operation": "length", "text": "hello"})
    assert result["result"] == 5
    
    # Test word count
    result = skill.run({"operation": "words", "text": "hello world test"})
    assert result["result"] == 3


def test_skill_registry():
    """Test skill registry."""
    registry = get_registry()
    
    # Register a skill
    registry.register(CalculatorSkill)
    
    # Instantiate skill
    skill = registry.instantiate("CalculatorSkill")
    assert skill.name == "calculator"
    
    # List available
    available = registry.list_available()
    assert "CalculatorSkill" in available
