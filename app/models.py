"""Модели данных проекта.

Всего две сущности:
  - ColumnMapping — «где какая колонка» в конкретном прайсе (результат определения
    структуры). Индексы колонок 0-based; None означает «такой колонки нет».
  - Product — одна распарсенная позиция товара.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ColumnMapping:
    """Соответствие «смысл колонки → её номер» в разобранной таблице."""

    name: Optional[int]       # колонка с названием товара (обязательная)
    article: Optional[int]    # артикул / код
    price: Optional[int]      # цена
    quantity: Optional[int]   # количество / остаток

    def is_valid(self) -> bool:
        # Без названия товара прайс бесполезен — это минимальное требование.
        return self.name is not None


@dataclass
class Product:
    """Одна позиция итогового отчёта."""

    name: str
    article: str
    price: Optional[float]
    category: str = ""
