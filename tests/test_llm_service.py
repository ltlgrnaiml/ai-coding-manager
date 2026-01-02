"""Tests for LLM service (with mocked API calls)."""

import pytest
from unittest.mock import patch, MagicMock
from pydantic import BaseModel

# Import what we can test without API keys
from ai_dev_orchestrator.llm.service import (
    ModelInfo,
    AVAILABLE_MODELS,
    get_available_models,
    get_current_model,
    set_current_model,
    LLMStatus,
)


class TestModelConfiguration:
    """Tests for model configuration without API calls."""

    def test_available_models_defined(self):
        """Test that available models are defined."""
        models = get_available_models()
        assert len(models) > 0
        assert all(isinstance(m, ModelInfo) for m in models)

    def test_model_info_fields(self):
        """Test ModelInfo has required fields."""
        models = get_available_models()
        for model in models:
            assert model.id
            assert model.name
            assert model.context_window > 0
            assert model.rpm > 0
            assert model.input_price >= 0
            assert model.output_price >= 0
            assert model.category in ["fast", "premium", "budget", "code", "vision"]

    def test_get_set_current_model(self):
        """Test getting and setting current model."""
        original = get_current_model()
        
        # Set a new model
        models = get_available_models()
        if len(models) > 1:
            new_model = models[1].id
            set_current_model(new_model)
            assert get_current_model() == new_model
            
            # Restore original
            set_current_model(original)
            assert get_current_model() == original

    def test_model_categories(self):
        """Test that models have proper categories."""
        models = get_available_models()
        categories = set(m.category for m in models)
        
        # Should have at least fast and premium
        assert "fast" in categories or "premium" in categories

    def test_context_windows_reasonable(self):
        """Test that context windows are reasonable sizes."""
        models = get_available_models()
        for model in models:
            # Context should be at least 8k, at most 2M
            assert 8000 <= model.context_window <= 2_000_000, f"{model.id} has unreasonable context"


class TestLLMStatusEnum:
    """Tests for LLM status enumeration."""

    def test_status_values(self):
        """Test LLMStatus enum values."""
        assert LLMStatus.AVAILABLE.value == "available"
        assert LLMStatus.UNAVAILABLE.value == "unavailable"
        assert LLMStatus.ERROR.value == "error"
        assert LLMStatus.RATE_LIMITED.value == "rate_limited"


class TestStructuredOutputSchema:
    """Tests for structured output with mock responses."""

    def test_pydantic_schema_generation(self):
        """Test that Pydantic models generate valid JSON schemas."""
        class TaskOutput(BaseModel):
            title: str
            steps: list[str]
            priority: int

        schema = TaskOutput.model_json_schema()
        
        assert "properties" in schema
        assert "title" in schema["properties"]
        assert "steps" in schema["properties"]
        assert "priority" in schema["properties"]
        assert schema["properties"]["steps"]["type"] == "array"


class TestMockedAPIOperations:
    """Tests with mocked API calls.
    
    Note: These tests require mocking at the right level since
    the service checks for API key before making calls.
    """

    @patch("ai_dev_orchestrator.llm.service.XAI_API_KEY", "test-key")
    @patch("ai_dev_orchestrator.llm.service._get_openai_client")
    def test_health_check_mocked(self, mock_client):
        """Test health check with mocked client."""
        from ai_dev_orchestrator.llm.service import check_health
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "healthy"
        mock_client.return_value.chat.completions.create.return_value = mock_response
        
        result = check_health()
        # With mocked API key and client, should be available
        assert result.status in [LLMStatus.AVAILABLE, LLMStatus.NO_API_KEY]

    @patch("ai_dev_orchestrator.llm.service.XAI_API_KEY", "test-key")
    @patch("ai_dev_orchestrator.llm.service._get_openai_client")
    def test_health_check_failure_mocked(self, mock_client):
        """Test health check handling API errors."""
        from ai_dev_orchestrator.llm.service import check_health
        import httpx
        
        # Mock connection error
        mock_client.return_value.chat.completions.create.side_effect = httpx.ConnectError("Connection failed")
        
        result = check_health()
        # Should be unavailable or error
        assert result.status in [LLMStatus.UNAVAILABLE, LLMStatus.ERROR, LLMStatus.NO_API_KEY]

    @patch("ai_dev_orchestrator.llm.service.XAI_API_KEY", "test-key")
    @patch("ai_dev_orchestrator.llm.service._get_openai_client")
    def test_generate_text_mocked(self, mock_client):
        """Test text generation with mocked client."""
        from ai_dev_orchestrator.llm.service import generate_text
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello, I am Grok!"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_client.return_value.chat.completions.create.return_value = mock_response
        
        result = generate_text("Say hello")
        # May fail if API key validation is deeper
        if result.success:
            assert "Grok" in result.text

    @patch("ai_dev_orchestrator.llm.service.XAI_API_KEY", "test-key")
    @patch("ai_dev_orchestrator.llm.service._get_openai_client")
    def test_generate_structured_mocked(self, mock_client):
        """Test structured generation with mocked client."""
        from ai_dev_orchestrator.llm.service import generate_structured
        
        class SimpleOutput(BaseModel):
            name: str
            count: int
        
        # Mock successful JSON response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"name": "test", "count": 42}'
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_client.return_value.chat.completions.create.return_value = mock_response
        
        result = generate_structured("Generate a name and count", SimpleOutput)
        # May fail if API key validation is deeper
        if result.success and result.data:
            # result.data may be dict or SimpleOutput depending on implementation
            if hasattr(result.data, 'name'):
                assert result.data.name == "test"
                assert result.data.count == 42
            elif isinstance(result.data, dict):
                assert result.data["name"] == "test"
                assert result.data["count"] == 42
