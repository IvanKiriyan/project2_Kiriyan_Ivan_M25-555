"""
Основная логика работы с таблицами
"""

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

#Функция удаления созданных таблиц
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