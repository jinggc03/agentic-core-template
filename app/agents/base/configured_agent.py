"""ConfiguredAgent - ADK-aligned agent implementation."""

import time
import asyncio
from typing import Optional, List
from app.agents.base.types import (
    TurnContext,
    TurnResult,
    Message,
    Snapshot,
    TurnMode,
)
from app.agents.base.execution_policy import PolicyEnforcer, get_default_policy
from app.agents.base.loop_guard import LoopGuard, LoopDetectedError
from app.providers.base import BaseLLMProvider
from app.providers.factory import get_llm_provider
from app.core.logging import get_logger

logger = get_logger(__name__)


def _get_limits() -> dict:
    """Read execution limits from settings (lazy, avoids circular imports)."""
    try:
        from app.core.config import settings
        return {
            "max_input_chars": settings.MAX_INPUT_CHARS,
            "max_output_chars": settings.MAX_OUTPUT_CHARS,
            "timeout_seconds": settings.AGENT_TIMEOUT_SECONDS,
        }
    except Exception:
        return {
            "max_input_chars": 8000,
            "max_output_chars": 12000,
            "timeout_seconds": 60,
        }


class ConfiguredAgent:
    """Agent configured for ADK operation.
    
    This is the main agent class that orchestrates:
    - Turn preparation
    - Execution policy enforcement
    - Input/output length limits
    - Anti-loop detection
    - LLM provider calls
    - Context management
    - Response structuring
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        system_prompt: str,
        provider: Optional[BaseLLMProvider] = None,
        policy_enforcer: Optional[PolicyEnforcer] = None,
        conversation_id: Optional[str] = None,
    ):
        """Initialize configured agent.
        
        Args:
            agent_id: Unique agent identifier
            name: Human-readable agent name
            system_prompt: System prompt for agent
            provider: LLM provider (uses factory default if None)
            policy_enforcer: Execution policy enforcer
            conversation_id: Conversation ID for context
        """
        self.agent_id = agent_id
        self.name = name
        self.system_prompt = system_prompt
        self.provider = provider or get_llm_provider()
        self.policy_enforcer = policy_enforcer or PolicyEnforcer(get_default_policy())
        self.conversation_id = conversation_id or f"{agent_id}-{int(time.time())}"
        
        # State
        self.messages: List[Message] = []
        self.turn_count = 0
        self.snapshot: Optional[Snapshot] = None

        # Anti-loop guard (per conversation)
        self.loop_guard = LoopGuard()

    def prepare_turn(self, user_input: str) -> TurnContext:
        """Prepare a turn (prepare_turno in ADK).
        
        Args:
            user_input: User message
            
        Returns:
            Prepared TurnContext
        """
        turn_context = TurnContext(
            agent_id=self.agent_id,
            conversation_id=self.conversation_id,
            turn_count=self.turn_count,
            user_input=user_input,
            system_prompt=self.system_prompt,
            mode=TurnMode.SINGLE,
            policy=self.policy_enforcer.policy,
            snapshot=self.snapshot,
        )
        
        logger.debug(
            f"Agent {self.agent_id} prepared turn {self.turn_count}: {user_input[:50]}..."
        )
        return turn_context

    async def run_turn(self, user_input: str) -> TurnResult:
        """Execute a single turn (ADK turn execution).
        
        Args:
            user_input: User input for this turn
            
        Returns:
            TurnResult with response and metadata
        """
        limits = _get_limits()
        start_time = time.time()

        # ── Input length guard ────────────────────────────────────────────────
        if len(user_input) > limits["max_input_chars"]:
            return TurnResult(
                success=False,
                output="",
                error=(
                    f"Input too long ({len(user_input)} chars). "
                    f"Maximum is {limits['max_input_chars']} chars."
                ),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # ── Anti-loop check ───────────────────────────────────────────────────
        try:
            self.loop_guard.check_input(user_input)
        except LoopDetectedError as e:
            return TurnResult(
                success=False,
                output="",
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # ── Policy turn-start check ───────────────────────────────────────────
        is_allowed, error = self.policy_enforcer.on_turn_start()
        if not is_allowed:
            return TurnResult(
                success=False,
                output="",
                error=error or "Turn not allowed",
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        
        # Prepare turn and use the generated context through execution.
        turn_context = self.prepare_turn(user_input)
        
        # Add user message
        user_message = Message(role="user", content=turn_context.user_input)
        self.messages.append(user_message)
        
        try:
            # ── Policy model-call check ───────────────────────────────────────
            is_allowed, error = self.policy_enforcer.on_model_call()
            if not is_allowed:
                return TurnResult(
                    success=False,
                    output="",
                    error=error or "Model call not allowed",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # ── LLM call with timeout ─────────────────────────────────────────
            response = await asyncio.wait_for(
                self.provider.generate(
                    prompt=turn_context.user_input,
                    system_prompt=turn_context.system_prompt,
                    temperature=0.7,
                    max_tokens=2000,
                ),
                timeout=limits["timeout_seconds"],
            )
            
            # ── Output length truncation ──────────────────────────────────────
            max_out = limits["max_output_chars"]
            if len(response) > max_out:
                logger.warning(
                    f"Agent {self.agent_id} output truncated "
                    f"({len(response)} → {max_out} chars)"
                )
                response = response[:max_out]

            # ── Anti-loop output check ────────────────────────────────────────
            try:
                self.loop_guard.check_output(response)
            except LoopDetectedError as e:
                return TurnResult(
                    success=False,
                    output="",
                    error=str(e),
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # Add assistant message
            assistant_message = Message(role="assistant", content=response)
            self.messages.append(assistant_message)
            
            # Increment turn
            self.turn_count += 1
            self.loop_guard.on_turn_complete(user_input, response)
            
            execution_time_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Agent {self.agent_id} completed turn {self.turn_count-1} "
                f"in {execution_time_ms:.1f}ms"
            )
            
            return TurnResult(
                success=True,
                output=response,
                model_calls=1,
                tool_calls=0,
                execution_time_ms=execution_time_ms,
            )

        except asyncio.TimeoutError:
            elapsed = (time.time() - start_time) * 1000
            logger.error(
                f"Agent {self.agent_id} timed out after "
                f"{limits['timeout_seconds']}s"
            )
            return TurnResult(
                success=False,
                output="",
                error=f"Execution timed out after {limits['timeout_seconds']} seconds",
                execution_time_ms=elapsed,
            )
        except Exception as e:
            logger.error(f"Agent {self.agent_id} error: {e}")
            execution_time_ms = (time.time() - start_time) * 1000
            return TurnResult(
                success=False,
                output="",
                error=str(e),
                execution_time_ms=execution_time_ms,
            )

    def run(self, user_input: str) -> str:
        """Synchronous turn execution wrapper.
        
        Args:
            user_input: User message
            
        Returns:
            Agent response
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop is None:
            result = asyncio.run(self.run_turn(user_input))
        else:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                result = executor.submit(
                    asyncio.run, self.run_turn(user_input)
                ).result()
        
        if result.success:
            return result.output
        else:
            raise RuntimeError(result.error or "Turn execution failed")

    def get_messages(self) -> List[Message]:
        """Get conversation message history.
        
        Returns:
            List of messages
        """
        return self.messages.copy()

    def save_snapshot(self) -> Snapshot:
        """Save current state as snapshot (for context caching).
        
        Returns:
            State snapshot
        """
        self.snapshot = Snapshot(
            agent_id=self.agent_id,
            conversation_id=self.conversation_id,
            turn_count=self.turn_count,
            messages=self.messages.copy(),
            state={
                "name": self.name,
                "system_prompt": self.system_prompt,
            },
        )
        logger.debug(f"Agent {self.agent_id} saved snapshot")
        return self.snapshot

    def reset(self):
        """Reset agent state."""
        self.messages = []
        self.turn_count = 0
        self.snapshot = None
        self.policy_enforcer.reset()
        self.loop_guard.reset()
        logger.info(f"Agent {self.agent_id} reset")

    def __repr__(self) -> str:
        return (
            f"ConfiguredAgent("
            f"id={self.agent_id}, "
            f"name={self.name}, "
            f"turns={self.turn_count}"
            f")"
        )
