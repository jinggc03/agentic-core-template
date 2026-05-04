"""Test LLM providers."""

import pytest

from app.providers.base import BaseLLMProvider
from app.providers.deepseek import DeepSeekProvider
from app.providers.factory import get_llm_provider
from app.providers.openrouter import OpenRouterProvider
from app.providers.openai import OpenAIProvider
from app.core.config import Settings


def test_openrouter_provider_init():
    """Test OpenRouter provider initialization."""
    provider = OpenRouterProvider(
        api_key="test-key",
        model="meta-llama/llama-3.1-70b-instruct",
    )
    assert provider.api_key == "test-key"
    assert provider.model == "meta-llama/llama-3.1-70b-instruct"
    assert provider.base_url == "https://openrouter.ai/api/v1"


def test_openai_provider_init():
    """Test OpenAI provider initialization."""
    provider = OpenAIProvider(
        api_key="test-key",
        model="gpt-4-turbo",
    )
    assert provider.api_key == "test-key"
    assert provider.model == "gpt-4-turbo"
    assert provider.base_url == "https://api.openai.com/v1"


def test_deepseek_provider_init():
    """Test DeepSeek provider initialization."""
    provider = DeepSeekProvider(
        api_key="test-key",
        model="deepseek-chat",
    )
    assert provider.api_key == "test-key"
    assert provider.model == "deepseek-chat"
    assert provider.base_url == "https://api.deepseek.com"


def test_provider_factory_selects_deepseek(monkeypatch):
    """Test provider factory can select DeepSeek."""
    monkeypatch.setattr(
        "app.core.config.settings",
        Settings(
            LLM_PROVIDER="deepseek",
            LLM_MODEL="deepseek-chat",
            DEEPSEEK_API_KEY="deepseek-key",
        ),
    )

    provider = get_llm_provider()

    assert isinstance(provider, DeepSeekProvider)
    assert provider.api_key == "deepseek-key"
    assert provider.model == "deepseek-chat"


def test_provider_factory_requires_deepseek_key(monkeypatch):
    """Test provider factory fails clearly without DeepSeek API key."""
    monkeypatch.setattr(
        "app.core.config.settings",
        Settings(
            LLM_PROVIDER="deepseek",
            LLM_MODEL="deepseek-chat",
            LLM_API_KEY="",
            DEEPSEEK_API_KEY="",
        ),
    )

    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY or LLM_API_KEY"):
        get_llm_provider()


def test_base_provider_interface():
    """Test BaseLLMProvider interface."""
    
    class TestProvider(BaseLLMProvider):
        async def generate(self, prompt: str, **kwargs) -> str:
            return "test response"
        
        async def generate_with_tools(self, prompt: str, tools: list, **kwargs) -> dict:
            return {"response": "test"}
    
    provider = TestProvider(api_key="test-key", model="test-model")
    assert provider.api_key == "test-key"
    assert provider.model == "test-model"
