# ADR-0001: ADK-First Runtime

**Status:** Accepted  
**Date:** 2025  
**Deciders:** Core team

---

## Context

We need a runtime for executing AI agents that provides:

1. Predictable, auditable execution flow
2. Hard limits on LLM calls, tool calls, and turn count
3. Anti-loop protection
4. Timeout enforcement
5. A clear mental model for contributors to follow

We evaluated several options:
- **LangChain / LangGraph** — widely used, large ecosystem
- **CrewAI** — multi-agent orchestration
- **AutoGen** — research-oriented multi-agent
- **Custom ADK** — purpose-built for this project's requirements

---

## Decision

We build and use a **custom ADK (Agent Development Kit)** as the primary agent runtime.

Every agent is a `ConfiguredAgent` subclass. Every turn goes through a fixed five-step pipeline:

1. Routing (policy enforcement)
2. Context injection
3. Message building
4. Execution (with timeout)
5. State update

---

## Rationale

### Why not LangChain?

- LangChain's abstractions add significant complexity for straightforward agent patterns
- Execution flow is difficult to audit and reason about
- Rate limits and execution bounds require significant custom wrapping
- The ecosystem changes rapidly, creating maintenance burden
- For this project's scope, the overhead is not justified

### Why not CrewAI / AutoGen?

- Multi-agent orchestration is not the primary use case
- Both frameworks make opinionated decisions about agent communication that conflict with our architecture
- Harder to enforce hard execution limits at the framework level

### Why custom ADK?

- **Full control** over execution flow — every turn is inspectable
- **Hard limits** are first-class, built into `ExecutionPolicy` and `PolicyEnforcer`
- **Anti-loop** detection is built-in via `LoopGuard`
- **Timeout** is enforced at the LLM call level via `asyncio.wait_for`
- **Simplicity** — contributors can read and understand the full execution path in `configured_agent.py`
- **Portability** — skills are independent of the runtime; they can be published to skill registries or used by any agent

---

## Consequences

### Positive

- Clear, auditable execution path
- Hard limits prevent runaway LLM usage
- Skills are portable and testable in isolation
- Contributors have a clear pattern to follow (subclass `ConfiguredAgent`)
- The framework can evolve without breaking agent implementations

### Negative

- No immediate access to the LangChain/LangGraph ecosystem
- Must implement provider integrations ourselves (mitigated by OpenAI-compatible API standard)
- Multi-agent orchestration requires custom implementation if needed

---

## MCP as the external exposure layer

MCP (Model Context Protocol) is used as the **transport** for exposing skills to external clients — not as a business logic layer. This keeps skills portable:

- Skills are called from MCP routes, not the other way around
- Skills have no MCP dependency
- Swapping MCP for a different protocol does not require skill changes

---

## FastAPI as the transport layer

FastAPI is the HTTP API layer only. Route handlers:
1. Validate input (Pydantic)
2. Authenticate (API key)
3. Call the appropriate agent or skill
4. Return the result

No business logic lives in routes. This keeps routes thin and testable.
