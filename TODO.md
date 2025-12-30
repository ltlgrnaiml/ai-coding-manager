# AI Dev Orchestrator - TODO & Roadmap

> Extracted from engineering-tools on December 30, 2025

---

## Origin & Motivation

This project was born from **EXP-001: L1 vs L3 Plan Granularity Experiment**, which tested 8 AI models across two plan granularity levels to determine optimal cost/quality tradeoffs.

### Key Findings That Motivated This Project

1. **L3 plans reduce stochastic variation by 50%+** - Budget models match premium quality
2. **All 8 models achieved 100% task completion** - Plan structure matters more than model
3. **3-6x cost savings** possible with structured plans on cheaper models
4. **L2 (middle ground) identified** - Constraints without full procedures

### The Vision

Create a **standalone framework** for structured AI-assisted code development that:
- Helps developers get consistent, high-quality code from AI assistants
- Provides tiered plan granularity (L1/L2/L3) matched to model capability
- Enables A/B testing of AI models with reproducible experiments
- Tracks session continuity across AI conversations

---

## Current State (What's Done)

### ✅ Core Infrastructure

- [x] Project structure created
- [x] `contracts/plan_schema.py` - Full L1/L2/L3 system with EXP-001 improvements
- [x] `AGENTS.md` - Global AI instructions
- [x] `README.md` - Getting started guide
- [x] `pyproject.toml` - Minimal dependencies (just pydantic)
- [x] `.gitignore` - Standard Python ignores

### ✅ Workflow Infrastructure

- [x] `.discussions/` - Design conversation directory with AGENTS.md
- [x] `.plans/` - Execution plan directory with README
- [x] `.sessions/` - Session continuity directory with README
- [x] `.questions/` - Open questions directory with README
- [x] `.adrs/` - ADR directory with INDEX.md

### ✅ Experiment Framework

- [x] `.experiments/EXP-001_L1-vs-L3/` - Complete experiment with:
  - [x] `FINAL_REPORT.md` - Comprehensive analysis
  - [x] `SCORECARD_V2.json` - Enhanced scoring rubric
  - [x] `scripts/save_results.py` - Automated results collection
  - [x] `scripts/aggregate_results.py` - Results aggregation
  - [x] All 8 model instruction files (L1 and L3)

---

## What Needs to Be Completed

### 🔴 Priority 1: Core Functionality

- [ ] **CLI Scripts**
  - [ ] `scripts/new_plan.py` - Create new plan from template
  - [ ] `scripts/new_discussion.py` - Create new discussion
  - [ ] `scripts/new_experiment.py` - Bootstrap experiment structure
  - [ ] `scripts/verify_plan.py` - Run all verification commands

- [ ] **Templates**
  - [ ] `.plans/.templates/PLAN_TEMPLATE.json` - Plan JSON template
  - [ ] `.discussions/.templates/DISC_TEMPLATE.md` - Discussion template
  - [ ] `.adrs/.templates/ADR_TEMPLATE.json` - ADR JSON template
  - [ ] `.experiments/.templates/` - Experiment bootstrap template

### 🟡 Priority 2: Documentation

- [ ] **ADRs to Copy/Adapt from engineering-tools**
  - [ ] ADR-0001: AI Development Workflow Orchestration (was ADR-0041)
  - [ ] ADR-0002: AI-Assisted Development Patterns (was ADR-0033)
  - [ ] ADR-0003: 3-Tier Document Model (was ADR-0015)
  - [ ] ADR-0004: Plan Granularity Levels (NEW - from EXP-001)
  - [ ] ADR-0005: Contract Discipline (was ADR-0009)

- [ ] **Guides**
  - [ ] `docs/guides/GETTING_STARTED.md` - Step-by-step tutorial
  - [ ] `docs/guides/PLAN_AUTHORING.md` - How to write L1/L2/L3 plans
  - [ ] `docs/guides/EXPERIMENT_DESIGN.md` - How to run model experiments
  - [ ] `docs/guides/SESSION_MANAGEMENT.md` - Cross-session handoff

- [ ] **SPECs**
  - [ ] `docs/specs/SPEC-001_Plan-Schema.json` - Plan schema specification

### 🟢 Priority 3: Examples & Polish

- [ ] **Example Projects**
  - [ ] `examples/simple_crud_app/` - Simple REST API plan
  - [ ] `examples/api_refactor/` - Refactoring existing code plan
  - [ ] `examples/new_feature/` - Full workflow from discussion to code

- [ ] **Tests**
  - [ ] `tests/test_plan_schema.py` - Schema validation tests
  - [ ] `tests/test_cli.py` - CLI script tests

- [ ] **CI/CD**
  - [ ] `.github/workflows/test.yml` - Run tests on PR
  - [ ] `.github/workflows/lint.yml` - Ruff linting

### 🔵 Priority 4: Product Features (Future)

- [ ] **Web UI** (if building SaaS)
  - [ ] Plan editor with L1/L2/L3 toggle
  - [ ] Experiment dashboard
  - [ ] Model comparison charts

- [ ] **Integrations**
  - [ ] VS Code extension
  - [ ] Windsurf deep integration
  - [ ] GitHub Actions for plan verification

- [ ] **Advanced Features**
  - [ ] Plan version history
  - [ ] Team collaboration
  - [ ] Model cost tracking

---

## Key Decisions Made

| Decision | Rationale |
|----------|-----------|
| Pydantic-only dependency | Keep it minimal and portable |
| JSON for plans/ADRs | Machine-readable, AI-friendly |
| Markdown for discussions | Human-readable, flexible |
| L1/L2/L3 granularity | Evidence from EXP-001 supports tiered approach |
| Session-based continuity | AI assistants work in conversations |

---

## References

- **Source Project**: `engineering-tools` (private)
- **Key Experiment**: EXP-001 L1 vs L3 Granularity
- **Models Tested**: Opus, Sonnet, Gemini Pro, GPT-5.2 (L1) + Grok, Haiku, Flash, GPT-5.1 (L3)

---

## How to Contribute

1. Pick an item from the TODO list above
2. Create a branch: `feature/item-name`
3. Implement with tests
4. Submit PR

---

*Last Updated: December 30, 2025*
