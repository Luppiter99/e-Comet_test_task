"""
Скрипт для обновления данных о репозиториях и их активности.

Содержит:
- Обновление топ-100 репозиториев GitHub (с сохранением в базу данных).
- Обновление данных об активности (коммитах) для каждого репозитория из топ-100
  за последние 24 часа.
- Управление подключением и отключением базы данных.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from app.db.connection import db
from app.services.github_parser import (update_top100_in_db,
                                        update_activity_in_db)


async def refresh_data():
    """
    Обновляет данные в базе данных:
    1. Получает и сохраняет топ-100 репозиториев GitHub.
    2. Для каждого репозитория из топ-100 обновляет информацию
       об активности (коммитах) за последние 24 часа.
    """
    # Обновляем топ-100 репозиториев
    await update_top100_in_db()

    # Получаем список репозиториев из top100
    async with db.connect_to_pool() as conn:
        records = await conn.fetch("SELECT owner, repo FROM top100")

    # Определяем период за последние 24 часа
    until_dt = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)
    since_dt = until_dt - timedelta(days=1)

    since_str = since_dt.strftime("%Y-%m-%dT00:00:00Z")
    until_str = until_dt.strftime("%Y-%m-%dT00:00:00Z")

    # Обновляем активность для каждого репозитория из топ-100
    for record in records:
        owner = record["owner"]
        full_name = record["repo"]
        # Разделяем полный путь репозитория на owner/repo
        _, repo_name = full_name.split("/", 1)
        await update_activity_in_db(owner, repo_name, since_str, until_str)


async def main():
    """
    Основная функция скрипта.

    Выполняет:
    - Подключение к базе данных.
    - Вызов функции `refresh_data` для обновления данных.
    - Отключение от базы данных.
    """
    await db.connect()
    await refresh_data()
    await db.disconnect()


def handler(event, context):
    """
    Хэндлер для Яндекс.Функции.
    Яндекс.Функция будет вызывать эту функцию при срабатывании триггера.
    """
    asyncio.run(main())
    return {"status": "ok", "message": "Data refreshed successfully."}
