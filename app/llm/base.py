"""Абстракция LLM-провайдера.

Провайдер умеет одно: получить список сообщений чата и вернуть текст ответа.
Так конкретную реализацию (DeepSeek, OpenAI, локальный сервер) можно менять,
не трогая остальной код.
"""

from __future__ import annotations

from typing import Protocol, TypedDict


class ChatMessage(TypedDict):
    role: str      # "system" | "user" | "assistant"
    content: str


class LLMError(RuntimeError):
    """Любая ошибка обращения к модели (сеть, ключ, невалидный ответ)."""


class LLMProvider(Protocol):
    def chat(self, messages: list[ChatMessage]) -> str:
        ...
