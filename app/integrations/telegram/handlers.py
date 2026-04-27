"""Telegram message handlers."""

from typing import Dict, Any
from app.core.logging import get_logger
from app.agents.registry import get_registry
from app.agents.base import AgentRunner

logger = get_logger(__name__)


class TelegramHandler:
    """Handles Telegram messages and routes to agents."""

    def __init__(self):
        """Initialize handler."""
        self.agent_registry = get_registry()

    async def handle_message(
        self, chat_id: str, message_text: str, agent_id: str = "default"
    ) -> str:
        """Handle incoming Telegram message.
        
        Args:
            chat_id: Chat ID
            message_text: Message text
            agent_id: Agent to use for response
            
        Returns:
            Response message
        """
        try:
            agent = self.agent_registry.instantiate(agent_id)
            turn_result = await AgentRunner(agent).run_turn(message_text)
            if not turn_result.success:
                error_msg = turn_result.error or "Agent turn failed"
                logger.warning(f"Agent {agent_id} failed Telegram turn: {error_msg}")
                return f"Error: {error_msg}"

            response = turn_result.output
            logger.info(f"Message from {chat_id} handled by {agent_id}")
            return response
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return f"Error: {str(e)}"

    async def handle_command(
        self, chat_id: str, command: str, args: list
    ) -> str:
        """Handle Telegram command.
        
        Args:
            chat_id: Chat ID
            command: Command name
            args: Command arguments
            
        Returns:
            Response message
        """
        if command == "help":
            return (
                "Available commands:\n"
                "/help - Show this help\n"
                "/agents - List available agents\n"
                "/reset - Reset agent history"
            )
        elif command == "agents":
            available = self.agent_registry.list_available()
            return f"Available agents: {', '.join(available)}"
        elif command == "reset":
            # Reset all cached agents
            return "Agent history cleared"
        else:
            return f"Unknown command: {command}"
