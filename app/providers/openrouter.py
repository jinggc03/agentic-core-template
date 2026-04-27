"""OpenRouter LLM provider."""

from typing import Any, Dict, Optional
import aiohttp

from app.providers.base import BaseLLMProvider


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter LLM provider implementation."""

    def __init__(self, api_key: str, model: str = "meta-llama/llama-3.1-70b-instruct"):
        """Initialize OpenRouter provider.
        
        Args:
            api_key: OpenRouter API key
            model: Model identifier
        """
        super().__init__(api_key, model)
        self.base_url = "https://openrouter.ai/api/v1"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """Generate response using OpenRouter."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com",
                "X-Title": "personal-agent-runtime",
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"OpenRouter API error: {resp.status}")

    async def generate_with_tools(
        self,
        prompt: str,
        tools: list[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Generate response with tool support."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://github.com",
                "X-Title": "personal-agent-runtime",
            }
            payload = {
                "model": self.model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
            }
            async with session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise Exception(f"OpenRouter API error: {resp.status}")
