"""Invoice agent routing logic."""

from typing import Optional
from app.agents.base.types import TurnMode
from examples.invoice_agent.types import InvoiceContext


class InvoiceRouter:
    """Routes execution based on user input and context.
    
    Determines:
    - Execution mode (single/agentic)
    - Which tools to use
    - Processing flow
    """
    
    def __init__(self):
        """Initialize router."""
        self.context: Optional[InvoiceContext] = None

    def resolve_mode(self, user_input: str, context: Optional[InvoiceContext] = None) -> TurnMode:
        """Resolve execution mode based on input.
        
        Args:
            user_input: User input
            context: Optional current context
            
        Returns:
            Resolved TurnMode
        """
        self.context = context
        
        # Keywords that suggest agentic mode
        agentic_keywords = [
            "process", "validate", "extract", "analyze", "review",
            "check", "verify", "summarize", "details"
        ]
        
        user_lower = user_input.lower()
        
        # Use agentic mode for complex operations
        if any(kw in user_lower for kw in agentic_keywords):
            return TurnMode.AGENTIC
        
        # Default to single mode for simple queries
        return TurnMode.SINGLE

    def should_extract_invoice(self, user_input: str) -> bool:
        """Determine if invoice extraction is needed.
        
        Args:
            user_input: User input
            
        Returns:
            Whether to extract invoice
        """
        extract_keywords = ["extract", "parse", "read", "upload", "process"]
        return any(kw in user_input.lower() for kw in extract_keywords)

    def should_validate_invoice(self, user_input: str) -> bool:
        """Determine if invoice validation is needed.
        
        Args:
            user_input: User input
            
        Returns:
            Whether to validate invoice
        """
        validate_keywords = ["validate", "check", "verify", "correct"]
        return any(kw in user_input.lower() for kw in validate_keywords)

    def get_next_step(self, context: InvoiceContext) -> str:
        """Determine next processing step.
        
        Args:
            context: Current context
            
        Returns:
            Next step
        """
        if not context.invoice_data:
            return "extract"
        
        if not context.validation_result:
            return "validate"
        
        if not context.validation_result.is_valid:
            return "correct"
        
        return "complete"

    def reset(self):
        """Reset routing context."""
        self.context = None
