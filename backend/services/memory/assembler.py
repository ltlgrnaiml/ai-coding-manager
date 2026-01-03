"""Memory Architecture - Context Assembly Engine.

Deterministic context assembly with budget allocation, scoring, and compression.
"""

import hashlib
import json
import logging
import time
from datetime import datetime
from typing import Optional

from .models import (
    Memory, MemorySession, MemoryType, MessageRole,
    AssembledContext, ContextSection, ContextSectionType,
    AssemblyOptions, DebugInfo, TokenAttribution, MemoryPriority,
)
from . import database as db

logger = logging.getLogger(__name__)


# Token estimation (rough approximation, can be replaced with tiktoken)
def estimate_tokens(text: str) -> int:
    """Estimate token count for text (approx 4 chars per token)."""
    return max(1, len(text) // 4)


def count_message_tokens(messages: list[dict]) -> int:
    """Count tokens in a list of messages."""
    total = 0
    for msg in messages:
        total += estimate_tokens(msg.get("content", ""))
        total += 4  # Role and formatting overhead
    return total


class MemoryCandidate:
    """A candidate memory for inclusion in context."""
    
    def __init__(
        self,
        memory: Memory,
        section_type: ContextSectionType,
        score: float = 0.0,
        relevance: float = 0.0,
        recency: float = 0.0,
    ):
        self.memory = memory
        self.section_type = section_type
        self.score = score
        self.relevance = relevance
        self.recency = recency
        self.included = False
        self.exclusion_reason: Optional[str] = None
    
    @property
    def priority(self) -> float:
        """Combined priority score."""
        base_priority = self.memory.priority / 100.0
        return base_priority * 0.4 + self.relevance * 0.3 + self.recency * 0.2 + self.score * 0.1


class ContextAssembler:
    """Assembles optimal context from memory stores."""
    
    def __init__(self, options: Optional[AssemblyOptions] = None):
        self.options = options or AssemblyOptions()
        self._cache_hits = 0
        self._cache_misses = 0
    
    def assemble(
        self,
        session_id: str,
        user_message: str,
        model_id: str,
        token_budget: int,
        system_prompt: Optional[str] = None,
    ) -> AssembledContext:
        """
        Assemble context for LLM call.
        
        This is the core algorithm - deterministic and fully observable.
        """
        start_time = time.time()
        
        # Phase 1: Gather all candidates
        candidates = self._gather_candidates(session_id, user_message, system_prompt)
        
        # Phase 2: Score and rank candidates
        scored = self._score_candidates(candidates, user_message)
        
        # Phase 3: Allocate budget to sections
        budget_allocation = self._allocate_budget(token_budget)
        
        # Phase 4: Select candidates within budget
        selected = self._select_within_budget(scored, budget_allocation)
        
        # Phase 5: Build sections
        sections = self._build_sections(selected, user_message)
        
        # Phase 6: Build final messages
        messages = self._build_messages(sections)
        
        # Phase 7: Calculate totals
        tokens_used = sum(s.tokens for s in sections)
        
        # Phase 8: Build debug info
        assembly_time_ms = (time.time() - start_time) * 1000
        debug_info = self._build_debug_info(
            candidates, selected, sections, assembly_time_ms
        )
        
        # Phase 9: Create assembled context
        context = AssembledContext(
            session_id=session_id,
            model_id=model_id,
            token_budget=token_budget,
            tokens_used=tokens_used,
            sections=sections,
            messages=messages,
            debug_info=debug_info,
        )
        
        # Phase 10: Save for debugging/replay
        db.save_context(context)
        
        logger.info(
            f"Assembled context: {tokens_used}/{token_budget} tokens "
            f"({context.budget_utilization:.1%}), {len(messages)} messages, "
            f"{assembly_time_ms:.1f}ms"
        )
        
        return context
    
    def _gather_candidates(
        self,
        session_id: str,
        user_message: str,
        system_prompt: Optional[str],
    ) -> list[MemoryCandidate]:
        """Gather all candidate memories for inclusion."""
        candidates = []
        
        # 1. System prompt (if provided)
        if system_prompt:
            system_memory = Memory(
                type=MemoryType.SYSTEM,
                role=MessageRole.SYSTEM,
                content=system_prompt,
                tokens=estimate_tokens(system_prompt),
                priority=MemoryPriority.CRITICAL,
            )
            candidates.append(MemoryCandidate(
                system_memory, ContextSectionType.SYSTEM, score=1.0
            ))
        
        # 2. Pinned memories (user-specified)
        pinned = db.get_session_memories(session_id, pinned_only=True, limit=20)
        for mem in pinned:
            candidates.append(MemoryCandidate(
                mem, ContextSectionType.PINNED, score=0.9
            ))
        
        # 3. Recent chat history
        recent = db.get_recent_memories(session_id, limit=self.options.history_limit)
        recency_weight = 1.0
        for i, mem in enumerate(reversed(recent)):
            candidates.append(MemoryCandidate(
                mem, ContextSectionType.HISTORY,
                score=0.5,
                recency=recency_weight,
            ))
            recency_weight *= 0.95  # Decay for older messages
        
        # 4. Session summary (if exists)
        session = db.get_session(session_id)
        if session and session.summary and self.options.include_summary:
            summary_memory = Memory(
                type=MemoryType.SUMMARY,
                role=MessageRole.SYSTEM,
                content=f"Previous conversation summary:\n{session.summary}",
                tokens=estimate_tokens(session.summary),
                priority=MemoryPriority.MEDIUM,
            )
            candidates.append(MemoryCandidate(
                summary_memory, ContextSectionType.SUMMARY, score=0.6
            ))
        
        # 5. User's current message (always included)
        current_message = Memory(
            type=MemoryType.MESSAGE,
            role=MessageRole.USER,
            content=user_message,
            tokens=estimate_tokens(user_message),
            priority=MemoryPriority.CRITICAL,
            session_id=session_id,
        )
        candidates.append(MemoryCandidate(
            current_message, ContextSectionType.USER_MESSAGE, score=1.0
        ))
        
        # 6. RAG results (if enabled)
        if self.options.rag_sources:
            rag_memories = self._get_rag_candidates(user_message, session_id)
            for mem in rag_memories:
                candidates.append(MemoryCandidate(
                    mem, ContextSectionType.RAG, score=0.7
                ))
        
        return candidates
    
    def _get_rag_candidates(self, query: str, session_id: str) -> list[Memory]:
        """Get RAG results from configured sources."""
        results = []
        
        # Search memories via FTS
        fts_results = db.search_memories_fts(query, limit=self.options.max_rag_results)
        for mem in fts_results:
            # Don't include if it's from current session (already in history)
            if mem.session_id != session_id:
                results.append(mem)
        
        # TODO: Add research paper search integration
        # TODO: Add trace search integration
        # TODO: Add code chunk search integration
        
        return results[:self.options.max_rag_results]
    
    def _score_candidates(
        self,
        candidates: list[MemoryCandidate],
        user_message: str,
    ) -> list[MemoryCandidate]:
        """Score candidates for relevance."""
        query_terms = set(user_message.lower().split())
        
        for candidate in candidates:
            # Simple relevance scoring (keyword overlap)
            content_terms = set(candidate.memory.content.lower().split())
            overlap = len(query_terms & content_terms)
            candidate.relevance = min(1.0, overlap / max(len(query_terms), 1))
        
        # Sort by priority (descending)
        return sorted(candidates, key=lambda c: c.priority, reverse=True)
    
    def _allocate_budget(self, total_budget: int) -> dict[ContextSectionType, int]:
        """Allocate token budget to sections."""
        return {
            ContextSectionType.SYSTEM: int(total_budget * self.options.system_budget_pct),
            ContextSectionType.WORKING_MEMORY: int(total_budget * self.options.working_memory_budget_pct),
            ContextSectionType.USER_MESSAGE: int(total_budget * self.options.user_message_budget_pct),
            ContextSectionType.PINNED: int(total_budget * self.options.pinned_budget_pct),
            ContextSectionType.RAG: int(total_budget * self.options.rag_budget_pct),
            ContextSectionType.HISTORY: int(total_budget * self.options.history_budget_pct),
            ContextSectionType.SUMMARY: int(total_budget * self.options.summary_budget_pct),
        }
    
    def _select_within_budget(
        self,
        candidates: list[MemoryCandidate],
        budget: dict[ContextSectionType, int],
    ) -> list[MemoryCandidate]:
        """Select candidates that fit within budget."""
        used: dict[ContextSectionType, int] = {t: 0 for t in ContextSectionType}
        selected = []
        
        for candidate in candidates:
            section_type = candidate.section_type
            available = budget.get(section_type, 0)
            tokens_needed = candidate.memory.tokens
            
            # Critical items always included
            if candidate.memory.priority >= MemoryPriority.CRITICAL:
                candidate.included = True
                selected.append(candidate)
                used[section_type] = used.get(section_type, 0) + tokens_needed
                continue
            
            # Check if fits in budget
            if used.get(section_type, 0) + tokens_needed <= available:
                candidate.included = True
                selected.append(candidate)
                used[section_type] = used.get(section_type, 0) + tokens_needed
            else:
                candidate.exclusion_reason = f"Budget exceeded for {section_type.value}"
        
        return selected
    
    def _build_sections(
        self,
        selected: list[MemoryCandidate],
        user_message: str,
    ) -> list[ContextSection]:
        """Build context sections from selected candidates."""
        # Group by section type
        by_type: dict[ContextSectionType, list[MemoryCandidate]] = {}
        for candidate in selected:
            if candidate.section_type not in by_type:
                by_type[candidate.section_type] = []
            by_type[candidate.section_type].append(candidate)
        
        sections = []
        
        # Build each section
        for section_type, candidates in by_type.items():
            # Sort candidates within section (by recency for history, by score for others)
            if section_type == ContextSectionType.HISTORY:
                sorted_candidates = sorted(
                    candidates,
                    key=lambda c: c.memory.created_at if c.memory.created_at else datetime.min
                )
            else:
                sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
            
            # Combine content
            content_parts = [c.memory.content for c in sorted_candidates]
            combined_content = "\n\n".join(content_parts)
            
            total_tokens = sum(c.memory.tokens for c in sorted_candidates)
            avg_priority = sum(c.memory.priority for c in sorted_candidates) // len(sorted_candidates)
            source_ids = [c.memory.id for c in sorted_candidates]
            
            sections.append(ContextSection(
                type=section_type,
                content=combined_content,
                tokens=total_tokens,
                priority=avg_priority,
                source_ids=source_ids,
            ))
        
        return sections
    
    def _build_messages(self, sections: list[ContextSection]) -> list[dict]:
        """Build LLM-ready messages from sections."""
        messages = []
        
        # Order: system, summary, rag, pinned, history, user_message
        section_order = [
            ContextSectionType.SYSTEM,
            ContextSectionType.SUMMARY,
            ContextSectionType.RAG,
            ContextSectionType.PINNED,
            ContextSectionType.WORKING_MEMORY,
            ContextSectionType.HISTORY,
            ContextSectionType.USER_MESSAGE,
        ]
        
        sections_by_type = {s.type: s for s in sections}
        
        for section_type in section_order:
            section = sections_by_type.get(section_type)
            if not section:
                continue
            
            # Determine role based on section type
            if section_type in (ContextSectionType.SYSTEM, ContextSectionType.SUMMARY,
                               ContextSectionType.RAG, ContextSectionType.PINNED):
                role = "system"
            elif section_type == ContextSectionType.USER_MESSAGE:
                role = "user"
            elif section_type == ContextSectionType.HISTORY:
                # History needs to be split into individual messages
                # For now, include as system context
                role = "system"
                section.content = f"Conversation history:\n{section.content}"
            else:
                role = "assistant"
            
            messages.append({
                "role": role,
                "content": section.content,
            })
        
        return messages
    
    def _build_debug_info(
        self,
        all_candidates: list[MemoryCandidate],
        selected: list[MemoryCandidate],
        sections: list[ContextSection],
        assembly_time_ms: float,
    ) -> DebugInfo:
        """Build debug information for the assembly."""
        # Token attributions
        attributions = []
        total_tokens = sum(s.tokens for s in sections)
        
        for section in sections:
            attributions.append(TokenAttribution(
                section_type=section.type,
                tokens=section.tokens,
                percentage=section.tokens / max(total_tokens, 1),
                source_count=len(section.source_ids),
                sources=section.source_ids[:5],  # Limit sources for readability
            ))
        
        # Exclusion reasons
        excluded_reasons: dict[str, int] = {}
        for candidate in all_candidates:
            if not candidate.included and candidate.exclusion_reason:
                reason = candidate.exclusion_reason
                excluded_reasons[reason] = excluded_reasons.get(reason, 0) + 1
        
        return DebugInfo(
            candidates_considered=len(all_candidates),
            candidates_included=len(selected),
            candidates_excluded=len(all_candidates) - len(selected),
            compression_applied=False,
            token_attributions=attributions,
            assembly_time_ms=assembly_time_ms,
            cache_hits=self._cache_hits,
            cache_misses=self._cache_misses,
            excluded_reasons=excluded_reasons,
        )


# =============================================================================
# Convenience Functions
# =============================================================================

def assemble_context(
    session_id: str,
    user_message: str,
    model_id: str,
    token_budget: int,
    system_prompt: Optional[str] = None,
    options: Optional[AssemblyOptions] = None,
) -> AssembledContext:
    """Convenience function to assemble context."""
    assembler = ContextAssembler(options)
    return assembler.assemble(
        session_id=session_id,
        user_message=user_message,
        model_id=model_id,
        token_budget=token_budget,
        system_prompt=system_prompt,
    )


def replay_context(context_id: str, modifications: Optional[dict] = None) -> Optional[AssembledContext]:
    """Replay a previous context assembly, optionally with modifications."""
    original = db.get_context(context_id)
    if not original:
        return None
    
    # If no modifications, return original
    if not modifications:
        return original
    
    # Re-assemble with modifications
    options = AssemblyOptions()
    if "options" in modifications:
        options = AssemblyOptions(**modifications["options"])
    
    return assemble_context(
        session_id=modifications.get("session_id", original.session_id),
        user_message=modifications.get("user_message", ""),
        model_id=modifications.get("model_id", original.model_id),
        token_budget=modifications.get("token_budget", original.token_budget),
        system_prompt=modifications.get("system_prompt"),
        options=options,
    )
