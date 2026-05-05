"""LLM provider factory and selector."""

from app.providers.base import BaseLLMProvider
from app.providers.deepseek import DeepSeekProvider
from app.providers.openrouter import OpenRouterProvider
from app.providers.openai import OpenAIProvider


def get_llm_provider() -> BaseLLMProvider:
    """Get LLM provider based on environment configuration.
    
    Returns:
        Configured LLM provider instance
        
    Raises:
        ValueError: If provider or API key is not configured
    """
    from app.core.config import settings

    provider = settings.LLM_PROVIDER.lower()
    model = settings.LLM_MODEL
    api_key = settings.LLM_API_KEY

    if provider == "openrouter":
        if not settings.OPENROUTER_API_KEY and not api_key:
            raise ValueError("OPENROUTER_API_KEY or LLM_API_KEY must be configured")
        return OpenRouterProvider(
            api_key=api_key or settings.OPENROUTER_API_KEY,
            model=model,
        )
    elif provider == "openai":
        if not settings.OPENAI_API_KEY and not api_key:
            raise ValueError("OPENAI_API_KEY or LLM_API_KEY must be configured")
        return OpenAIProvider(
            api_key=api_key or settings.OPENAI_API_KEY,
            model=model,
        )
    elif provider == "deepseek":
        if not settings.DEEPSEEK_API_KEY and not api_key:
            raise ValueError("DEEPSEEK_API_KEY or LLM_API_KEY must be configured")
        return DeepSeekProvider(
            api_key=api_key or settings.DEEPSEEK_API_KEY,
            model=model,
        )
    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Supported: openrouter, openai, deepseek"
        )
