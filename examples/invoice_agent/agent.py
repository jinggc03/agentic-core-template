"""Invoice agent - ADK-aligned implementation."""

from typing import Optional
from app.agents.base import ConfiguredAgent, AgentRunner
from app.agents.base.execution_policy import get_default_policy, PolicyEnforcer
from app.agents.base.types import TurnResult, TurnMode
from app.providers.factory import get_llm_provider
from app.core.logging import get_logger
from examples.invoice_agent.routing import InvoiceRouter
from examples.invoice_agent.context import InvoiceContextManager
from examples.invoice_agent.message_builders import InvoiceMessageBuilder

logger = get_logger(__name__)


class InvoiceAgent(ConfiguredAgent):
    """Invoice processing agent - ADK-aligned.
    
    Demonstrates full ADK pattern with:
    - Routing layer (determines execution mode)
    - Context layer (manages state, avoids LLM calls)
    - Message builders (constructs prompts)
    - Execution policy enforcement
    """
    
    def __init__(
        self,
        agent_id: str = "invoice-agent",
        name: str = "Invoice Agent",
        conversation_id: Optional[str] = None,
    ):
        """Initialize invoice agent.
        
        Args:
            agent_id: Agent identifier
            name: Agent name
            conversation_id: Optional conversation ID
        """
        from app.core.config import settings

        system_prompt = InvoiceMessageBuilder.build_system_prompt()
        
        policy_enforcer = PolicyEnforcer(
            get_default_policy(settings.APP_ENV)
        )
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            system_prompt=system_prompt,
            provider=get_llm_provider(),
            policy_enforcer=policy_enforcer,
            conversation_id=conversation_id,
        )
        
        # ADK-specific components
        self.router = InvoiceRouter()
        self.context_manager = InvoiceContextManager()
        self.message_builder = InvoiceMessageBuilder()

    async def run_turn(self, user_input: str) -> TurnResult:
        """Execute turn with full ADK pattern.
        
        Steps:
        1. Routing - determine execution mode and flow
        2. Context - load/check state, avoid unnecessary LLM calls
        3. Message building - construct optimized prompt
        4. Execution - run through LLM provider
        5. State update - save context snapshot
        
        Args:
            user_input: User input
            
        Returns:
            TurnResult
        """
        import time
        start_time = time.time()
        
        try:
            # 1. ROUTING - Determine execution mode and flow
            logger.debug(f"[{self.agent_id}] STEP 1: Routing")
            mode = self.router.resolve_mode(user_input, self.context_manager.context)
            
            # 2. CONTEXT - Check if LLM call is necessary
            logger.debug(f"[{self.agent_id}] STEP 2: Context analysis")
            
            # Determine processing mode based on input
            processing_mode = "general"
            if self.router.should_extract_invoice(user_input):
                processing_mode = "extract"
                if not self.context_manager.should_call_llm_for_extraction():
                    logger.info(f"[{self.agent_id}] Context hit: invoice already extracted")
                    # Return cached response
                    return TurnResult(
                        success=True,
                        output="Invoice data already extracted. Use 'validate' to check it.",
                        model_calls=0,
                        tool_calls=0,
                        execution_time_ms=(time.time() - start_time) * 1000,
                    )
            elif self.router.should_validate_invoice(user_input):
                processing_mode = "validate"
                if not self.context_manager.should_call_llm_for_validation():
                    logger.info(f"[{self.agent_id}] Context hit: invoice already validated")
                    return TurnResult(
                        success=True,
                        output="Invoice already validated and is valid.",
                        model_calls=0,
                        tool_calls=0,
                        execution_time_ms=(time.time() - start_time) * 1000,
                    )
            
            # 3. MESSAGE BUILDING - Construct optimized prompt
            logger.debug(f"[{self.agent_id}] STEP 3: Message building")
            system_prompt = InvoiceMessageBuilder.build_system_prompt(mode)
            context_message = InvoiceMessageBuilder.build_context_message(
                user_input,
                self.context_manager.context,
                processing_mode,
            )
            
            # 4. EXECUTION - Call LLM provider
            logger.debug(f"[{self.agent_id}] STEP 4: LLM execution (mode={mode})")
            
            # Check policy
            is_allowed, error = self.policy_enforcer.on_turn_start()
            if not is_allowed:
                return TurnResult(
                    success=False,
                    output="",
                    error=error or "Turn not allowed",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )
            
            # Call LLM
            is_allowed, error = self.policy_enforcer.on_model_call()
            if not is_allowed:
                return TurnResult(
                    success=False,
                    output="",
                    error=error or "Model call not allowed",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )
            
            response = await self.provider.generate(
                prompt=context_message,
                system_prompt=system_prompt,
                temperature=0.5,  # Lower for consistency
                max_tokens=1500,
            )
            
            # 5. STATE UPDATE - Save context snapshot
            logger.debug(f"[{self.agent_id}] STEP 5: State update")
            # In a real system, you would parse response and update context
            # For now, save snapshot
            self.context_manager.save_context()
            
            # Update message history
            from app.agents.base.types import Message
            self.messages.append(Message(role="user", content=user_input))
            self.messages.append(Message(role="assistant", content=response))
            self.turn_count += 1
            
            execution_time_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[{self.agent_id}] Turn {self.turn_count} completed "
                f"(mode={mode}, time={execution_time_ms:.1f}ms)"
            )
            
            return TurnResult(
                success=True,
                output=response,
                model_calls=1,
                tool_calls=0,
                execution_time_ms=execution_time_ms,
            )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error: {e}", exc_info=True)
            return TurnResult(
                success=False,
                output="",
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def get_context(self) -> dict:
        """Get current agent context.
        
        Returns:
            Context summary
        """
        return self.context_manager.get_context_summary()

    def reset(self):
        """Reset agent state."""
        super().reset()
        self.router.reset()
        self.context_manager.reset()
        logger.info(f"[{self.agent_id}] Reset complete")


class InvoiceAgentRunner(AgentRunner):
    """Specialized runner for invoice agent.
    
    Provides domain-specific execution orchestration.
    """
    
    def __init__(self, agent: InvoiceAgent):
        """Initialize runner.
        
        Args:
            agent: InvoiceAgent instance
        """
        super().__init__(agent)
        self.agent: InvoiceAgent = agent  # Type hint for IDE

    def get_agent_context(self) -> dict:
        """Get agent context.
        
        Returns:
            Agent context
        """
        return self.agent.get_context()
