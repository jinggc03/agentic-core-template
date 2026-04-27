"""Agent runner - orchestrates agent execution."""

from typing import Optional
from app.agents.base.configured_agent import ConfiguredAgent
from app.agents.base.types import TurnResult
from app.core.logging import get_logger

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
    
    def __init__(self, agent: ConfiguredAgent):
        """Initialize runner with an agent.
        
        Args:
            agent: ConfiguredAgent instance
        """
        self.agent = agent
        self.running = False
        self.turn_results = []

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
        result = await self.agent.run_turn(user_input)
        self.turn_results.append(result)
        
        return result

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
