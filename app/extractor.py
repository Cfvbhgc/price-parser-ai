"""Извлечение товаров из сетки по готовому маппингу колонок.

Весь файл разбирается здесь обычным кодом (LLM больше не нужен): для каждой
строки под заголовком берём ячейки по номерам из маппинга, парсим цену и
отсеиваем строки-разделители/мусор.
"""

from __future__ import annotations

import re

from app.models import ColumnMapping, Product
from app.reader import Grid


def _cell(row: list[str], index: int | None) -> str:
    if index is None or index >= len(row):
        return ""
    return row[index].strip()


def parse_price(raw: str) -> float | None:
    """Превратить строку цены в число.

    Понимает форматы вида «1 250,00», «1250.5», «1 500 руб.», «12 990 ₽».
    Пробелы (в т.ч. неразрывные) — разделители тысяч; запятая — десятичный знак.
    """
    if not raw:
        return None
    text = raw.replace("\xa0", " ").strip()
    # Убираем всё, кроме цифр, запятой, точки и минуса.
    text = re.sub(r"[^\d,.\-]", "", text)
    if not text:
        return None
    # Если есть и запятая, и точка — запятая считается десятичным разделителем
    # (европейский формат «1.250,00»), точки-разделители тысяч удаляем.
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", ".")
    try:
        return round(float(text), 2)
    except ValueError:
        return None


def extract_products(
    grid: Grid,
    header_index: int,
    mapping: ColumnMapping,
) -> list[Product]:
    products: list[Product] = []

    for row in grid[header_index + 1 :]:
        name = _cell(row, mapping.name)
        if not name:
            continue  # строки без названия пропускаем (пустые/технические)

        article = _cell(row, mapping.article)
        price = parse_price(_cell(row, mapping.price))

        # Строка-разделитель (например «=== ЭЛЕКТРИКА ===»): есть текст, но нет
        # ни цены, ни артикула — это не товар.
        if price is None and not article:
            continue

        products.append(Product(name=name, article=article, price=price))

    return products
