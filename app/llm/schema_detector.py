"""Определение структуры прайса через LLM.

Идея экономии токенов: мы НЕ отправляем в модель весь файл. Модели достаточно
образца — строки заголовка и нескольких строк данных, — чтобы понять, где какая
колонка. Модель возвращает компактный JSON-маппинг (номера колонок), а весь файл
дальше разбирается обычным кодом по этому маппингу.

Так LLM вызывается ОДИН раз на файл, а не на каждую строку.
"""

from __future__ import annotations

import json
import re

from app.llm.base import ChatMessage, LLMError, LLMProvider
from app.models import ColumnMapping

SYSTEM_PROMPT = (
    "Ты — помощник по разбору прайс-листов. Тебе дают заголовок таблицы и "
    "несколько строк данных. Определи, в каких колонках находятся: название "
    "товара, артикул, цена и количество. Отвечай СТРОГО одним JSON-объектом без "
    "пояснений и без markdown, вида:\n"
    '{"name": <int|null>, "article": <int|null>, "price": <int|null>, "quantity": <int|null>}\n'
    "Значения — номера колонок, начиная с 0. Если колонки нет — null."
)


def _build_user_prompt(header: list[str], sample_rows: list[list[str]]) -> str:
    header_desc = "\n".join(f"  {i}: {cell!r}" for i, cell in enumerate(header))
    rows_desc = "\n".join(
        "  | ".join(cell for cell in row) for row in sample_rows
    )
    return (
        "ЗАГОЛОВОК (номер колонки: текст):\n"
        f"{header_desc}\n\n"
        "ПРИМЕРЫ СТРОК ДАННЫХ:\n"
        f"{rows_desc}\n\n"
        "Верни JSON-маппинг колонок."
    )


def _extract_json(text: str) -> dict:
    """Достать JSON из ответа модели, даже если он обёрнут в ```json ... ```."""
    fenced = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not fenced:
        raise LLMError(f"В ответе модели нет JSON: {text[:200]}")
    return json.loads(fenced.group(0))


def _coerce_index(value: object, num_columns: int) -> int | None:
    if value is None:
        return None
    try:
        index = int(value)
    except (TypeError, ValueError):
        return None
    return index if 0 <= index < num_columns else None


def detect_mapping_via_llm(
    llm: LLMProvider,
    header: list[str],
    sample_rows: list[list[str]],
) -> ColumnMapping:
    """Спросить у модели, где какая колонка. Бросает LLMError при проблемах."""
    messages: list[ChatMessage] = [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        ChatMessage(role="user", content=_build_user_prompt(header, sample_rows)),
    ]
    answer = llm.chat(messages)
    data = _extract_json(answer)

    num_columns = len(header)
    mapping = ColumnMapping(
        name=_coerce_index(data.get("name"), num_columns),
        article=_coerce_index(data.get("article"), num_columns),
        price=_coerce_index(data.get("price"), num_columns),
        quantity=_coerce_index(data.get("quantity"), num_columns),
    )
    if not mapping.is_valid():
        raise LLMError("Модель не смогла определить колонку с названием товара.")
    return mapping
