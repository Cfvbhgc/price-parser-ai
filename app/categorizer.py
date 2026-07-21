"""Категоризация товаров по ключевым словам.

Список категорий настраивается в categories.json: у каждой категории — набор
ключевых слов. Товар относим к первой категории, чьё ключевое слово встречается
в названии (в нижнем регистре, по вхождению — так ловятся формы: «болт»,
«болты», «болтов»). Если ничего не подошло — категория по умолчанию.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.models import Product


@dataclass
class Category:
    name: str
    keywords: list[str]


class Categorizer:
    def __init__(self, categories: list[Category], default_category: str = "Прочее") -> None:
        self._categories = categories
        self._default = default_category
        # Плоский список (ключевое слово → категория), отсортированный по длине
        # слова УБЫВАНИЮ. Так более длинное (специфичное) слово имеет приоритет:
        # «шуруповёрт» (инструмент) сработает раньше, чем «шуруп» (крепёж),
        # хотя одно является подстрокой другого.
        self._keywords: list[tuple[str, str]] = sorted(
            ((kw, cat.name) for cat in categories for kw in cat.keywords),
            key=lambda pair: len(pair[0]),
            reverse=True,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> "Categorizer":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        categories = [
            Category(name=item["name"], keywords=[k.lower() for k in item["keywords"]])
            for item in data.get("categories", [])
        ]
        return cls(categories, data.get("default_category", "Прочее"))

    def categorize_one(self, name: str) -> str:
        text = name.lower()
        for keyword, category_name in self._keywords:
            if keyword in text:
                return category_name
        return self._default

    def categorize(self, products: list[Product]) -> None:
        """Проставить категорию каждому товару (изменяет объекты на месте)."""
        for product in products:
            product.category = self.categorize_one(product.name)
