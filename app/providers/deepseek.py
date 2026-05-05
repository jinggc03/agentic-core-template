"""DeepSeek LLM provider."""

from typing import Any, Dict, Optional

import aiohttp

from app.providers.base import BaseLLMProvider


class DeepSeekProvider(BaseLLMProvider):
    """Official DeepSeek API provider implementation.

    DeepSeek exposes an OpenAI-compatible Chat Completions API at
    https://api.deepseek.com.
    """

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        """Initialize DeepSeek provider.

        Args:
            api_key: DeepSeek API key
            model: DeepSeek model identifier
        """
        super().__init__(api_key, model)
        self.base_url = "https://api.deepseek.com"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> str:
        """Generate response using DeepSeek."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
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
                raise Exception(f"DeepSeek API error: {resp.status}")

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
                "Content-Type": "application/json",
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
                raise Exception(f"DeepSeek API error: {resp.status}")
