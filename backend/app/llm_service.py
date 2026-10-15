"""
Provider-agnostic LLM service.
Supports Anthropic Claude, OpenAI, Google Gemini, and Groq.
"""

from abc import ABC, abstractmethod
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract LLM provider interface."""

    @abstractmethod
    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        """Generate a response from the LLM."""
        ...

    @abstractmethod
    async def generate_json(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        """Generate a JSON response from the LLM."""
        ...


class GroqProvider(LLMProvider):
    """Groq Cloud provider — ultra-fast inference via OpenAI-compatible API."""

    def __init__(self, api_key: str):
        from groq import AsyncGroq
        self.client = AsyncGroq(api_key=api_key)
        self.model = "openai/gpt-oss-120b"

    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system or "You are a biomedical knowledge assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Error with {self.model}, falling back to openai/gpt-oss-20b: {e}")
            response = await self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system or "You are a biomedical knowledge assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content

    async def generate_json(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        sys_prompt = (system or "You are a biomedical knowledge assistant.") + \
            "\n\nYou must respond with valid JSON only. No markdown, no code fences, just raw JSON."
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            text = response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Error in generate_json with {self.model}, falling back to openai/gpt-oss-20b: {e}")
            response = await self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            text = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
        return text.strip()


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: str):
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"

    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system or "You are a biomedical knowledge assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    async def generate_json(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        sys_prompt = (system or "You are a biomedical knowledge assistant.") + \
            "\n\nYou must respond with valid JSON only. No markdown, no code fences, just raw JSON."
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=sys_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
        return text.strip()


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: str):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4o"

    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system or "You are a biomedical knowledge assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    async def generate_json(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": (system or "You are a biomedical knowledge assistant.") + " Respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content


class GeminiProvider(LLMProvider):
    """Google Gemini provider."""

    def __init__(self, api_key: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-pro")

    async def generate(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = await self.model.generate_content_async(full_prompt)
        return response.text

    async def generate_json(self, prompt: str, system: str = "", max_tokens: int = 4096) -> str:
        full_prompt = f"{system}\n\nRespond with valid JSON only. No markdown.\n\n{prompt}" if system else prompt
        response = await self.model.generate_content_async(full_prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
        return text.strip()


def get_llm_provider() -> LLMProvider:
    """Factory function to get the configured LLM provider."""
    settings = get_settings()

    if settings.llm_provider == "groq":
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")
        return GroqProvider(settings.groq_api_key)
    elif settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
        return AnthropicProvider(settings.anthropic_api_key)
    elif settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        return OpenAIProvider(settings.openai_api_key)
    elif settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")
        return GeminiProvider(settings.gemini_api_key)
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
