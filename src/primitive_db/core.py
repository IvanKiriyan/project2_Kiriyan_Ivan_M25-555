"""
Основная логика работы с таблицами / итоговый файл с декораторами
"""

from typing import Any

from src.decorators import confirm_action, create_cacher, log_time #импортируем созданные декораторы

SUPPORTED_TYPES = {"int", "str", "bool"}

class DbValueError(ValueError):
    """Выводит ошибки"""

#Функция создания таблиц
def create_table(metadata: dict, table_name: str, columns: list[str]) -> dict:
    if table_name in metadata:
        raise ValueError(f'Таблица "{table_name}" уже существует.')

    if not columns:
        raise DbValueError("columns")

    result_columns: list[str] = ["ID:int"]

    seen_names: set[str] = {"id"}

    for col in columns:
        if ":" not in col:
            raise DbValueError(col)

        name, col_type = col.split(":", 1)
        name = name.strip()
        col_type = col_type.strip()

        if name == "":
            raise DbValueError(col)

        if name.lower() in seen_names:
            raise DbValueError(name)

        if col_type not in SUPPORTED_TYPES:
            raise DbValueError(col_type)

        result_columns.append(f"{name}:{col_type}")
        seen_names.add(name.lower())

    metadata[table_name] = result_columns
    return metadata

#Удаление созданных таблиц
@confirm_action("удаление таблицы")
def drop_table(metadata: dict, table_name: str) -> dict:
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    del metadata[table_name]
    return metadata

#Список таблиц
def list_tables(metadata: dict) -> list[str]:
    return sorted(metadata.keys())

#Выводит колонки
def format_columns_for_print(columns: list[str]) -> str:
    return ", ".join(columns)

#Обновление логики - CRUD
@log_time
def insert(
    metadata: dict,
    table_name: str,
    values: list[str],
    table_data: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    schema = metadata[table_name]
    if len(values) != len(schema) - 1:
        raise DbValueError("values")

    max_id = 0
    for row in table_data:
        row_id = row.get("ID", 0)
        if isinstance(row_id, int) and row_id > max_id:
            max_id = row_id
    new_id = max_id + 1

    record: dict[str, Any] = {"ID": new_id}

    for idx, col_def in enumerate(schema[1:], start=0):
        col_name, col_type = col_def.split(":", 1)
        col_name = col_name.strip()
        col_type = col_type.strip()
        raw = values[idx].strip()

        if col_type == "int":
            try:
                record[col_name] = int(raw)
            except ValueError as e:
                raise DbValueError(raw) from e

        elif col_type == "bool":
            low = raw.lower()
            if low == "true":
                record[col_name] = True
            elif low == "false":
                record[col_name] = False
            else:
                raise DbValueError(raw)

        elif col_type == "str":
            if len(raw) >= 2 and (
                (raw[0] == '"' and raw[-1] == '"') or (raw[0] == "'" and raw[-1] == "'")
            ):
                record[col_name] = raw[1:-1]
            else:
                raise DbValueError(raw)

        else:
            raise DbValueError(col_type)

    table_data.append(record)
    return table_data


_SELECT_CACHE = create_cacher()


# Фукнция select
@log_time
def select(
    table_data: list[dict[str, Any]],
    where_clause: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    def compute() -> list[dict[str, Any]]:
        if where_clause is None:
            return table_data

        (key, value), = where_clause.items()
        result: list[dict[str, Any]] = []
        for row in table_data:
            if row.get(key) == value:
                result.append(row)
        return result

    max_id = 0
    for row in table_data:
        row_id = row.get("ID", 0)
        if isinstance(row_id, int) and row_id > max_id:
            max_id = row_id

    if where_clause is None:
        cache_key = ("select_all", len(table_data), max_id)
    else:
        (k, v), = where_clause.items()
        cache_key = ("select_where", k, v, len(table_data), max_id)

    return _SELECT_CACHE(cache_key, compute)


#Update для обновления записей
def update(
    table_data: list[dict[str, Any]],
    set_clause: dict[str, Any],
    where_clause: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[int]]:
    (where_key, where_val), = where_clause.items()
    (set_key, set_val), = set_clause.items()

    updated_ids: list[int] = []
    for row in table_data:
        if row.get(where_key) == where_val:
            row[set_key] = set_val
            if isinstance(row.get("ID"), int):
                updated_ids.append(row["ID"])

    return table_data, updated_ids


#Удаление записей
@confirm_action("удаление записи")
def delete(
    table_data: list[dict[str, Any]],
    where_clause: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[int]]:
    (key, value), = where_clause.items()

    deleted_ids: list[int] = []
    new_data: list[dict[str, Any]] = []

    for row in table_data:
        if row.get(key) == value:
            if isinstance(row.get("ID"), int):
                deleted_ids.append(row["ID"])
        else:
            new_data.append(row)

    return new_data, deleted_ids