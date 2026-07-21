"""Поиск строки-заголовка (шапки) в кривом прайсе.

Реальные прайсы начинаются с мусора: название фирмы, «Прайс-лист от …»,
контакты, пустые строки. Настоящая шапка таблицы — где-то ниже. Мы НЕ
привязываемся к номеру строки, а ищем ту, что больше всего похожа на заголовок:
считаем, сколько РАЗНЫХ ролей колонок (название/артикул/цена/кол-во) в ней
угадывается по ключевым словам. Побеждает строка с максимальным числом ролей.
"""

from __future__ import annotations

from app.keywords import match_column_role
from app.reader import Grid

# Минимум разных ролей в строке, чтобы считать её заголовком.
# Достаточно двух (например, «Наименование» + «Цена») — этого хватает, чтобы
# отличить шапку от строки с адресом фирмы.
MIN_ROLES = 2


class HeaderNotFoundError(RuntimeError):
    """Не удалось найти строку, похожую на заголовок таблицы."""


def _score_row(row: list[str]) -> int:
    """Сколько разных ролей колонок распознано в строке."""
    roles = {match_column_role(cell) for cell in row}
    roles.discard(None)
    return len(roles)


def find_header_row(grid: Grid, scan_limit: int = 25) -> int:
    """Вернуть индекс строки-заголовка. Просматриваем только верхние scan_limit строк."""
    best_index = -1
    best_score = 0

    for index, row in enumerate(grid[:scan_limit]):
        score = _score_row(row)
        # Строго «>»: при равенстве оставляем более верхнюю строку —
        # обычно настоящая шапка выше повторов и подзаголовков.
        if score > best_score:
            best_score = score
            best_index = index

    if best_index < 0 or best_score < MIN_ROLES:
        raise HeaderNotFoundError(
            "Не нашёл строку-заголовок. Ожидаю колонки вроде "
            "«Наименование», «Артикул», «Цена», «Кол-во». "
            "Проверьте, что в файле есть таблица с такими заголовками."
        )
    return best_index
