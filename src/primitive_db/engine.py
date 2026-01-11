"""
Запуск, игровой цикл и парсинг команд
"""
import shlex

import prompt

from .core import DbValueError, create_table, drop_table, format_columns_for_print, list_tables
from .utils import load_metadata, save_metadata

META_FILEPATH = "db_meta.json"

#Выводит вспомогательные команды для пользователей
def print_help() -> None:
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")

#Главная функция
def run() -> None:
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> <столбец2:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")

    while True:
        #основной цикл программы
        metadata = load_metadata(META_FILEPATH)

        user_input = prompt.string(">>>Введите команду: ").strip()
        args = shlex.split(user_input)

        if not args:
            continue

        command, *rest = args

        try:
            match command:
                case "exit":
                    print("Всего доброго!")
                    return

                case "help":
                    print_help()

                case "list_tables":
                    tables = list_tables(metadata)
                    if not tables:
                        print("Таблиц нет.")
                    else:
                        for name in tables:
                            print(f"- {name}")

                case "create_table":
                    if len(rest) < 2:
                        raise DbValueError("create_table")

                    table_name = rest[0]
                    columns = rest[1:]

                    metadata = create_table(metadata, table_name, columns)
                    save_metadata(META_FILEPATH, metadata)

                    cols_text = format_columns_for_print(metadata[table_name])
                    print(f'Таблица "{table_name}" успешно создана со столбцами: {cols_text}')

                case "drop_table":
                    if len(rest) != 1:
                        raise DbValueError("drop_table")

                    table_name = rest[0]
                    metadata = drop_table(metadata, table_name)
                    save_metadata(META_FILEPATH, metadata)
                    print(f'Таблица "{table_name}" успешно удалена.')

                case _:
                    print(f"Функции {command} нет. Попробуйте снова.")

        except DbValueError as e:
            print(f"Некорректное значение: {e}. Попробуйте снова.")
        except ValueError as e:
            print(f"Ошибка: {e}")