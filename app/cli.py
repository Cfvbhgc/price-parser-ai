"""Консольный запуск.

Примеры:
    python -m app.cli data/samples/postavshik1_krepezh.xlsx
    python -m app.cli data/samples/postavshik1_krepezh.xlsx '{"use_llm": false}'
    python -m app.cli price.xlsx '{"output": "out.xlsx", "sheet": "Прайс"}'

На вход: путь к файлу и (необязательно) JSON с параметрами.
На выход: путь к готовому отчёту и краткая статистика — или понятная ошибка.
"""

from __future__ import annotations

import argparse
import logging
import sys

from app.config import RunParams
from app.header_detector import HeaderNotFoundError
from app.column_mapper import MappingError
from app.pipeline import PipelineError, process
from app.reader import ReadError


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="price-parser",
        description="Разбор и категоризация прайс-листа произвольной структуры.",
    )
    parser.add_argument("input", help="путь к прайсу (.xlsx или .csv)")
    parser.add_argument(
        "params",
        nargs="?",
        default=None,
        help='JSON с параметрами, напр. \'{"use_llm": false, "output": "out.xlsx"}\'',
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="подробный лог"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s | %(name)s | %(message)s",
    )

    try:
        params = RunParams.from_json(args.params)
        result = process(args.input, params)
    except (ReadError, HeaderNotFoundError, MappingError, PipelineError, ValueError) as exc:
        # Ожидаемые ошибки — печатаем понятное описание, без стектрейса.
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1

    print(f"Готово. Отчёт: {result.output_path}")
    print(f"Позиций: {result.total_products}")
    print(f"Заголовок найден в строке: {result.header_row}")
    print(f"Структура определена через: {result.mapping_method}")
    print("По категориям:")
    for category, count in result.by_category.items():
        print(f"  • {category}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
