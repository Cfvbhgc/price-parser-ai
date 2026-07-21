"""Эвристическое определение маппинга колонок (без LLM).

Работает по тем же ключевым словам, что и поиск заголовка: пробегаем по ячейкам
строки-заголовка и назначаем каждой колонке роль по её тексту. Это надёжный
запасной вариант, когда LLM недоступен (нет ключа) или не ответил.
"""

from __future__ import annotations

from app.keywords import match_column_role
from app.models import ColumnMapping


class MappingError(RuntimeError):
    """Не удалось сопоставить колонки (нет даже колонки с названием)."""


def detect_mapping_heuristic(header: list[str]) -> ColumnMapping:
    roles: dict[str, int] = {}
    for index, cell in enumerate(header):
        role = match_column_role(cell)
        # Первое совпадение для роли выигрывает — обычно нужная колонка левее.
        if role and role not in roles:
            roles[role] = index

    mapping = ColumnMapping(
        name=roles.get("name"),
        article=roles.get("article"),
        price=roles.get("price"),
        quantity=roles.get("quantity"),
    )
    if not mapping.is_valid():
        raise MappingError(
            "Не нашёл колонку с названием товара по заголовкам "
            f"{header}. Ожидаю что-то вроде «Наименование» или «Название»."
        )
    return mapping
