# DISC-0027: Automated Testing & Debugging Infrastructure

> **Status**: Draft  
> **Created**: 2026-01-03  
> **Author**: AI Assistant + USER  
> **Depends On**: DISC-0026, DISC-0022 (AIKH)  
> **Blocks**: Production deployment confidence  

---

## Summary

Design a comprehensive automated testing and debugging infrastructure that provides first-class observability, regression testing, and self-healing capabilities for AI-driven workflows. This supports the P2RE methodology and enables confident iteration on agentic systems.

---

## Context

### Problem

Current state lacks:

1. **No automated regression testing** for AI responses
2. **No golden/baseline output tracking** for behavior verification
3. **Limited debugging visibility** into multi-step agent flows
4. **No automatic error categorization** or root cause analysis
5. **No self-healing mechanisms** when providers fail
6. **Manual testing required** after each change

### Vision

A testing infrastructure that:

1. Automatically validates AI behavior against baselines
2. Provides rich debugging context for failures
3. Enables deterministic replay of conversations
4. Supports A/B testing between models
5. Auto-detects regressions and alerts
6. Integrates with P2RE traces for full observability

---

## Requirements

### Functional Requirements

- [ ] **FR-1**: Baseline/golden output capture and comparison
- [ ] **FR-2**: Deterministic conversation replay
- [ ] **FR-3**: Automatic regression detection
- [ ] **FR-4**: Error categorization and tagging
- [ ] **FR-5**: Multi-provider fallback testing
- [ ] **FR-6**: Performance benchmarking (latency, cost)
- [ ] **FR-7**: A/B model comparison framework
- [ ] **FR-8**: Integration test suite for all endpoints
- [ ] **FR-9**: UI component snapshot testing
- [ ] **FR-10**: Trace-based debugging (step-through agent flows)

### Non-Functional Requirements

- [ ] **NFR-1**: Tests run in < 5 minutes for CI
- [ ] **NFR-2**: Zero false positives (semantic comparison for AI outputs)
- [ ] **NFR-3**: Full trace visibility in Phoenix/P2RE
- [ ] **NFR-4**: Automatic cleanup of test artifacts
- [ ] **NFR-5**: Parallel test execution support

---

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Test Orchestrator                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Unit Tests  │  │ Integration │  │ AI Behavior Tests   │  │
│  │  (pytest)   │  │   Tests     │  │ (golden/baseline)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│  Mock Server  │  │  Test Fixtures  │  │  Baseline Store     │
│  (responses)  │  │  (conversations)│  │  (golden outputs)   │
└───────────────┘  └─────────────────┘  └─────────────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │   P2RE Trace Database   │
                │   (test run artifacts)  │
                └─────────────────────────┘
```

### Test Categories

#### 1. Unit Tests

Standard pytest for individual functions:

```python
# tests/unit/test_cost_calculation.py
def test_calculate_cost_claude_haiku():
    cost = _calculate_cost("claude-3-5-haiku-20241022", 1000, 500)
    assert cost == pytest.approx(0.00280, rel=0.01)

def test_calculate_cost_unknown_model_uses_fallback():
    cost = _calculate_cost("unknown-model", 1000, 1000)
    assert cost > 0  # Uses fallback pricing
```

#### 2. Integration Tests

API endpoint testing with real/mocked responses:

```python
# tests/integration/test_chat_api.py
@pytest.mark.integration
async def test_chat_stream_returns_valid_sse():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/chat/stream", json={
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "claude-3-5-haiku-20241022"
        })
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
```

#### 3. AI Behavior Tests (Golden/Baseline)

Semantic comparison of AI outputs:

```python
# tests/behavior/test_code_review.py
class TestCodeReviewBehavior:
    """Test that code review responses maintain quality."""
    
    @pytest.fixture
    def baseline_response(self):
        return load_baseline("code_review_python_function")
    
    def test_identifies_bugs(self, baseline_response):
        """AI should identify the same categories of bugs."""
        response = run_prompt("review this Python code: ...")
        
        # Semantic comparison, not exact match
        assert has_similar_issues(response, baseline_response)
        assert mentions_category(response, "error_handling")
        assert mentions_category(response, "type_hints")
    
    def test_response_length_reasonable(self):
        """Response should be within expected range."""
        response = run_prompt("review this code: print('hello')")
        assert 50 < len(response) < 2000
