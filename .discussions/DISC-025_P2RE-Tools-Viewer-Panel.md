# P2RE Tools Viewer Panel

> **ID**: DISC-025
> **Status**: draft
> **Created**: 2025-01-03

---

## Summary

Embedded viewer panel for P2RE (Prompts to Response Ecosystem) tools, starting with Phoenix trace inspection and expandable to include prompt optimization, quality grading, hallucination detection, and context optimization tools.

---

## Context

With P2RE trace capture now in place, we need a way to:
1. Quickly view and inspect traces without leaving the app
2. Access Phoenix UI for detailed trace analysis
3. Provide an extensible framework for future P2RE tools

This is the **OBSERVE pillar** user interface - making LLM observability accessible within the workflow.

---

## Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | Embedded iframe viewer for Phoenix UI (localhost:6006) | High |
| FR-02 | Tool selector dropdown/tabs for switching between tools | High |
| FR-03 | Dedicated sidebar tab or panel for P2RE tools | High |
| FR-04 | Extensible architecture for adding new tools | Medium |
| FR-05 | Quick jump to specific trace from trace list | Medium |

---

## Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR-01 | Responsive panel that resizes with window | Medium |
| NFR-02 | Fast loading with loading state indicators | Medium |
| NFR-03 | Graceful fallback if Phoenix unavailable | Low |

---

## Planned Tools (Roadmap)

1. **Phoenix Trace Viewer** (v1 - now)
   - Embedded Phoenix UI for trace inspection
   
2. **Prompt Optimizer** (future)
   - Analyze prompts for clarity, token efficiency
   - Suggest improvements
   
3. **Quality/Accuracy Grader** (future)
   - Score responses for relevance, accuracy
   - Human feedback collection
   
4. **Hallucination Detector** (future)
   - Flag potentially hallucinated content
   - Cross-reference with knowledge base
   
5. **Context Optimizer** (future)
   - Analyze RAG context relevance
   - Suggest context window improvements

---

## Open Questions

- [ ] Should tools open in a panel, modal, or dedicated route?
- [ ] How to handle Phoenix authentication if needed later?
- [ ] Should we build native trace viewer or rely on Phoenix?

---

## Decision

Start with embedded Phoenix iframe in a new sidebar tab. Use extensible tool selector pattern for future tools.

---

## Next Steps

- [x] Create DISC documentation
- [ ] Build P2REToolsPanel component with iframe
- [ ] Add "Tools" tab to SidebarTabs
- [ ] Add tool selector UI for future expansion
- [ ] Test Phoenix embed functionality
