"""
Запуск, игровой цикл и парсинг команд / финальный с выводом ошибок через декораторы
"""
import shlex

import prompt
from prettytable import PrettyTable

from src.decorators import handle_db_errors

from .core import (
    DbValueError,
    create_table,
    delete,
    drop_table,
    format_columns_for_print,
    insert,
    list_tables,
    select,
    update,
)
from .utils import load_metadata, load_table_data, save_metadata, save_table_data

META_FILEPATH = "db_meta.json"

#Выводит вспомогательные команды для пользователей
def print_help() -> None:
    print("\n***Операции с данными***\n")
    print("Функции:")
    print('<command> insert into <имя_таблицы> values (<значение1>, <значение2>, ...) - создать запись.')
    print("<command> select from <имя_таблицы> where <столбец> = <значение> - прочитать записи по условию.")
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец1> = <новое_значение1> "
        "where <столбец_условия> = <значение_условия> - обновить запись."
    )
    print("<command> delete from <имя_таблицы> where <столбец> = <значение> - удалить запись.")
    print("<command> info <имя_таблицы> - вывести информацию о таблице.\n")

    print("Команды управления таблицами:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу\n")

    print("Общие команды:")
    print("<command> exit - выход из программы")
    print("<command> help- справочная информация\n")

#Обновленный двигатель - добавлены CRUD-команды
def _split_values(values_text: str) -> list[str]:
    items: list[str] = []
    buf = ""
    in_quotes = False
    quote_char = ""

    for ch in values_text:
        if ch in ("'", '"'):
            if not in_quotes:
                in_quotes = True
                quote_char = ch
            elif quote_char == ch:
                in_quotes = False

        if ch == "," and not in_quotes:
            items.append(buf.strip())
            buf = ""
            continue

        buf += ch

    if buf.strip():
        items.append(buf.strip())

    return items


def _parse_expr(text: str) -> tuple[str, str]:
    if "=" not in text:
        raise DbValueError(text)

    left, right = text.split("=", 1)
    col = left.strip()
    raw = right.strip()

    if col == "" or raw == "":
        raise DbValueError(text)

    return col, raw


def _cast_by_schema(metadata: dict, table_name: str, col: str, raw: str):
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    col_type = None
    for item in metadata[table_name]:
        name, t = item.split(":", 1)
        if name.strip() == col:
            col_type = t.strip()
            break

    if col_type is None:
        raise DbValueError(col)

    if col_type == "int":
        try:
            return int(raw)
        except ValueError as e:
            raise DbValueError(raw) from e

    if col_type == "bool":
        low = raw.lower()
        if low == "true":
            return True
        if low == "false":
            return False
        raise DbValueError(raw)

    if col_type == "str":
        s = raw.strip()
        if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
            return s[1:-1]
        raise DbValueError(raw)

    raise DbValueError(col_type)

#Вывод таблицы
def _print_table(metadata: dict, table_name: str, rows: list[dict]) -> None:
    columns = [item.split(":", 1)[0].strip() for item in metadata.get(table_name, [])]
    table = PrettyTable()
    table.field_names = columns
    for row in rows:
        table.add_row([row.get(col) for col in columns])
    print(table)

#Декораторы
@handle_db_errors
def _cmd_list_tables(metadata: dict) -> None:
    tables = list_tables(metadata)
    if not tables:
        print("Таблиц нет.") #проверка существования таблиц
    else:
        for name in tables:
            print(f"- {name}")


@handle_db_errors
def _cmd_create_table(metadata: dict, rest: list[str]) -> None:
    if len(rest) < 2:
        raise DbValueError("create_table")

    table_name = rest[0]
    columns = rest[1:]

    new_metadata = create_table(metadata, table_name, columns)
    save_metadata(META_FILEPATH, new_metadata)

    cols_text = format_columns_for_print(new_metadata[table_name])
    print(f'Таблица "{table_name}" успешно создана со столбцами: {cols_text}')


@handle_db_errors
def _cmd_drop_table(metadata: dict, rest: list[str]) -> None:
    if len(rest) != 1:
        raise DbValueError("drop_table")

    table_name = rest[0]
    new_metadata = drop_table(metadata, table_name)

    if new_metadata is None:
        return

    save_metadata(META_FILEPATH, new_metadata)
    print(f'Таблица "{table_name}" успешно удалена.')