```

#### 4. Regression Tests

Automatic detection of behavior changes:

```python
# tests/regression/test_model_outputs.py
@pytest.mark.regression
class TestModelRegression:
    """Detect unexpected changes in model behavior."""
    
    def test_prompt_template_consistency(self):
        """Same prompt should produce semantically similar output."""
        current = run_prompt(STANDARD_PROMPT)
        baseline = load_baseline("standard_prompt_response")
        
        similarity = semantic_similarity(current, baseline)
        assert similarity > 0.8, f"Response diverged: {similarity}"
    
    def test_tool_calling_behavior(self):
        """Tool calls should match expected pattern."""
        response = run_with_tools(TOOL_PROMPT, tools=[search_tool])
        
        assert response.has_tool_call("search")
        assert response.tool_args["query"] contains_keywords(["python", "async"])
```

---

## Baseline/Golden Output System

### Schema

```sql
CREATE TABLE test_baselines (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT,                  -- 'code_review', 'chat', 'tool_use'
    
    -- Input
    prompt TEXT NOT NULL,
    system_prompt TEXT,
    model_id TEXT,
    
    -- Expected output characteristics
    expected_output TEXT,           -- Golden response (optional)
    expected_keywords TEXT,         -- JSON array of required keywords
    expected_categories TEXT,       -- JSON array of expected topics
    min_length INTEGER,
    max_length INTEGER,
    
    -- Semantic embedding for comparison
    embedding BLOB,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_by TEXT,               -- Who approved this baseline
    notes TEXT
);

CREATE TABLE test_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    baseline_id TEXT REFERENCES test_baselines(id),
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Actual output
    actual_output TEXT,
    actual_model TEXT,
    
    -- Comparison results
    similarity_score REAL,
    keywords_matched TEXT,          -- JSON array
    categories_matched TEXT,        -- JSON array
    length_in_range BOOLEAN,
    
    -- Status
    passed BOOLEAN,
    failure_reason TEXT,
    
    -- P2RE integration
    trace_id TEXT,
    latency_ms INTEGER,
    cost_usd REAL
);
```

### Workflow

```
1. CAPTURE: Run prompt → Store as baseline
   └─ pytest --capture-baseline test_code_review

2. APPROVE: Human reviews and approves baseline
   └─ UI: "Approve baseline: code_review_v1"

3. TEST: Run tests against baselines
   └─ pytest tests/behavior/

4. COMPARE: Semantic comparison + keyword matching
   └─ similarity > 0.8 AND keywords_present

5. ALERT: Notify on regression
   └─ Slack/email: "Baseline failed: code_review_v1"

6. UPDATE: Re-capture after intentional changes
   └─ pytest --update-baseline test_code_review
```

---

## Debugging Infrastructure

### Trace-Based Debugging

Leverage P2RE traces for debugging:

```python
# Debug a specific conversation
from backend.services.p2re import get_trace, replay_trace

# Get full trace with all steps
trace = get_trace("tr_abc123")
print(trace.messages)
print(trace.tool_calls)
print(trace.response_content)

# Replay with different model
result = replay_trace("tr_abc123", model="claude-sonnet-4")
compare(trace.response_content, result.response_content)
```

### Error Categorization

Automatic tagging of errors:

```python
class ErrorCategory(Enum):
    RATE_LIMIT = "rate_limit"
    AUTH_FAILURE = "auth_failure"
    CONTEXT_OVERFLOW = "context_overflow"
    INVALID_REQUEST = "invalid_request"
    TOOL_FAILURE = "tool_failure"
    TIMEOUT = "timeout"
    CONTENT_FILTER = "content_filter"
    UNKNOWN = "unknown"

