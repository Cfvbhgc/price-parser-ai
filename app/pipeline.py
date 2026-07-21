"""Пайплайн: полный путь от кривого прайса до аккуратного отчёта.

    файл → сетка → строка-заголовок → маппинг колонок (LLM/эвристика)
         → извлечение товаров → категоризация → Excel-отчёт

Каждый шаг вынесен в свой модуль; здесь только оркестрация и сбор статистики.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from app.categorizer import Categorizer
from app.config import RunParams, Settings, settings as default_settings
from app.extractor import extract_products
from app.reader import read_grid
from app.report import write_report
from app.structure import detect_structure

logger = logging.getLogger(__name__)


class PipelineError(RuntimeError):
    """Понятная пользователю ошибка обработки прайса."""


@dataclass
class PipelineResult:
    output_path: Path
    total_products: int
    header_row: int              # номер строки-заголовка (1-based, как в Excel)
    mapping_method: str          # как определён маппинг: "llm" / "эвристика"
    by_category: dict[str, int] = field(default_factory=dict)


def _default_output(input_path: Path) -> Path:
    return Path("data/reports") / f"{input_path.stem}_отчёт.xlsx"


def process(
    input_path: str | Path,
    params: RunParams | None = None,
    settings: Settings = default_settings,
) -> PipelineResult:
    params = params or RunParams()
    input_path = Path(input_path)

    # 1. Чтение файла в сетку (с разворотом объединённых ячеек).
    grid = read_grid(input_path, sheet=params.sheet)

    # 2. Определение структуры: где заголовок и где какая колонка.
    structure = detect_structure(grid, use_llm=params.use_llm, settings=settings)
    logger.info(
        "Заголовок в строке %s, маппинг определён через: %s",
        structure.header_index + 1,
        structure.method,
    )

    # 3. Извлечение товаров по маппингу (весь файл — обычным кодом).
    products = extract_products(grid, structure.header_index, structure.mapping)
    if not products:
        raise PipelineError(
            "Не удалось извлечь ни одной позиции. Возможно, под заголовком нет "
            "строк с товарами или не распозналась колонка с ценой/артикулом."
        )

    # 4. Категоризация.
    categories_file = params.categories_file or settings.categories_file
    categorizer = Categorizer.from_file(categories_file)
    categorizer.categorize(products)

    # 5. Формирование отчёта.
    output_path = Path(params.output) if params.output else _default_output(input_path)
    write_report(products, output_path, title=params.report_title)

    by_category = dict(Counter(p.category for p in products))
    return PipelineResult(
        output_path=output_path,
        total_products=len(products),
        header_row=structure.header_index + 1,
        mapping_method=structure.method,
        by_category=dict(sorted(by_category.items(), key=lambda kv: -kv[1])),
    )
