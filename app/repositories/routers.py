"""
Маршруты (эндпоинты) для получения информации о публичных репозиториях GitHub.

Содержит два эндпоинта:
1. /api/repos/top100 - для получения списка топ-100 публичных репозиториев,
   отсортированных по заданному критерию и порядку.
2. /api/repos/{owner}/{repo}/activity - для получения информации об активности
   (коммитах) конкретного репозитория за указанный промежуток времени.

Реализация основана на данных, хранящихся в PostgreSQL, которые
периодически обновляются парсером.
"""
import asyncpg  # type: ignore
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.connection import get_connection
from .crud import get_top_repos, fetch_repo_activity
from .schemas import TopRepo, SortBy, Order, RepoActivity

router = APIRouter(
    prefix="/api/repos",
    tags=["Repositories"]
)


@router.get("/top100", response_model=list[TopRepo])
async def read_top_100_repos(
    sort_by: SortBy = Query(SortBy.STARS, description="Поле для сортировки"),
    order: Order = Query(Order.DESC, description="Порядок сортировки"),
    connection: asyncpg.Connection = Depends(get_connection)
):
    """
    Получить список топ-100 публичных репозиториев,
    отсортированных по указанному полю и в указанном порядке.

    Параметры:
        sort_by (SortBy): Поле для сортировки (stars, watchers, forks,
        open_issues).
        order (Order): Порядок сортировки (ASC или DESC).
        connection (asyncpg.Connection): Соединение с базой данных,
            предоставленное через зависимость.

    Возвращает:
        list[Top100]: Список из максимум 100 репозиториев в
        формате схемы Top100.

    Исключения:
        HTTPException(500): При ошибке взаимодействия с базой данных или других
        непредвиденных ошибках.
    """
    try:
        result = await get_top_repos(connection, sort_by, order)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка сервера: {e}"
        )


@router.get("/{owner}/{repo}/activity", response_model=list[RepoActivity])
async def get_repo_activity(
    owner: str,
    repo: str,
    since: date,
    until: date,
    connection: asyncpg.Connection = Depends(get_connection)
) -> list[RepoActivity]:
    """
    Получить активность репозитория (коммиты) за указанный период.

    Параметры:
        owner (str): Владелец репозитория.
        repo (str): Имя репозитория.
        since (date): Начальная дата периода (включительно).
        until (date): Конечная дата периода (включительно).
        connection (asyncpg.Connection): Соединение с базой данных.

    Возвращает:
        list[RepoActivity]: Список объектов RepoActivity, каждый из которых
        содержит дату, количество коммитов и список авторов в этот день.

    Исключения:
        HTTPException(400): Если `since` больше `until`.
        HTTPException(404): Если за указанный период нет активности.
        HTTPException(500): При ошибке взаимодействия с базой данных
            или других непредвиденных ошибках.
    """
    if since > until:
        raise HTTPException(status_code=400,
                            detail="`since` не может быть больше `until`")

    try:
        data = await fetch_repo_activity(connection, owner, repo, since, until)
        if not data:
            raise HTTPException(
                status_code=404,
                detail="No activity found for the given period"
            )
        return data
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"{e}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка сервера: {e}"
        )
