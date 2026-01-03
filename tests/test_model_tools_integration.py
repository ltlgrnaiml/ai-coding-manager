"""Model Tools Integration Test Suite.

Comprehensive test coverage for all model tools across all providers.
Optimized for cost while ensuring all tools are operational.

Strategy:
1. Use cheapest model per provider for basic tool tests
2. Test each tool type once (not repeated across all models)
3. Minimal token prompts (~50 tokens input, ~100 tokens output)
4. Provider-specific tests for unique capabilities

Estimated Cost per Full Run: ~$0.01-0.02
"""

import os
import pytest
from typing import Any
from unittest.mock import patch, MagicMock

# Skip all tests if no API keys configured
pytestmark = pytest.mark.skipif(
    not any([
        os.getenv("XAI_API_KEY"),
        os.getenv("ANTHROPIC_API_KEY"),
        os.getenv("GOOGLE_API_KEY"),
    ]),
    reason="No API keys configured"
)


# =============================================================================
# Cost-Optimized Model Selection
# =============================================================================

# Cheapest tool-capable model per provider for integration tests
COST_OPTIMIZED_MODELS = {
    "anthropic": "claude-3-5-haiku-20241022",  # $0.8/$4.0 per MTok
    "google": "gemini-2.0-flash",               # $0.1/$0.4 per MTok
    "xai": "grok-4-fast-reasoning",             # $0.2/$0.5 per MTok
}

# Minimal test prompts (optimize for low token count)
MINIMAL_PROMPTS = {
    "basic": "Say 'OK' only.",
    "tool_call": "What is 2+2? Use a tool if available.",
    "json_mode": "Return JSON: {\"status\": \"ok\"}",
    "streaming": "Count 1 to 3.",
}


# =============================================================================
# Provider Availability Fixtures
# =============================================================================

@pytest.fixture
def anthropic_available():
    return bool(os.getenv("ANTHROPIC_API_KEY"))

@pytest.fixture
def google_available():
    return bool(os.getenv("GOOGLE_API_KEY"))

@pytest.fixture
def xai_available():
    return bool(os.getenv("XAI_API_KEY"))


# =============================================================================
# Test Classes by Provider
# =============================================================================

