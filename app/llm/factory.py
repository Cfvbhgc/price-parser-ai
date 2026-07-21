"""Сборка LLM-провайдера из настроек.

Дефолты для известных провайдеров, чтобы в .env хватало одного ключа.
"""

from __future__ import annotations

from app.config import Settings
from app.llm.base import LLMProvider
from app.llm.openai_compatible import OpenAICompatibleProvider

PROVIDER_DEFAULTS = {
    "deepseek": {"base_url": "https://api.deepseek.com", "model": "deepseek-chat"},
    "openai": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
}


def create_llm_provider(settings: Settings) -> LLMProvider:
    defaults = PROVIDER_DEFAULTS.get(settings.llm_provider.lower(), {})
    base_url = settings.llm_base_url or defaults.get("base_url", "")
    model = settings.llm_model or defaults.get("model", "")

    if not base_url or not model:
        raise ValueError(
            f"Для провайдера «{settings.llm_provider}» не задан base_url/model. "
            "Укажите LLM_BASE_URL и LLM_MODEL в .env."
        )

    return OpenAICompatibleProvider(
        api_key=settings.llm_api_key,
        model=model,
        base_url=base_url,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
    )
