"""Invoice agent context management."""

from typing import Optional
from datetime import datetime
from examples.invoice_agent.types import InvoiceContext, InvoiceData, InvoiceValidationResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class InvoiceContextManager:
    """Manages invoice agent context and state.
    
    Responsible for:
    - Loading/saving context snapshots
    - Managing current processing state
    - Validating context transitions
    - Preventing unnecessary LLM calls
    """
    
    def __init__(self):
        """Initialize context manager."""
        self.context = InvoiceContext()
        self.last_updated = datetime.utcnow()

    def load_context(self, saved_context: Optional[dict]) -> InvoiceContext:
        """Load context from snapshot or external source.
        
        Args:
            saved_context: Saved context dictionary
            
        Returns:
            Loaded context
        """
        if saved_context:
            try:
                self.context = InvoiceContext(**saved_context)
                self.last_updated = datetime.utcnow()
                logger.debug("Context loaded from snapshot")
            except Exception as e:
                logger.warning(f"Failed to load context: {e}, using default")
                self.context = InvoiceContext()
        else:
            self.context = InvoiceContext()
        
        return self.context

    def save_context(self) -> dict:
        """Save current context to snapshot.
        
        Returns:
            Context dictionary
        """
        self.last_updated = datetime.utcnow()
        return self.context.model_dump()

    def update_invoice_data(self, invoice_data: InvoiceData) -> None:
        """Update invoice data in context.
        
        Args:
            invoice_data: New invoice data
        """
        self.context.invoice_data = invoice_data
        self.context.processing_stage = "data_extracted"
        self.last_updated = datetime.utcnow()
        logger.debug("Invoice data updated in context")

    def update_validation_result(self, result: InvoiceValidationResult) -> None:
        """Update validation result in context.
        
        Args:
            result: Validation result
        """
        self.context.validation_result = result
        self.context.processing_stage = "validated" if result.is_valid else "validation_failed"
        self.last_updated = datetime.utcnow()
        logger.debug(f"Validation result updated: valid={result.is_valid}")

    def is_invoice_extracted(self) -> bool:
        """Check if invoice data is extracted.
        
        Returns:
            Whether invoice is extracted
        """
        return self.context.invoice_data is not None

    def is_invoice_validated(self) -> bool:
        """Check if invoice is validated.
        
        Returns:
            Whether invoice is validated
        """
        return (
            self.context.validation_result is not None
            and self.context.validation_result.is_valid
        )

    def should_call_llm_for_extraction(self) -> bool:
        """Determine if LLM call is needed for extraction.
        
        Returns:
            Whether to call LLM
        """
        # Don't call LLM if data already extracted
        return not self.is_invoice_extracted()

    def should_call_llm_for_validation(self) -> bool:
        """Determine if LLM call is needed for validation.
        
        Returns:
            Whether to call LLM
        """
        # Only validate if data extracted
        if not self.is_invoice_extracted():
            return False
        
        # Don't validate again if already valid
        if self.is_invoice_validated():
            return False
        
        return True

    def get_context_summary(self) -> dict:
        """Get summary of current context.
        
        Returns:
            Context summary
        """
        return {
            "has_invoice_data": self.is_invoice_extracted(),
            "is_validated": self.is_invoice_validated(),
            "processing_stage": self.context.processing_stage,
            "last_updated": self.last_updated.isoformat(),
            "invoice_amount": (
                self.context.invoice_data.total_amount
                if self.is_invoice_extracted()
                else None
            ),
        }

    def reset(self):
        """Reset context."""
        self.context = InvoiceContext()
        self.last_updated = datetime.utcnow()
        logger.debug("Context reset")
