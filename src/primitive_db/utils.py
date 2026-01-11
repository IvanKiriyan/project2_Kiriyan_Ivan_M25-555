import json
from typing import Any

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
