"""Agent runner - orchestrates agent execution."""

from typing import Optional
from uuid import uuid4

from app.agents.base.configured_agent import ConfiguredAgent
from app.agents.base.types import TurnResult
from app.auth.context import AuthContext
from app.core.logging import get_logger
from app.repositories import (
    AgentStateRecord,
    ConversationRecord,
    MessageRecord,
    RepositoryBundle,
    get_repository_bundle,
)
from app.services.audit import AuditService

logger = get_logger(__name__)


class AgentRunner:
    """Orchestrates agent execution with turn management.
    
    The runner is responsible for:
    - Managing agent lifecycle
    - Executing turns sequentially
    - Applying execution policies
    - Handling errors
    - Maintaining execution state
    """
    
    def __init__(
        self,
        agent: ConfiguredAgent,
        repositories: Optional[RepositoryBundle] = None,
        persist_turns: bool = False,
        audit_service: Optional[AuditService] = None,
        auth_context: Optional[AuthContext] = None,
    ):
        """Initialize runner with an agent.
        
        Args:
            agent: ConfiguredAgent instance
            repositories: Optional persistence repositories
            persist_turns: Whether to persist conversations, messages, and state
            audit_service: Optional audit event service
            auth_context: Optional request auth context
        """
        self.agent = agent
        self.auth_context = auth_context
        if auth_context is not None:
            self.agent.auth_context = auth_context
        self.running = False
        self.turn_results = []
        self.persist_turns = persist_turns
        self.repositories = repositories
        self.audit_service = audit_service

    async def run_turn(self, user_input: str) -> TurnResult:
        """Execute a single turn.
        
        Args:
            user_input: User input for this turn
            
        Returns:
            TurnResult
        """
        if not self.running:
            self.running = True
        
        logger.debug(f"Runner executing turn for {self.agent.agent_id}")
        self._record_audit_turn_started()
        result = await self.agent.run_turn(user_input)
        self.turn_results.append(result)
        self._persist_turn(user_input, result)
        self._record_audit_turn_completed(result)
        
        return result

    def _get_repositories(self) -> Optional[RepositoryBundle]:
        if self.repositories is not None:
            return self.repositories
        if self.persist_turns:
            self.repositories = get_repository_bundle()
            return self.repositories
        return None

    def _persist_turn(self, user_input: str, result: TurnResult) -> None:
        repositories = self._get_repositories()
        if repositories is None:
            return

        try:
            conversation_id = self.agent.conversation_id
            if repositories.conversations.get_conversation(conversation_id) is None:
                repositories.conversations.create_conversation(
                    ConversationRecord(
                        id=conversation_id,
                        agent_id=self.agent.agent_id,
                        user_id=self.auth_context.actor_id if self.auth_context else None,
                        metadata={"agent_name": self.agent.name},
                    )
                )

            turn_index = max(len(self.turn_results) - 1, 0)
            repositories.messages.add_message(
                MessageRecord(
                    id=str(uuid4()),
                    conversation_id=conversation_id,
                    role="user",
                    content=user_input,
                    metadata={
                        "turn_index": turn_index,
                        "actor_id": self.auth_context.actor_id if self.auth_context else None,
                    },
                )
            )
            repositories.messages.add_message(
                MessageRecord(
                    id=str(uuid4()),
                    conversation_id=conversation_id,
                    role="assistant" if result.success else "error",
                    content=result.output if result.success else (result.error or ""),
                    metadata={
                        "turn_index": turn_index,
                        "success": result.success,
                        "model_calls": result.model_calls,
                        "tool_calls": result.tool_calls,
                        "execution_time_ms": result.execution_time_ms,
                        "actor_id": self.auth_context.actor_id if self.auth_context else None,
                    },
                )
            )

            snapshot = (
                self.agent.snapshot.model_dump(mode="json")
                if self.agent.snapshot
                else None
            )
            repositories.agent_states.save_state(
                AgentStateRecord(
                    id=f"{self.agent.agent_id}:{conversation_id}",
                    agent_id=self.agent.agent_id,
                    conversation_id=conversation_id,
                    state={
                        "turn_count": self.agent.turn_count,
                        "last_turn_success": result.success,
                    },
                    snapshot=snapshot,
                    version=self.agent.turn_count,
                )
            )
        except Exception as exc:
            logger.warning(
                "Failed to persist turn for %s/%s: %s",
                self.agent.agent_id,
                self.agent.conversation_id,
                exc,
            )

    def _record_audit_turn_started(self) -> None:
        if self.audit_service is None:
            return
        try:
            self.audit_service.agent_turn_started(
                agent_id=self.agent.agent_id,
                conversation_id=self.agent.conversation_id,
            )
        except Exception as exc:
            logger.warning("Failed to record audit start event: %s", exc)

    def _record_audit_turn_completed(self, result: TurnResult) -> None:
        if self.audit_service is None:
            return
        try:
            self.audit_service.agent_turn_completed(
                agent_id=self.agent.agent_id,
                conversation_id=self.agent.conversation_id,
                success=result.success,
                execution_time_ms=result.execution_time_ms,
                error=result.error,
            )
        except Exception as exc:
            logger.warning("Failed to record audit completion event: %s", exc)

    def run(self, user_input: str) -> str:
        """Synchronous turn execution.
        
        Args:
            user_input: User message
            
        Returns:
            Agent response
        """
        return self.agent.run(user_input)

    def get_execution_summary(self) -> dict:
        """Get summary of execution.
        
        Returns:
            Execution summary
        """
        if not self.turn_results:
            return {
                "turns": 0,
                "successful_turns": 0,
                "failed_turns": 0,
                "total_model_calls": 0,
                "total_tool_calls": 0,
                "total_time_ms": 0,
            }
        
        successful = sum(1 for r in self.turn_results if r.success)
        failed = len(self.turn_results) - successful
        model_calls = sum(r.model_calls for r in self.turn_results)
        tool_calls = sum(r.tool_calls for r in self.turn_results)
        total_time = sum(r.execution_time_ms for r in self.turn_results)
        
        return {
            "turns": len(self.turn_results),
            "successful_turns": successful,
            "failed_turns": failed,
            "total_model_calls": model_calls,
            "total_tool_calls": tool_calls,
            "total_time_ms": total_time,
            "average_turn_time_ms": total_time / len(self.turn_results) if self.turn_results else 0,
        }

    def stop(self):
        """Stop the runner."""
        self.running = False
        logger.info(f"Agent {self.agent.agent_id} runner stopped")

    def reset(self):
        """Reset runner state."""
        self.agent.reset()
        self.running = False
        self.turn_results = []
        logger.info(f"Agent {self.agent.agent_id} runner reset")

    def __repr__(self) -> str:
        return (
            f"AgentRunner(agent={self.agent.agent_id}, "
            f"running={self.running}, turns={len(self.turn_results)})"
        )