def categorize_error(error: Exception, response: dict) -> ErrorCategory:
    """Auto-categorize errors for debugging."""
    if "rate limit" in str(error).lower():
        return ErrorCategory.RATE_LIMIT
    if response.get("status") == 401:
        return ErrorCategory.AUTH_FAILURE
    # ... more rules
```

### Debug Dashboard (Future UI)

```
┌─────────────────────────────────────────────────────────────┐
│  Test Run: 2026-01-03 10:30:00                              │
├─────────────────────────────────────────────────────────────┤
│  ✅ Unit Tests:        45/45 passed                         │
│  ✅ Integration Tests: 12/12 passed                         │
│  ⚠️  Behavior Tests:   8/10 passed (2 regressions)          │
│                                                              │
│  Failed:                                                     │
│  ├─ test_code_review_identifies_bugs                        │
│  │   Similarity: 0.72 (expected > 0.8)                      │
│  │   Missing: "error_handling" keyword                       │
│  │   [View Trace] [Compare Outputs] [Update Baseline]       │
│  │                                                          │
│  └─ test_tool_calling_behavior                              │
│      Tool call missing: expected "search", got none          │
│      [View Trace] [Replay] [Debug]                          │
└─────────────────────────────────────────────────────────────┘
```

---

## A/B Testing Framework

Compare models systematically:

```python
# tests/ab/test_model_comparison.py
@pytest.mark.ab_test
class TestModelComparison:
    """Compare model performance for routing decisions."""
    
    PROMPTS = [
        "Explain async/await in Python",
        "Review this code for bugs: ...",
        "Generate a unit test for: ...",
    ]
    
    MODELS = [
        "claude-3-5-haiku-20241022",
        "gemini-2.5-flash",
        "grok-4-1-fast-non-reasoning",
    ]
    
    def test_compare_quality(self):
        """Run same prompts through all models, compare quality."""
        results = []
        for prompt in self.PROMPTS:
            for model in self.MODELS:
                response = run_prompt(prompt, model=model)
                results.append({
                    "model": model,
                    "prompt": prompt,
                    "response": response,
                    "latency": response.latency_ms,
                    "cost": response.cost_usd,
                    "quality_score": evaluate_quality(response),
                })
        
        # Generate comparison report
        report = generate_ab_report(results)
        save_report(report, "model_comparison_2026-01-03")
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)

- [ ] Set up pytest structure with markers
- [ ] Create mock server for offline testing
- [ ] Implement baseline capture command
- [ ] Add test_baselines table to P2RE database

### Phase 2: Behavior Testing (Week 2)

- [ ] Semantic similarity comparison (embeddings)
- [ ] Keyword/category extraction
- [ ] Baseline approval workflow
- [ ] Regression detection alerts

### Phase 3: Debugging Tools (Week 3)

- [ ] Error categorization system
- [ ] Trace replay functionality
- [ ] Debug command (CLI)
- [ ] Test run history tracking

### Phase 4: CI/CD Integration (Week 4)

- [ ] GitHub Actions workflow
- [ ] Parallel test execution
- [ ] Coverage reporting
- [ ] Automatic PR checks

### Phase 5: UI Dashboard (Future)

- [ ] Test run visualization
- [ ] Baseline management UI
- [ ] A/B comparison reports
- [ ] Regression alerts in UI

---

## Open Questions

| ID | Question | Status |
|----|----------|--------|
| Q-1 | How to handle non-deterministic AI outputs in tests? | Open |
| Q-2 | Should we use LLM-as-judge for quality evaluation? | Open |
| Q-3 | How often to refresh baselines? | Open |
| Q-4 | Should tests use real API calls or always mock? | Open |
| Q-5 | How to handle multi-turn conversation testing? | Open |

---

## Related Documents

- DISC-0026: Unified Model Registry Schema
- DISC-0022: AI Knowledge Hub Architecture
- ADR-0004: Observability & Debugging
- P2RE trace system (existing)
