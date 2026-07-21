"""Определение структуры прайса: где заголовок и где какая колонка.

Собирает вместе поиск заголовка, LLM-детекцию и эвристику-фолбэк, и возвращает
готовый результат для дальнейшего разбора файла.

Стратегия определения маппинга:
  1. если разрешён LLM и есть ключ — спрашиваем модель (образец, не весь файл);
  2. если LLM недоступен или упал — откатываемся на эвристику по ключевым словам.
Пользователю всегда сообщаем, какой способ сработал.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.column_mapper import detect_mapping_heuristic
from app.config import Settings, settings as default_settings
from app.header_detector import find_header_row
from app.llm.factory import create_llm_provider
from app.llm.schema_detector import detect_mapping_via_llm
from app.models import ColumnMapping
from app.reader import Grid

logger = logging.getLogger(__name__)


@dataclass
class Structure:
    header_index: int
    mapping: ColumnMapping
    method: str  # как определили маппинг: "llm" или "эвристика"


def detect_structure(
    grid: Grid,
    use_llm: bool,
    settings: Settings = default_settings,
) -> Structure:
    # 1. Находим строку-заголовок и отсекаем мусор сверху.
    header_index = find_header_row(grid, scan_limit=settings.header_scan_limit)
    header = grid[header_index]

    # 2. Образец для LLM: заголовок + несколько строк данных под ним.
    sample_rows = grid[header_index + 1 : header_index + 1 + settings.sample_rows]

    # 3. Определяем маппинг.
    if use_llm and settings.has_llm_key:
        try:
            llm = create_llm_provider(settings)
            mapping = detect_mapping_via_llm(llm, header, sample_rows)
            return Structure(header_index, mapping, method="llm")
        except Exception as exc:  # noqa: BLE001 — любой сбой LLM → откат на эвристику
            logger.warning("LLM не определил структуру (%s). Использую эвристику.", exc)

    mapping = detect_mapping_heuristic(header)
    return Structure(header_index, mapping, method="эвристика")
