import asyncpg  # type: ignore
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Создание пула подключений"""
        self.pool = await asyncpg.create_pool(dsn=DATABASE_URL,
                                              min_size=1,
                                              max_size=25)

    async def disconnect(self):
        """Закрытие пула подключений"""
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def connect_to_pool(self):
        """Контекстный менеджер для получения соединения из пула"""
        async with self.pool.acquire() as connection:
            yield connection


db = Database()


# Функция для использования в FastAPI-зависимостях
async def get_connection():
    async with db.connect_to_pool() as connection:
        yield connection
