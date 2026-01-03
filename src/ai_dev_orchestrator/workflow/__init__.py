"""Workflow module - Plan and artifact management.

This module provides:
- Plan creation and management (L1/L2/L3 granularity)
- Discussion and ADR creation
- Session management for AI continuity
"""

from ai_dev_orchestrator.workflow.plan_manager import (
    create_plan,
    load_plan,
    save_plan,
    get_next_plan_id,
)
from ai_dev_orchestrator.workflow.discussion_manager import (
    create_discussion,
    load_discussion,
    save_discussion,
    get_next_discussion_id,
)
from ai_dev_orchestrator.workflow.session_manager import (
    create_session,
    get_current_session,
    get_next_session_id,
)

__all__ = [
    # Plans
    "create_plan",
    "load_plan",
    "save_plan",
    "get_next_plan_id",
    # Discussions
    "create_discussion",
    "load_discussion",
    "save_discussion",
    "get_next_discussion_id",
    # Sessions
    "create_session",
    "get_current_session",
    "get_next_session_id",
]
