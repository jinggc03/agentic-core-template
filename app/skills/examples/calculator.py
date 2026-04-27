"""Example skill: simple calculator."""

from typing import Any, Dict
from app.skills.base.skill import BaseSkill


class CalculatorSkill(BaseSkill):
    """Simple calculator skill for demonstration."""

    def __init__(self):
        super().__init__(
            name="calculator",
            description="Performs basic arithmetic operations",
            version="0.1.0",
        )

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute calculation.
        
        Args:
            input_data: Must contain 'operation', 'a', and 'b'
                operation: 'add', 'subtract', 'multiply', 'divide'
                a: first number
                b: second number
                
        Returns:
            Result dictionary with 'result' key
        """
        if not self.validate_input(input_data):
            return {"error": "Invalid input"}

        operation = input_data.get("operation", "").lower()
        a = float(input_data.get("a", 0))
        b = float(input_data.get("b", 0))

        result = None
        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                return {"error": "Division by zero"}
            result = a / b
        else:
            return {"error": f"Unknown operation: {operation}"}

        return {"result": result, "operation": operation, "a": a, "b": b}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate calculator input."""
        required = ["operation", "a", "b"]
        return all(key in input_data for key in required)