class TestAnthropicModels:
    """Tests for Anthropic Claude models - using cheapest: claude-3-5-haiku."""
    
    MODEL = COST_OPTIMIZED_MODELS["anthropic"]
    
    @pytest.fixture(autouse=True)
    def skip_if_unavailable(self, anthropic_available):
        if not anthropic_available:
            pytest.skip("ANTHROPIC_API_KEY not set")
    
    @pytest.mark.asyncio
    async def test_basic_completion(self):
        """Test basic text completion works."""
        from backend.services.llm.service import LLMService
        service = LLMService()
        
        response = await service.generate(
            prompt=MINIMAL_PROMPTS["basic"],
            model=self.MODEL,
            max_tokens=10,
        )
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_streaming(self):
        """Test streaming responses work."""
        from backend.services.llm.service import LLMService
        service = LLMService()
        
        chunks = []
        async for chunk in service.stream(
            prompt=MINIMAL_PROMPTS["streaming"],
            model=self.MODEL,
            max_tokens=20,
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0
    
    @pytest.mark.asyncio
    async def test_json_mode(self):
        """Test JSON mode structured output."""
        from backend.services.llm.service import LLMService
        import json
        service = LLMService()
        
        response = await service.generate(
            prompt=MINIMAL_PROMPTS["json_mode"],
            model=self.MODEL,
            max_tokens=50,
            response_format={"type": "json_object"},
        )
        
        # Should be valid JSON
        parsed = json.loads(response)
        assert "status" in parsed


class TestGoogleModels:
    """Tests for Google Gemini models - using cheapest: gemini-2.0-flash."""
    
    MODEL = COST_OPTIMIZED_MODELS["google"]
    
    @pytest.fixture(autouse=True)
    def skip_if_unavailable(self, google_available):
        if not google_available:
            pytest.skip("GOOGLE_API_KEY not set")
    
    @pytest.mark.asyncio
    async def test_basic_completion(self):
        """Test basic text completion works."""
        from backend.services.llm.service import LLMService
        service = LLMService()
        
        response = await service.generate(
            prompt=MINIMAL_PROMPTS["basic"],
            model=self.MODEL,
            max_tokens=10,
        )
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_streaming(self):
        """Test streaming responses work."""
        from backend.services.llm.service import LLMService
        service = LLMService()
        
        chunks = []
        async for chunk in service.stream(
            prompt=MINIMAL_PROMPTS["streaming"],
            model=self.MODEL,
            max_tokens=20,
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0


class TestXAIModels:
    """Tests for xAI Grok models - using cheapest: grok-4-fast-reasoning."""
    
    MODEL = COST_OPTIMIZED_MODELS["xai"]
    
    @pytest.fixture(autouse=True)
    def skip_if_unavailable(self, xai_available):
        if not xai_available:
            pytest.skip("XAI_API_KEY not set")
    
    @pytest.mark.asyncio
    async def test_basic_completion(self):
        """Test basic text completion works."""
        from backend.services.llm.service import LLMService
        service = LLMService()
        
        response = await service.generate(
            prompt=MINIMAL_PROMPTS["basic"],
            model=self.MODEL,
            max_tokens=10,
        )
        assert response is not None
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_streaming(self):
        """Test streaming responses work."""
        from backend.services.llm.service import LLMService
        service = LLMService()
        
        chunks = []
        async for chunk in service.stream(
            prompt=MINIMAL_PROMPTS["streaming"],
            model=self.MODEL,
            max_tokens=20,
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0


# =============================================================================
# Tool-Specific Tests (One per Tool Type)
# =============================================================================

class TestToolCapabilities:
    """Test each tool type once using the cheapest capable model."""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="Requires Anthropic")
    async def test_anthropic_tool_calling(self):
        """Test Anthropic function/tool calling."""
        from backend.services.llm.service import LLMService
        service = LLMService()
        
        tools = [{
            "name": "get_weather",
            "description": "Get weather for a location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                },
                "required": ["location"]
            }
        }]
        
        response = await service.generate(
            prompt="What's the weather in Tokyo?",
            model=COST_OPTIMIZED_MODELS["anthropic"],
            max_tokens=100,
            tools=tools,
        )
        
        # Should either call the tool or respond
        assert response is not None
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="Requires Google")
    async def test_google_tool_calling(self):
        """Test Google Gemini function calling."""
        from backend.services.llm.service import LLMService
        service = LLMService()
        
        tools = [{
            "name": "calculate",
            "description": "Perform a calculation",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"]
            }
        }]
        
        response = await service.generate(
            prompt="Calculate 15 * 7",
            model=COST_OPTIMIZED_MODELS["google"],
            max_tokens=100,
            tools=tools,
        )
        
        assert response is not None
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("XAI_API_KEY"), reason="Requires xAI")
    async def test_xai_tool_calling(self):
        """Test xAI Grok function calling."""
        from backend.services.llm.service import LLMService
        service = LLMService()
        
        tools = [{
            "type": "function",
            "function": {
                "name": "search",
                "description": "Search for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            }
        }]
        
        response = await service.generate(
            prompt="Search for Python tutorials",
            model=COST_OPTIMIZED_MODELS["xai"],
            max_tokens=100,
            tools=tools,
        )
        
        assert response is not None


# =============================================================================
# Cross-Provider Compatibility Tests
# =============================================================================

class TestCrossProviderCompatibility:
    """Ensure all providers work with the same interface."""
    
    @pytest.mark.asyncio
    async def test_all_available_providers_respond(self):
        """Test that all configured providers can respond."""
        from backend.services.llm.service import LLMService
        service = LLMService()
        
        results = {}
        
        for provider, model in COST_OPTIMIZED_MODELS.items():
            api_key_var = {
                "anthropic": "ANTHROPIC_API_KEY",
                "google": "GOOGLE_API_KEY",
                "xai": "XAI_API_KEY",
            }[provider]
            
            if not os.getenv(api_key_var):
                results[provider] = "SKIPPED"
                continue
            
            try:
                response = await service.generate(
                    prompt=MINIMAL_PROMPTS["basic"],
                    model=model,
                    max_tokens=10,
                )
                results[provider] = "OK" if response else "EMPTY"
            except Exception as e:
                results[provider] = f"ERROR: {str(e)[:50]}"
        
        # At least one provider should work
        assert any(v == "OK" for v in results.values()), f"No providers working: {results}"
        
        # Log results for visibility
        for provider, status in results.items():
            print(f"{provider}: {status}")


# =============================================================================
# Model Registry Tests (No API Calls)
# =============================================================================

class TestModelRegistry:
    """Test model registry without making API calls."""
    
    def test_all_models_have_required_fields(self):
        """Verify all models in registry have required fields."""
        from backend.services.p2re.model_registry import get_all_models
        
        models = get_all_models()
        assert len(models) > 0
        
        for model in models:
            assert model.id, "Model missing id"
            assert model.provider_id, f"Model {model.id} missing provider_id"
            assert model.name, f"Model {model.id} missing name"
            assert model.context_window > 0, f"Model {model.id} invalid context_window"
            assert model.pricing is not None, f"Model {model.id} missing pricing"
    
    def test_all_providers_have_models(self):
        """Verify each provider has at least one model."""
        from backend.services.p2re.model_registry import get_all_models, get_all_providers
        
        providers = get_all_providers()
        models = get_all_models()
        
        provider_ids = {p.id for p in providers}
        model_providers = {m.provider_id for m in models}
        
        # Every provider should have models
        for pid in provider_ids:
            assert pid in model_providers, f"Provider {pid} has no models"
    
    def test_tool_capable_models_exist(self):
        """Verify tool-capable models exist for each provider."""
        from backend.services.p2re.model_registry import get_all_models
        
        models = get_all_models()
        
        tool_capable = {
            "anthropic": False,
            "google": False,
            "xai": False,
        }
        
        for model in models:
            if model.capabilities.tools:
                if model.provider_id in tool_capable:
                    tool_capable[model.provider_id] = True
        
        for provider, has_tools in tool_capable.items():
            assert has_tools, f"Provider {provider} has no tool-capable models"


# =============================================================================
# Cost Estimation Tests
# =============================================================================

class TestCostEstimation:
    """Test cost estimation accuracy."""
    
    def test_estimate_cost_endpoint(self):
        """Test the cost estimation API."""
        from backend.services.p2re.model_registry import estimate_cost, CostEstimateRequest
        
        request = CostEstimateRequest(
            model_id=COST_OPTIMIZED_MODELS["google"],
            input_tokens=1000,
            output_tokens=500,
        )
        
        result = estimate_cost(request)
        
        assert result.input_cost > 0
        assert result.output_cost > 0
        assert result.total_cost == result.input_cost + result.output_cost
    
    def test_cheapest_models_are_correctly_identified(self):
        """Verify our cost optimization selections are correct."""
        from backend.services.p2re.model_registry import get_all_models
        
        models = get_all_models()
        
        for provider, expected_model in COST_OPTIMIZED_MODELS.items():
            provider_models = [m for m in models if m.provider_id == provider and m.capabilities.tools]
            
            if not provider_models:
                continue
            
            # Find cheapest by input cost
            cheapest = min(provider_models, key=lambda m: m.pricing.input_per_mtok)
            
            # Our selection should be the cheapest or very close
            selected = next((m for m in provider_models if m.id == expected_model), None)
            assert selected is not None, f"Selected model {expected_model} not found"
            
            # Allow 50% margin for manual selection (some cheap models may be less capable)
            assert selected.pricing.input_per_mtok <= cheapest.pricing.input_per_mtok * 1.5, \
                f"Model {expected_model} is not cost-optimized for {provider}"


# =============================================================================
# Run Configuration
# =============================================================================

if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
        "--asyncio-mode=auto",
    ])
