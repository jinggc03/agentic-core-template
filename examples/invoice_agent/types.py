"""Invoice agent types and data structures."""

from typing import Optional
from pydantic import BaseModel, Field


class InvoiceData(BaseModel):
    """Extracted invoice data."""
    
    invoice_number: Optional[str] = Field(None, description="Invoice number")
    date: Optional[str] = Field(None, description="Invoice date")
    vendor: Optional[str] = Field(None, description="Vendor/seller name")
    total_amount: Optional[float] = Field(None, description="Total amount")
    currency: Optional[str] = Field("USD", description="Currency")
    items: list[str] = Field(default_factory=list, description="Line items")
    status: str = Field(default="pending", description="Invoice status")


class InvoiceValidationResult(BaseModel):
    """Invoice validation result."""
    
    is_valid: bool = Field(..., description="Whether invoice is valid")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")


class InvoiceContext(BaseModel):
    """Context for invoice processing."""
    
    invoice_data: Optional[InvoiceData] = Field(None, description="Current invoice data")
    validation_result: Optional[InvoiceValidationResult] = Field(None, description="Validation result")
    processing_stage: str = Field(default="initial", description="Current processing stage")