@handle_db_errors
def _cmd_insert(metadata: dict, user_input: str, args: list[str]) -> None:
    if len(args) < 4 or args[1] != "into" or args[3] != "values":
        raise DbValueError("insert")

    table_name = args[2]
    table_data = load_table_data(table_name)

    low = user_input.lower()
    pos = low.find("values")
    if pos == -1:
        raise DbValueError("values")

    after = user_input[pos + len("values") :].strip()
    if not (after.startswith("(") and after.endswith(")")):
        raise DbValueError(after)

    inside = after[1:-1].strip()
    values = _split_values(inside)

    table_data = insert(metadata, table_name, values, table_data)
    save_table_data(table_name, table_data)

    new_id = table_data[-1]["ID"]
    print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')


@handle_db_errors
def _cmd_select(metadata: dict, user_input: str, args: list[str]) -> None:
    if len(args) < 3 or args[1] != "from":
        raise DbValueError("select")

    table_name = args[2]
    table_data = load_table_data(table_name)

    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    if len(args) == 3:
        rows = select(table_data)
        if not rows:
            print("Записей нет.")
        else:
            _print_table(metadata, table_name, rows)
        return

    if len(args) >= 5 and args[3] == "where":
        where_text = user_input.lower().split("where", 1)[1].strip()
        col, raw = _parse_expr(where_text)
        value = _cast_by_schema(metadata, table_name, col, raw)

        rows = select(table_data, {col: value})
        if not rows:
            print("Записей нет.")
        else:
            _print_table(metadata, table_name, rows)
        return

    raise DbValueError("select")


@handle_db_errors
def _cmd_update(metadata: dict, user_input: str, args: list[str]) -> None:
    if len(args) < 2:
        raise DbValueError("update")

    table_name = args[1]
    table_data = load_table_data(table_name)

    low = user_input.lower()
    if " set " not in low or " where " not in low:
        raise DbValueError("update")

    set_part = user_input.split("set", 1)[1].rsplit("where", 1)[0].strip()
    where_part = user_input.rsplit("where", 1)[1].strip()

    set_col, set_raw = _parse_expr(set_part)
    where_col, where_raw = _parse_expr(where_part)

    if set_col == "ID":
        raise DbValueError("ID")

    set_val = _cast_by_schema(metadata, table_name, set_col, set_raw)
    where_val = _cast_by_schema(metadata, table_name, where_col, where_raw)

    table_data, updated_ids = update(table_data, {set_col: set_val}, {where_col: where_val})
    if not updated_ids:
        print("Ошибка: Записи не найдены.")
        return

    save_table_data(table_name, table_data)
    print(f'Запись с ID={updated_ids[0]} в таблице "{table_name}" успешно обновлена.')


@handle_db_errors
def _cmd_delete(metadata: dict, user_input: str, args: list[str]) -> None:
    if len(args) < 4 or args[1] != "from":
        raise DbValueError("delete")

    table_name = args[2]
    table_data = load_table_data(table_name)

    if args[3] != "where":
        raise DbValueError("where")

    where_text = user_input.lower().split("where", 1)[1].strip()
    col, raw = _parse_expr(where_text)
    value = _cast_by_schema(metadata, table_name, col, raw)

    result = delete(table_data, {col: value})
    if result is None:
        return

    table_data, deleted_ids = result
    if not deleted_ids:
        print("Ошибка: Записи не найдены.")
        return

    save_table_data(table_name, table_data)
    print(f'Запись с ID={deleted_ids[0]} успешно удалена из таблицы "{table_name}".')


@handle_db_errors
def _cmd_info(metadata: dict, args: list[str]) -> None:
    if len(args) != 2:
        raise DbValueError("info")

    table_name = args[1]
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    table_data = load_table_data(table_name)
    cols_text = format_columns_for_print(metadata[table_name])

    print(f"Таблица: {table_name}")
    print(f"Столбцы: {cols_text}")
    print(f"Количество записей: {len(table_data)}")

#Основной цикл: чтение, парсинг команд, обработка
def run() -> None:
    print_help()

    while True:
        metadata = load_metadata(META_FILEPATH)
        user_input = prompt.string(">>>Введите команду: ").strip()
        args = shlex.split(user_input)

        if not args:
            continue

        command, *rest = args

        match command:
            case "exit":
                print("Всего доброго!")
                return

            case "help":
                print_help()

            case "list_tables":
                _cmd_list_tables(metadata)

            case "create_table":
                _cmd_create_table(metadata, rest)

            case "drop_table":
                _cmd_drop_table(metadata, rest)

            case "insert":
                _cmd_insert(metadata, user_input, args)

            case "select":
                _cmd_select(metadata, user_input, args)

            case "update":
                _cmd_update(metadata, user_input, args)

            case "delete":
                _cmd_delete(metadata, user_input, args)

            case "info":
                _cmd_info(metadata, args)

            case _:
                print(f"Функции {command} нет. Попробуйте снова.")