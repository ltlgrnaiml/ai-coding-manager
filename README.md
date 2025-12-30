# AI Dev Orchestrator

> A framework for structured, AI-assisted code development with tiered plan granularity.

## What is This?

AI Dev Orchestrator helps you get **consistent, high-quality code** from AI coding assistants by providing:

1. **Plan Granularity System (L1/L2/L3)** - Match plan detail to model capability
2. **6-Tier Workflow** - Discussion → ADR → SPEC → Contract → Plan → Fragment
3. **Experiment Framework** - A/B test AI models, measure stochastic variation
4. **Session Continuity** - Handoff context between AI sessions

## Quick Start

```bash
# Clone the repo
git clone https://github.com/your-org/ai-dev-orchestrator.git
cd ai-dev-orchestrator

# Install dependencies
pip install -e .

# Create your first plan
python scripts/new_plan.py "My Feature"
```

## Plan Granularity Levels

Based on [EXP-001 research](/.experiments/EXP-001_L1-vs-L3/FINAL_REPORT.md), different AI models need different levels of detail:

| Level | Target Models | What to Include |
|-------|---------------|-----------------|
| **L1** | Premium (Opus, Sonnet, GPT-5.2) | Context prefixes only |
| **L2** | Mid-tier (Gemini Pro, GPT-5.1) | + Constraints + Pattern refs |
| **L3** | Budget (Haiku, Flash, Grok) | + Step-by-step code snippets |

### Key Finding

> **L3 plans reduce stochastic variation by 50%+**, enabling budget models to match premium model quality at 3-6x cost savings.

## Project Structure

```
ai-dev-orchestrator/
├── contracts/           # Pydantic schemas (SSOT)
│   ├── plan_schema.py   # L1/L2/L3 plan system
│   ├── adr_schema.py    # ADR structure
│   └── spec_schema.py   # SPEC structure
│
├── .adrs/               # Architecture Decision Records (WHY)
├── docs/specs/          # Technical Specifications (WHAT)
├── docs/guides/         # How-to Guides (HOW)
│
├── .discussions/        # Design conversations
├── .plans/              # Execution plans
├── .sessions/           # Session continuity logs
├── .experiments/        # A/B testing framework
│
├── scripts/             # Automation tools
└── examples/            # Example projects
```

## The 6-Tier Workflow

```
T0: Discussion   → Capture AI ↔ Human design conversation
T1: ADR          → Record WHY architectural decisions were made
T2: SPEC         → Define WHAT to build (behavioral requirements)
T3: Contract     → Define data shapes (Pydantic SSOT)
T4: Plan         → Milestones, tasks, acceptance criteria
T5: Fragment     → One verifiable unit of work
```

### Entry Points

Not all work requires the full workflow:

| Scenario | Start At | Skip |
|----------|----------|------|
| Architectural change | T0 (Discussion) | None |
| New feature | T2 (SPEC) | T0, T1 |
| Bug fix / Refactor | T4 (Plan) | T0-T3 |

## Context Prefixes (L1)

When writing L1 plans, use standardized prefixes:

```json
"context": [
  "ARCHITECTURE: Functional style, no classes",
  "FILE: Create gateway/services/my_service.py",
  "FUNCTION: def process_data(input: str) -> Output",
  "ENUM: Status values: pending, active, completed",
  "VERSION: Use __version__ = '2025.12.01'"
]
```

## Constraints (L2)

For mid-tier models, add explicit constraints:

```json
"constraints": [
  "DO NOT use class-based architecture",
  "MUST place tests in tests/unit/",
  "EXACTLY 5 enum values, no more"
],
"existing_patterns": [
  "Follow pattern in gateway/services/user_service.py"
]
```

## Running Experiments

Compare AI model performance:

```bash
# Create experiment branches
git worktree add ../exp-l1-opus experiment/l1-opus
git worktree add ../exp-l3-haiku experiment/l3-haiku

# Run experiments in each worktree with different models

# Collect results
python .experiments/EXP-001/scripts/save_results.py

# Aggregate and analyze
python .experiments/EXP-001/scripts/aggregate_results.py
```

## Documentation

- [Getting Started Guide](docs/guides/GETTING_STARTED.md)
- [Plan Authoring Guide](docs/guides/PLAN_AUTHORING.md)
- [Experiment Design Guide](docs/guides/EXPERIMENT_DESIGN.md)
- [AI Coding Guide](AI_CODING_GUIDE.md)

## Origin

This framework was extracted from a production engineering tools platform after conducting [EXP-001: L1 vs L3 Plan Granularity Experiment](/.experiments/EXP-001_L1-vs-L3/FINAL_REPORT.md) which tested 8 AI models across two granularity levels.

## License

MIT License - See [LICENSE](LICENSE) for details.

---

*Built with ❤️ for AI-assisted development*
