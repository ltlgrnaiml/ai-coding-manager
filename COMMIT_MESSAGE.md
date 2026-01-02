# Git Commit Message

## Commit Title

```
feat: Initialize AICM repo with UAM foundation from engineering-tools
```

## Commit Body

```
Migrate critical discussion files from engineering-tools to establish
the AI Coding Management Hub (AICM) as a standalone project.

## What Changed

### Migrated Files (.discussions/)
- DISC-011: Unified Artifact Model (UAM) - Umbrella
- DISC-012: Plan Artifact Structure & Lifecycle
- DISC-013: Quality Scoring System
- DISC-014: Primary Chain Validation
- DISC-015: AI-Native Documentation Architecture
- DISC-017: AI Coding Management Hub (AICM)
- DISC-018: Meta-Agent Self-Improvement System (deferred)
- DISC_TEMPLATE.md
- INDEX.md

### Key Decisions Carried Forward
- UAM Six Pillars: EXPLORE, DECIDE, DEFINE, SHAPE, EXECUTE, GUIDE
- Primary Chain Model: Every artifact has ONE parent
- L3-First Plans: Default to procedural granularity
- Score Provenance: Content-addressed quality scoring
- AICM Vision: Standalone tool for AI-assisted artifact management

## Project Repo Refactor

This commit marks the beginning of the AICM standalone project:

1. **ai-coding-manager** = New standalone tool repo
2. **engineering-tools** = Becomes first "customer project" of AICM
3. **Relationship**: AICM manages artifacts, engineering-tools uses them

### Migration Strategy
- All migrated code is 100% FUNGIBLE - needs refactoring
- Every file must be modified before project completion
- Files NOT modified require manual review
- Full asset migration will follow (UI, services, knowledge)
```

---

# Breaking Changes for engineering-tools

## Overview

The `engineering-tools` project is being refactored. The following breaking changes will occur:

## 1. Documentation System Overhaul

| Change | Impact |
|--------|--------|
| UAM adoption | ALL documents must comply with Six Pillars model |
| Primary Chain enforcement | ALL artifacts need `source_*` fields |
| Quality scoring | ALL artifacts will be graded |

## 2. Code Refactoring Required

| Component | Status | Action Required |
|-----------|--------|-----------------|
| DAT (Data Aggregator) | Stays in engineering-tools | Refactor for UAM compliance |
| SOV (SOV Analyzer) | Stays in engineering-tools | Refactor for UAM compliance |
| PPTX (PPTX Generator) | Stays in engineering-tools | Refactor for UAM compliance |
| DevTools UI | Migrates to AICM | Will be refactored |
| Knowledge Services | Migrates to AICM | Will be refactored |
| Workflow Services | Migrates to AICM | Will be refactored |

## 3. Document Compliance Required

All 33+ orphan ADRs need `source_discussion` field added. Options:
- Create retroactive DISCs for groups of related ADRs
- Add `source_discussion: "pre-uam"` marker with note
- Review each for "One Thing" rule violations

## 4. Folder Structure Changes

```
engineering-tools/
├── apps/
│   ├── data_aggregator/    # STAYS - DAT domain
│   ├── sov_analyzer/       # STAYS - SOV domain
│   └── pptx_generator/     # STAYS - PPTX domain
├── shared/contracts/       # STAYS - but needs UAM compliance
├── .discussions/           # STAYS - but needs UAM compliance
├── .adrs/                  # STAYS - needs source_discussion
└── gateway/                # PARTIAL MIGRATION to AICM

ai-coding-manager/          # NEW STANDALONE REPO
├── .discussions/           # UAM foundation (MIGRATED)
├── backend/                # Will receive workflow/devtools/knowledge
├── frontend/               # Will receive DevToolsPage + components
└── contracts/              # Will receive UAM schemas
```

## 5. Timeline

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | DISC migration | ✅ COMPLETE |
| Phase 2 | Contract/schema migration | PENDING |
| Phase 3 | Backend service migration | PENDING |
| Phase 4 | Frontend component migration | PENDING |
| Phase 5 | engineering-tools UAM compliance | PENDING |

---

## Session Reference

- **Session**: SESSION_022
- **Date**: 2026-01-01
- **Author**: Mycahya Eggleston + AI Assistant
