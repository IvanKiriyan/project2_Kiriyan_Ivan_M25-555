import json
import os
from typing import Any

DATA_DIR = "data" #добавлена папка для хранения

#Функция для загрузки данных из JSON
def load_metadata(filepath: str) -> dict[str, Any]:
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

#Функция сохранения данных в JSON
def save_metadata(filepath: str, data: dict[str, Any]) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

#Функция вызова таблицы
def load_table_data(table_name: str) -> list[dict[str, Any]]:
    filepath = os.path.join(DATA_DIR, f"{table_name}.json")
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

#Функция сохранения таблицы
def save_table_data(table_name: str, data: list[dict[str, Any]]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, f"{table_name}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)