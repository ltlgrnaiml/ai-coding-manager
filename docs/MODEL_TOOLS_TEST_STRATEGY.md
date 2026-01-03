# Model Tools Test Strategy

> Comprehensive test coverage for all LLM model tools, optimized for minimal cost.

## Overview

| Metric | Value |
|--------|-------|
| Total Models | 22 |
| Total Tools | 15 |
| Providers | 3 (Anthropic, Google, xAI) |
| Est. Cost/Run | ~$0.01-0.02 |

## Cost Optimization Strategy

### 1. Use Cheapest Model Per Provider

Instead of testing every model, we test each provider's **cheapest tool-capable model**:

| Provider | Model | Input $/MTok | Output $/MTok |
|----------|-------|--------------|---------------|
| Google | `gemini-2.0-flash` | $0.10 | $0.40 |
| xAI | `grok-4-fast-reasoning` | $0.20 | $0.50 |
| Anthropic | `claude-3-5-haiku-20241022` | $0.80 | $4.00 |

### 2. Minimal Token Prompts

All test prompts are optimized for minimal tokens:

```python
MINIMAL_PROMPTS = {
    "basic": "Say 'OK' only.",           # ~5 tokens
    "tool_call": "What is 2+2?",          # ~6 tokens
    "json_mode": "Return JSON: {...}",    # ~10 tokens
    "streaming": "Count 1 to 3.",         # ~5 tokens
}
```

### 3. Test Each Tool Type Once

Instead of testing every tool with every model, we test each tool type once with the cheapest capable model.

## Test Matrix

### Per-Provider Tests (Required)

| Test | Anthropic | Google | xAI |
|------|-----------|--------|-----|
| Basic Completion | ✓ | ✓ | ✓ |
| Streaming | ✓ | ✓ | ✓ |
| JSON Mode | ✓ | - | - |
| Tool Calling | ✓ | ✓ | ✓ |

### Tool-Specific Tests (One Each)

| Tool | Provider | Model | Test |
|------|----------|-------|------|
| Function Calling | Anthropic | claude-3-5-haiku | Define + invoke tool |
| Function Calling | Google | gemini-2.0-flash | Define + invoke tool |
| Function Calling | xAI | grok-4-fast | Define + invoke tool |

### Registry Tests (No API Calls)

These tests verify data integrity without making API calls:

- All models have required fields
- All providers have models
- Tool-capable models exist for each provider
- Cost estimation is accurate

## Running the Tests

### Full Suite (All Providers)

```bash
# All integration tests
pytest tests/test_model_tools_integration.py -v

# Quick smoke test (stop on first failure)
pytest tests/test_model_tools_integration.py -v -x
```

### Single Provider

```bash
# Anthropic only
pytest tests/test_model_tools_integration.py::TestAnthropicModels -v

# Google only
pytest tests/test_model_tools_integration.py::TestGoogleModels -v

# xAI only
pytest tests/test_model_tools_integration.py::TestXAIModels -v
```

### Registry Tests Only (Free)

```bash
# No API calls - tests registry data only
pytest tests/test_model_tools_integration.py::TestModelRegistry -v
pytest tests/test_model_tools_integration.py::TestCostEstimation -v
```

## Cost Breakdown

### Estimated Tokens Per Test

| Test Type | Input Tokens | Output Tokens |
|-----------|--------------|---------------|
| Basic Completion | ~10 | ~10 |
| Streaming | ~10 | ~20 |
| JSON Mode | ~15 | ~20 |
| Tool Calling | ~50 | ~100 |

### Estimated Cost Per Full Run

```
Anthropic (claude-3-5-haiku):
  4 tests × ~100 tokens = 400 tokens
  Cost: 400 × $0.8/1M = $0.00032

Google (gemini-2.0-flash):
  3 tests × ~100 tokens = 300 tokens
  Cost: 300 × $0.1/1M = $0.00003

xAI (grok-4-fast):
  3 tests × ~100 tokens = 300 tokens
  Cost: 300 × $0.2/1M = $0.00006

TOTAL: ~$0.01 per full run
```

## Adding New Tests

### Adding a New Model Test

```python
class TestNewModel:
    MODEL = "new-model-id"
    
    @pytest.mark.asyncio
    async def test_basic_completion(self):
        service = LLMService()
        response = await service.generate(
            prompt="Say OK",
            model=self.MODEL,
            max_tokens=10,
        )
        assert response
```

### Adding a New Tool Test

```python
@pytest.mark.asyncio
async def test_new_tool(self):
    tools = [{
        "name": "new_tool",
        "description": "...",
        "parameters": {...}
    }]
    
    response = await service.generate(
        prompt="Use the new tool",
        model=COST_OPTIMIZED_MODELS["provider"],
        tools=tools,
    )
    assert response
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run Model Integration Tests
  env:
    XAI_API_KEY: ${{ secrets.XAI_API_KEY }}
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
  run: |
    pytest tests/test_model_tools_integration.py -v --tb=short
```

### Cost Limits

Consider adding a daily/weekly budget check before running integration tests in CI:

```python
@pytest.fixture(scope="session", autouse=True)
def check_test_budget():
    # Could integrate with billing API to check remaining budget
    pass
```

## Troubleshooting

### Test Skipped

If tests are skipped, check that the relevant API key is set:

```bash
echo $XAI_API_KEY
echo $ANTHROPIC_API_KEY  
echo $GOOGLE_API_KEY
```

### Rate Limits

If hitting rate limits, add delays between tests:

```python
@pytest.fixture(autouse=True)
async def rate_limit_delay():
    yield
    await asyncio.sleep(1)  # 1 second between tests
```

---

*Last Updated: 2026-01-03 | Per DISC-029 Cross-Platform Workflow*
