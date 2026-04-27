"""Example skill: text processing."""

from typing import Any, Dict
from app.skills.base.skill import BaseSkill


class TextProcessingSkill(BaseSkill):
    """Text processing skill for demonstration."""

    def __init__(self):
        super().__init__(
            name="text_processor",
            description="Performs text operations like uppercase, lowercase, reverse",
            version="0.1.0",
        )

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute text operation.
        
        Args:
            input_data: Must contain 'operation' and 'text'
                operation: 'uppercase', 'lowercase', 'reverse', 'length', 'words'
                text: input text to process
                
        Returns:
            Result dictionary with 'result' key
        """
        if not self.validate_input(input_data):
            return {"error": "Invalid input"}

        operation = input_data.get("operation", "").lower()
        text = input_data.get("text", "")

        result = None
        if operation == "uppercase":
            result = text.upper()
        elif operation == "lowercase":
            result = text.lower()
        elif operation == "reverse":
            result = text[::-1]
        elif operation == "length":
            result = len(text)
        elif operation == "words":
            result = len(text.split())
        else:
            return {"error": f"Unknown operation: {operation}"}

        return {"result": result, "operation": operation, "original_text": text}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate text processor input."""
        required = ["operation", "text"]
        return all(key in input_data for key in required)
