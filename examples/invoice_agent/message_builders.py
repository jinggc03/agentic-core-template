"""Invoice agent message builders."""

from typing import Optional, List
from app.agents.base.types import Message, TurnMode
from examples.invoice_agent.types import InvoiceContext


class InvoiceMessageBuilder:
    """Builds messages for invoice agent LLM calls.
    
    Responsible for:
    - Constructing the final message to the LLM
    - Injecting context appropriately
    - Structuring prompts for different modes
    - Avoiding token waste
    """
    
    @staticmethod
    def build_system_prompt(mode: TurnMode = TurnMode.SINGLE) -> str:
        """Build system prompt based on mode.
        
        Args:
            mode: Execution mode
            
        Returns:
            System prompt
        """
        base_prompt = """You are an expert invoice processing assistant.
Your role is to help users extract, validate, and analyze invoices.

Core responsibilities:
- Extract key information from invoices (number, date, vendor, amount, items)
- Validate invoice data for accuracy and completeness
- Provide clear summaries and insights
- Ask for clarification when needed
- Be precise and professional

Always structure your responses clearly and focus on accuracy."""

        if mode == TurnMode.AGENTIC:
            base_prompt += """

In agentic mode:
- You can take multiple steps to solve complex problems
- Use tool calls when needed to extract/validate data
- Reason through the problem systematically
- Report your findings clearly"""

        return base_prompt

    @staticmethod
    def build_extraction_prompt(user_input: str, context: Optional[InvoiceContext] = None) -> str:
        """Build extraction prompt.
        
        Args:
            user_input: User input
            context: Optional context
            
        Returns:
            Extraction prompt
        """
        prompt = f"""Extract invoice information from the following input:

{user_input}

Please extract and provide:
1. Invoice number
2. Invoice date
3. Vendor/Seller name
4. Total amount
5. Currency
6. Line items (list)

Format the response as a structured summary."""

        if context and context.invoice_data:
            prompt += f"""

Previous invoice data:
- Invoice Number: {context.invoice_data.invoice_number}
- Vendor: {context.invoice_data.vendor}
- Amount: {context.invoice_data.total_amount} {context.invoice_data.currency}

Update this data if the new input provides corrections."""

        return prompt

    @staticmethod
    def build_validation_prompt(context: InvoiceContext) -> str:
        """Build validation prompt.
        
        Args:
            context: Invoice context
            
        Returns:
            Validation prompt
        """
        if not context.invoice_data:
            return "No invoice data to validate."
        
        data = context.invoice_data
        prompt = f"""Validate the following invoice data:

Invoice Number: {data.invoice_number or 'Not provided'}
Date: {data.date or 'Not provided'}
Vendor: {data.vendor or 'Not provided'}
Total Amount: {data.total_amount or 'Not provided'} {data.currency}
Items: {', '.join(data.items) if data.items else 'None'}

Please validate:
1. Are all required fields present?
2. Is the data format correct?
3. Are there any inconsistencies?
4. Any other issues?

Provide a clear assessment of validity."""

        return prompt

    @staticmethod
    def build_summary_prompt(context: InvoiceContext) -> str:
        """Build summary prompt.
        
        Args:
            context: Invoice context
            
        Returns:
            Summary prompt
        """
        if not context.invoice_data:
            return "No invoice data to summarize."
        
        data = context.invoice_data
        prompt = f"""Provide a concise summary of this invoice:

Invoice Number: {data.invoice_number or 'Not provided'}
Date: {data.date or 'Not provided'}
Vendor: {data.vendor or 'Not provided'}
Total Amount: {data.total_amount or 'Not provided'} {data.currency}
Items: {', '.join(data.items) if data.items else 'None'}

Summary should include:
- Key details
- Total value
- Any notable items
- Recommendation (approve/review/reject)"""

        return prompt

    @staticmethod
    def build_context_message(
        user_input: str,
        context: Optional[InvoiceContext] = None,
        mode: str = "general",
    ) -> str:
        """Build message with context injection.
        
        Args:
            user_input: User input
            context: Optional context
            mode: Processing mode (extract/validate/summarize/general)
            
        Returns:
            Final message to send to LLM
        """
        if mode == "extract":
            return InvoiceMessageBuilder.build_extraction_prompt(user_input, context)
        elif mode == "validate":
            if context:
                return InvoiceMessageBuilder.build_validation_prompt(context)
            else:
                return user_input
        elif mode == "summarize":
            if context:
                return InvoiceMessageBuilder.build_summary_prompt(context)
            else:
                return user_input
        else:
            return user_input

    @staticmethod
    def format_message_history(messages: List[Message], max_tokens: int = 4000) -> str:
        """Format message history for context.
        
        Args:
            messages: Message history
            max_tokens: Maximum tokens to include
            
        Returns:
            Formatted history
        """
        if not messages:
            return ""
        
        # Keep recent messages within token limit
        history = []
        current_tokens = 0
        estimated_tokens_per_message = 100
        
        for msg in reversed(messages):
            msg_tokens = len(msg.content.split()) + estimated_tokens_per_message
            if current_tokens + msg_tokens > max_tokens:
                break
            history.insert(0, f"{msg.role.upper()}: {msg.content[:200]}...")
            current_tokens += msg_tokens
        
        return "\n".join(history)
