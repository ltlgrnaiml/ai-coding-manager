"""Memory Architecture - Agentic Communication Interface.

Shared memory and handoff mechanisms for multi-agent workflows.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

from .models import (
    Memory, MemoryType, MessageRole, MemoryPriority,
    AssembledContext, AssemblyOptions,
    SharedMemoryEntry, AgentScope, AgentHandoff,
)
from . import database as db
from .assembler import assemble_context, estimate_tokens

logger = logging.getLogger(__name__)


class AgentMemoryInterface:
    """
    Interface for agent-to-agent communication via shared memory.
    
    This enables multi-agent workflows where agents can:
    - Share state and observations
    - Hand off tasks to other agents
    - Access specialized context for their role
    """
    
    def __init__(self, agent_id: str, session_id: str):
        self.agent_id = agent_id
        self.session_id = session_id
        self._subscribers: dict[str, list[Callable]] = {}
    
    # =========================================================================
    # Shared Memory Operations
    # =========================================================================
    
    def publish(
        self,
        key: str,
        value: Any,
        scope: AgentScope = AgentScope.SESSION,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """
        Publish data to shared memory.
        
        Args:
            key: Memory key (e.g., "task_plan", "code_review_result")
            value: Any JSON-serializable value
            scope: Visibility scope (private, session, workflow, global)
            ttl_seconds: Time-to-live in seconds (None = no expiry)
        """
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        
        entry = SharedMemoryEntry(
            key=key,
            value=value,
            scope=scope,
            agent_id=self.agent_id,
            expires_at=expires_at,
        )
        
        db.set_shared_memory(entry)
        logger.debug(f"Agent {self.agent_id} published {key} with scope {scope.value}")
        
        # Notify subscribers
        self._notify_subscribers(key, value)
    
    def get(self, key: str, scope: AgentScope = AgentScope.SESSION) -> Optional[Any]:
        """
        Get data from shared memory.
        
        Returns the most recent value for the key within the scope.
        """
        entries = db.get_shared_memory(key, scope)
        
        # Filter expired entries
        now = datetime.utcnow()
        valid_entries = [
            e for e in entries
            if e.expires_at is None or e.expires_at > now
        ]
        
        if not valid_entries:
            return None
        
        # Return most recent
        sorted_entries = sorted(valid_entries, key=lambda e: e.created_at, reverse=True)
        return sorted_entries[0].value
    
    def get_all(self, key: str, scope: AgentScope = AgentScope.SESSION) -> list[SharedMemoryEntry]:
        """Get all entries for a key (from all agents)."""
        entries = db.get_shared_memory(key, scope)
        now = datetime.utcnow()
        return [e for e in entries if e.expires_at is None or e.expires_at > now]
    
    def subscribe(self, key: str, callback: Callable[[str, Any], None]) -> None:
        """
        Subscribe to changes for a key.
        
        The callback receives (key, new_value) when the key is updated.
        Note: This is in-process only; for distributed systems, use a message queue.
        """
        if key not in self._subscribers:
            self._subscribers[key] = []
        self._subscribers[key].append(callback)
    
    def _notify_subscribers(self, key: str, value: Any) -> None:
        """Notify all subscribers of a key change."""
        for callback in self._subscribers.get(key, []):
            try:
                callback(key, value)
            except Exception as e:
                logger.error(f"Subscriber callback error for {key}: {e}")
    
    # =========================================================================
    # Agent Handoff
    # =========================================================================
    
    def handoff(
        self,
        to_agent: str,
        state: dict,
        summary: Optional[str] = None,
    ) -> AgentHandoff:
        """
        Hand off task state to another agent.
        
        Args:
            to_agent: ID of the receiving agent
            state: State dictionary to transfer
            summary: Optional human-readable summary
        
        Returns:
            The handoff record
        """
        handoff = AgentHandoff(
            from_agent=self.agent_id,
            to_agent=to_agent,
            session_id=self.session_id,
            state=state,
            summary=summary,
        )
        
        db.save_handoff(handoff)
        
        # Also publish to shared memory for immediate access
        self.publish(
            f"handoff:{to_agent}",
            {
                "handoff_id": handoff.id,
                "from_agent": self.agent_id,
                "state": state,
                "summary": summary,
            },
            scope=AgentScope.SESSION,
            ttl_seconds=3600,  # 1 hour
        )
        
        logger.info(f"Agent {self.agent_id} handed off to {to_agent}")
        return handoff
    
    def receive_handoff(self) -> Optional[dict]:
        """
        Receive any pending handoff for this agent.
        
        Returns:
            Handoff state dict or None if no pending handoff
        """
        handoff_data = self.get(f"handoff:{self.agent_id}", AgentScope.SESSION)
        return handoff_data
    
    # =========================================================================
    # Agent Context
    # =========================================================================
    
    def get_context(
        self,
        user_message: str,
        model_id: str,
        token_budget: int,
        role_prompt: Optional[str] = None,
        options: Optional[AssemblyOptions] = None,
    ) -> AssembledContext:
        """
        Get context optimized for this agent's role.
        
        Includes:
        - Agent-specific system prompt (role)
        - Relevant shared memory
        - Session history filtered for relevance
        - Any pending handoff state
        """
        if options is None:
            options = AssemblyOptions()
        
        # Build agent-specific system prompt
        system_parts = []
        
        if role_prompt:
            system_parts.append(role_prompt)
        else:
            system_parts.append(f"You are agent '{self.agent_id}' in a multi-agent workflow.")
        
        # Include handoff context if present
        handoff = self.receive_handoff()
        if handoff:
            system_parts.append(f"\nHandoff from {handoff.get('from_agent')}:")
            if handoff.get('summary'):
                system_parts.append(handoff['summary'])
            system_parts.append(f"State: {handoff.get('state')}")
        
        # Include relevant shared memory
        shared_context = self._get_shared_context()
        if shared_context:
            system_parts.append("\nShared context from other agents:")
            system_parts.append(shared_context)
        
        system_prompt = "\n".join(system_parts)
        
        return assemble_context(
            session_id=self.session_id,
            user_message=user_message,
            model_id=model_id,
            token_budget=token_budget,
            system_prompt=system_prompt,
            options=options,
        )
    
    def _get_shared_context(self) -> str:
        """Get relevant shared memory as context string."""
        # Get recent session-scoped shared entries
        conn = db.get_connection()
        try:
            rows = conn.execute(
                """SELECT key, value, agent_id, created_at FROM shared_memory
                   WHERE scope = 'session'
                   ORDER BY created_at DESC LIMIT 10"""
            ).fetchall()
            
            if not rows:
                return ""
            
            import json
            parts = []
            for row in rows:
                parts.append(f"- {row['key']} (from {row['agent_id']}): {row['value'][:100]}")
            
            return "\n".join(parts)
        finally:
            conn.close()
    
    # =========================================================================
    # Agent Observations
    # =========================================================================
    
    def observe(self, observation: str, importance: int = MemoryPriority.MEDIUM) -> Memory:
        """
        Record an observation from this agent.
        
        Observations are stored as memories and can be used in future context assembly.
        """
        memory = Memory(
            session_id=self.session_id,
            type=MemoryType.AGENT_STATE,
            role=MessageRole.ASSISTANT,
            content=f"[Agent: {self.agent_id}] {observation}",
            tokens=estimate_tokens(observation),
            priority=importance,
            metadata={"agent_id": self.agent_id},
        )
        
        return db.add_memory(memory)
    
    def get_observations(self, limit: int = 20) -> list[Memory]:
        """Get recent observations from this agent."""
        memories = db.get_session_memories(
            session_id=self.session_id,
            types=[MemoryType.AGENT_STATE],
            limit=limit,
        )
        
        return [m for m in memories if m.metadata.get("agent_id") == self.agent_id]


# =============================================================================
# Workflow Coordinator
# =============================================================================

class WorkflowCoordinator:
    """
    Coordinates multi-agent workflows.
    
    Manages agent lifecycle, routing, and shared state.
    """
    
    def __init__(self, workflow_id: str, session_id: str):
        self.workflow_id = workflow_id
        self.session_id = session_id
        self.agents: dict[str, AgentMemoryInterface] = {}
        self._current_agent: Optional[str] = None
    
    def register_agent(self, agent_id: str) -> AgentMemoryInterface:
        """Register an agent in the workflow."""
        if agent_id in self.agents:
            return self.agents[agent_id]
        
        interface = AgentMemoryInterface(agent_id, self.session_id)
        self.agents[agent_id] = interface
        
        # Publish agent registration
        interface.publish(
            "agent:registered",
            {"agent_id": agent_id, "workflow_id": self.workflow_id},
            scope=AgentScope.WORKFLOW,
        )
        
        logger.info(f"Registered agent {agent_id} in workflow {self.workflow_id}")
        return interface
    
    def get_agent(self, agent_id: str) -> Optional[AgentMemoryInterface]:
        """Get an agent's memory interface."""
        return self.agents.get(agent_id)
    
    def set_current_agent(self, agent_id: str) -> None:
        """Set the currently active agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not registered")
        self._current_agent = agent_id
    
    def route_to(self, agent_id: str, task: str, context: dict) -> None:
        """Route a task to a specific agent."""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not registered")
        
        current = self.agents.get(self._current_agent) if self._current_agent else None
        
        if current:
            current.handoff(
                to_agent=agent_id,
                state={"task": task, **context},
                summary=f"Task routed: {task}",
            )
        else:
            # No current agent, just publish directly
            target = self.agents[agent_id]
            target.publish(
                f"handoff:{agent_id}",
                {"task": task, **context},
                scope=AgentScope.SESSION,
            )
        
        self._current_agent = agent_id
    
    def get_workflow_state(self) -> dict:
        """Get current workflow state."""
        return {
            "workflow_id": self.workflow_id,
            "session_id": self.session_id,
            "agents": list(self.agents.keys()),
            "current_agent": self._current_agent,
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def create_agent(agent_id: str, session_id: str) -> AgentMemoryInterface:
    """Create an agent memory interface."""
    return AgentMemoryInterface(agent_id, session_id)


def create_workflow(workflow_id: str, session_id: str) -> WorkflowCoordinator:
    """Create a workflow coordinator."""
    return WorkflowCoordinator(workflow_id, session_id)
