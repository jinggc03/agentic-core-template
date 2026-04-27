"""Agent registry and factory - ADK-aligned.

The registry manages:
- Agent class registration
- Instance creation and caching
- Modular agent loading from packages
- Agent discovery and listing
"""

from typing import Dict, Type, Optional, Any
from app.agents.base import ConfiguredAgent
from app.core.logging import get_logger
import importlib
from pathlib import Path

logger = get_logger(__name__)


class AgentRegistry:
    """Registry for managing ConfiguredAgent instances.
    
    Features:
    - Class registration and instantiation
    - Modular agent loading from packages
    - Instance caching
    - Agent discovery
    """

    def __init__(self):
        """Initialize registry."""
        self._agents: Dict[str, Type[ConfiguredAgent]] = {}
        self._instances: Dict[str, ConfiguredAgent] = {}

    def register(self, agent_id: str, agent_class: Type[ConfiguredAgent]) -> None:
        """Register an agent class.
        
        Args:
            agent_id: Unique identifier for agent
            agent_class: ConfiguredAgent subclass
        """
        if not issubclass(agent_class, ConfiguredAgent):
            raise TypeError(f"{agent_class} must be a ConfiguredAgent subclass")
        
        self._agents[agent_id] = agent_class
        logger.info(f"Registered agent: {agent_id} ({agent_class.__name__})")

    def instantiate(
        self,
        agent_id: str,
        **kwargs: Any
    ) -> ConfiguredAgent:
        """Instantiate an agent.
        
        Args:
            agent_id: Agent identifier
            **kwargs: Arguments for agent constructor
            
        Returns:
            ConfiguredAgent instance
            
        Raises:
            ValueError: If agent not registered
        """
        if agent_id not in self._agents:
            available = ", ".join(self._agents.keys()) or "(none)"
            raise ValueError(
                f"Agent '{agent_id}' not registered. Available: {available}"
            )

        agent_class = self._agents[agent_id]
        
        # Ensure agent_id is passed
        if "agent_id" not in kwargs:
            kwargs["agent_id"] = agent_id
        
        try:
            instance = agent_class(**kwargs)
            self._instances[agent_id] = instance
            logger.info(f"Instantiated agent: {agent_id}")
            return instance
        except TypeError as e:
            logger.error(f"Failed to instantiate {agent_id}: {e}")
            raise

    def get_instance(self, agent_id: str) -> Optional[ConfiguredAgent]:
        """Get cached agent instance.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            ConfiguredAgent instance or None
        """
        return self._instances.get(agent_id)

    def release_instance(self, agent_id: str) -> None:
        """Release cached agent instance.
        
        Args:
            agent_id: Agent identifier
        """
        if agent_id in self._instances:
            del self._instances[agent_id]
            logger.debug(f"Released agent instance: {agent_id}")

    def list_available(self) -> list[str]:
        """List all registered agent IDs.
        
        Returns:
            List of agent IDs
        """
        return list(self._agents.keys())

    def load_modular_agent(
        self,
        agent_id: str,
        module_path: str,
        class_name: str
    ) -> None:
        """Load an agent from a module (modular loading).
        
        Enables discovering agents from:
        - examples/invoice_agent
        - custom_agents/my_agent
        - third-party packages
        
        Args:
            agent_id: Identifier for agent
            module_path: Module path (e.g., "examples.invoice_agent.agent")
            class_name: Class name (e.g., "InvoiceAgent")
            
        Raises:
            ImportError: If module not found
            AttributeError: If class not found in module
        """
        try:
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
            self.register(agent_id, agent_class)
            logger.info(f"Loaded modular agent: {agent_id} from {module_path}")
        except ImportError as e:
            logger.error(f"Failed to import {module_path}: {e}")
            raise
        except AttributeError as e:
            logger.error(f"Class {class_name} not found in {module_path}: {e}")
            raise

    def discover_agents(self, package_path: str) -> Dict[str, str]:
        """Discover available agents in a package.
        
        Args:
            package_path: Package path (e.g., "examples")
            
        Returns:
            Dict of {agent_id: module_path}
        """
        discovered = {}
        
        try:
            pkg = importlib.import_module(package_path)
            pkg_dir = Path(pkg.__file__).parent
            
            # Look for agent.py files
            for agent_dir in pkg_dir.glob("*/agent.py"):
                parent = agent_dir.parent.name
                module_path = f"{package_path}.{parent}.agent"
                discovered[parent] = module_path
                logger.debug(f"Discovered agent: {parent}")
        except Exception as e:
            logger.warning(f"Failed to discover agents in {package_path}: {e}")
        
        return discovered

    def __repr__(self) -> str:
        registered = len(self._agents)
        cached = len(self._instances)
        return f"AgentRegistry(registered={registered}, cached={cached})"


# Global registry instance
_registry = AgentRegistry()


def get_registry() -> AgentRegistry:
    """Get the global agent registry.
    
    Returns:
        AgentRegistry instance
    """
    return _registry


# Auto-load core agents on module import
def _init_core_agents():
    """Initialize core agents in registry."""
    try:
        from examples.invoice_agent import InvoiceAgent
        _registry.register("invoice-agent", InvoiceAgent)
        logger.debug("Loaded core agent: invoice-agent")
    except ImportError:
        logger.debug("invoice-agent not available for loading")
    except Exception as e:
        logger.warning(f"Failed to load core agents: {e}")


# Initialize on import
_init_core_agents()
