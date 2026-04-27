"""Agent endpoints - ADK-aligned."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from app.agents.registry import get_registry
from app.agents.base import ConfiguredAgent, AgentRunner
from app.agents.base.types import TurnResult
from app.api.deps import require_api_key
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class AgentRunRequest(BaseModel):
    """Request to run an agent."""

    agent_id: str = Field(..., description="Agent identifier")
    input: str = Field(..., description="User input")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    system_prompt: Optional[str] = Field(None, description="Override system prompt")


class AgentRunByIdRequest(BaseModel):
    """Request to run an agent identified in the route path."""

    input: str = Field(..., description="User input")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    system_prompt: Optional[str] = Field(None, description="Override system prompt")


class AgentRunResponse(BaseModel):
    """Agent run response (turn result)."""

    agent_id: str = Field(..., description="Agent identifier")
    output: str = Field(..., description="Agent response")
    status: str = Field(default="success", description="Execution status")
    execution_time_ms: float = Field(..., description="Execution time")
    model_calls: int = Field(default=0, description="LLM calls made")
    tool_calls: int = Field(default=0, description="Tool calls made")
    error: Optional[str] = Field(None, description="Error if failed")


class AgentInfoResponse(BaseModel):
    """Agent information."""

    agent_id: str = Field(..., description="Agent identifier")
    name: str = Field(..., description="Agent name")
    available: bool = Field(..., description="Whether agent is available")


class AgentContextResponse(BaseModel):
    """Agent context/state response."""

    agent_id: str = Field(..., description="Agent identifier")
    context: Dict[str, Any] = Field(..., description="Agent context")
    has_context: bool = Field(..., description="Whether agent has context")


@router.post("/run", response_model=AgentRunResponse, tags=["agent"])
async def run_agent(request: AgentRunRequest, _: str = Depends(require_api_key)):
    """Run an agent turn (ADK-aligned turn execution).
    
    Executes:
    1. Routing - determine execution mode
    2. Context - check state, avoid LLM calls if possible
    3. Message building - construct optimized prompt
    4. Execution - call LLM provider
    5. State update - save snapshot
    
    Args:
        request: AgentRunRequest
        
    Returns:
        AgentRunResponse with turn result
    """
    try:
        registry = get_registry()
        
        # Instantiate agent
        agent = registry.instantiate(
            request.agent_id,
            conversation_id=request.conversation_id,
        )
        
        if not isinstance(agent, ConfiguredAgent):
            raise TypeError(f"Agent {request.agent_id} is not a ConfiguredAgent")
        
        runner = AgentRunner(agent)
        turn_result: TurnResult = await runner.run_turn(request.input)
        
        logger.info(
            f"Agent {request.agent_id} executed turn "
            f"(success={turn_result.success}, time={turn_result.execution_time_ms:.1f}ms)"
        )
        
        # Return response
        return AgentRunResponse(
            agent_id=request.agent_id,
            output=turn_result.output,
            status="success" if turn_result.success else "failed",
            execution_time_ms=turn_result.execution_time_ms,
            model_calls=turn_result.model_calls,
            tool_calls=turn_result.tool_calls,
            error=turn_result.error,
        )
        
    except ValueError as e:
        logger.error(f"Agent not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except TypeError as e:
        logger.error(f"Invalid agent type: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/run", response_model=AgentRunResponse, tags=["agent"])
async def run_agent_by_id(
    agent_id: str,
    request: AgentRunByIdRequest,
    _: str = Depends(require_api_key),
):
    """Run a turn for a specific agent ID provided in the URL path."""
    return await run_agent(
        AgentRunRequest(
            agent_id=agent_id,
            input=request.input,
            conversation_id=request.conversation_id,
            system_prompt=request.system_prompt,
        ),
        _,
    )


@router.get("", tags=["agent"])
async def list_agents():
    """List available agents.
    
    Returns:
        List of agent identifiers
    """
    registry = get_registry()
    agents = registry.list_available()
    return {
        "agents": agents,
        "count": len(agents),
    }


@router.get("/{agent_id}", response_model=AgentInfoResponse, tags=["agent"])
async def get_agent_info(agent_id: str):
    """Get agent information.
    
    Args:
        agent_id: Agent identifier
        
    Returns:
        AgentInfoResponse
    """
    registry = get_registry()
    available_agents = registry.list_available()
    is_available = agent_id in available_agents

    return AgentInfoResponse(
        agent_id=agent_id,
        name=agent_id.replace("-", " ").title(),
        available=is_available,
    )


@router.get("/{agent_id}/context", response_model=AgentContextResponse, tags=["agent"])
async def get_agent_context(agent_id: str):
    """Get agent context/state.
    
    Returns current agent context if available.
    This avoids unnecessary LLM calls by checking cached state.
    
    Args:
        agent_id: Agent identifier
        
    Returns:
        AgentContextResponse with context
    """
    try:
        registry = get_registry()
        instance = registry.get_instance(agent_id)
        
        if not instance:
            raise HTTPException(
                status_code=404,
                detail=f"Agent {agent_id} not instantiated"
            )
        
        # Get context - implementation depends on agent type
        context = {}
        has_context = False
        
        if hasattr(instance, "get_context"):
            context = instance.get_context()
            has_context = bool(context)
        
        return AgentContextResponse(
            agent_id=agent_id,
            context=context,
            has_context=has_context,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent context: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/reset", tags=["agent"])
async def reset_agent(agent_id: str, _: str = Depends(require_api_key)):
    """Reset agent state.
    
    Clears message history and resets all state.
    
    Args:
        agent_id: Agent identifier
        
    Returns:
        Reset confirmation
    """
    try:
        registry = get_registry()
        instance = registry.get_instance(agent_id)
        
        if not instance:
            raise HTTPException(
                status_code=404,
                detail=f"Agent {agent_id} not instantiated"
            )
        
        instance.reset()
        logger.info(f"Agent {agent_id} reset")
        
        return {
            "agent_id": agent_id,
            "status": "reset",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))
