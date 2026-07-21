"""Конфигурация проекта.

Разделяем два уровня настроек:
  - Settings — «окружение»: ключ и параметры LLM, путь к файлу категорий.
    Берётся из .env один раз на запуск процесса.
  - RunParams — «параметры конкретного запуска»: путь вывода, использовать ли LLM,
    имя листа и т.п. Приходит из JSON в командной строке.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Optional, Union

from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень проекта — чтобы дефолтные относительные пути не зависели от того,
# из какой папки запущен CLI.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Настройки окружения (.env)."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # LLM-провайдер (OpenAI-совместимый). По умолчанию — DeepSeek.
    llm_provider: str = "deepseek"
    llm_api_key: str = ""
    llm_model: str = ""                       # пусто → дефолт провайдера
    llm_base_url: str = ""                    # пусто → дефолт провайдера
    llm_temperature: float = 0.0             # структуру определяем детерминированно
    llm_max_tokens: int = 512

    # Файл с категориями (ключевые слова → категория).
    categories_file: str = str(PROJECT_ROOT / "categories.json")

    # Сколько строк-образцов (кроме заголовка) отправлять в LLM.
    sample_rows: int = 5
    # Сколько верхних строк просматривать в поиске заголовка.
    header_scan_limit: int = 25

    @property
    def has_llm_key(self) -> bool:
        return bool(self.llm_api_key) and "replace_me" not in self.llm_api_key


@dataclass
class RunParams:
    """Параметры конкретного запуска (JSON из командной строки)."""

    output: Optional[str] = None                    # куда сохранить отчёт
    use_llm: bool = True                            # определять структуру через LLM
    sheet: Optional[Union[str, int]] = None         # имя/индекс листа (для xlsx)
    categories_file: Optional[str] = None           # переопределить файл категорий
    report_title: str = "Отчёт по прайс-листу"

    @classmethod
    def from_json(cls, raw: Optional[str]) -> "RunParams":
        if not raw:
            return cls()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Параметры не являются корректным JSON: {exc}. "
                'Пример: \'{"use_llm": false, "output": "out.xlsx"}\''
            ) from exc
        if not isinstance(data, dict):
            raise ValueError("Параметры должны быть JSON-объектом, например {\"use_llm\": false}")
        allowed = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"Неизвестные параметры: {', '.join(sorted(unknown))}")
        return cls(**data)


settings = Settings()
