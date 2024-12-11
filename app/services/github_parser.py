"""
Модуль парсеров для сбора данных из GitHub API.

Содержит функции для получения данных о топ-100 репозиториях
и активности по коммитам, их агрегации и записи в базу данных.
"""

from datetime import datetime
from ghapi.all import GhApi  # type: ignore

from app.repositories.crud import (upsert_top_100_repo,
                                   upsert_repo_activity)
from app.db.connection import db


async def fetch_top100_repos():
    """
    Получаем топ 100 публичных репозиториев по количеству звёзд.

    Использует GitHub API через ghapi для выполнения запроса и формирования
    списка репозиториев с ключевыми метриками.

    Возвращает:
        list[dict]: Список словарей, где каждый словарь содержит данные
        о репозитории:
        - repo (str): Полное имя репозитория.
        - owner (str): Владелец репозитория.
        - position_cur (int): Текущая позиция в топе.
        - position_prev (Optional[int]): Предыдущая позиция
        (None, если неизвестно).
        - stars (int): Количество звёзд.
        - watchers (int): Количество просмотров.
        - forks (int): Количество форков.
        - open_issues (int): Количество открытых issues.
        - language (Optional[str]): Основной язык (None, если неизвестно).
    """
    api = GhApi()
    result = api.search.repos(q="stars:>1", sort="stars",
                              order="desc", per_page=100)

    repos = []
    if 'items' in result:
        for num, repo in enumerate(result['items'], start=1):
            repo_data = {
                "repo": repo['full_name'],
                "owner": repo['owner']['login'],
                "position_cur": num,
                "position_prev": None,
                "stars": repo['stargazers_count'],
                "watchers": repo['watchers_count'],
                "forks": repo['forks_count'],
                "open_issues": repo['open_issues_count'],
                "language": repo['language']
            }
            repos.append(repo_data)

    return repos


async def update_top100_in_db():
    """
    Обновляет данные о топ-100 репозиториях в таблице top100.

    Использует функцию fetch_top100_repos для получения списка
    репозиториев и синхронизирует данные с базой данных.
    """
    repos = await fetch_top100_repos()
    new_repos = {repo['repo'] for repo in repos}

    async with db.connect_to_pool() as connection:
        await connection.execute(
            "DELETE FROM top100 WHERE repo NOT IN (SELECT UNNEST($1::text[]))",
            list(new_repos)
        )

        for repo_data in repos:
            await upsert_top_100_repo(connection, repo_data)


async def fetch_commits(owner: str, repo: str, since: str, until: str):
    """
    Получает список коммитов для указанного репозитория и периода.

    Параметры:
        owner (str): Владелец репозитория.
        repo (str): Полное имя репозитория.
        since (str): Дата начала в формате ISO8601
        until (str): Дата окончания в формате ISO8601.

    Возвращает:
        list[dict]: Список коммитов, полученных через GitHub API.
    """
    try:
        api = GhApi()
        commits = []
        page = 1
        per_page = 100
        while True:
            result = api.repos.list_commits(
                owner, repo, since=since, until=until,
                per_page=per_page, page=page
                )
            if not result:
                break
            commits.extend(result)
            if len(result) < per_page:
                break
            page += 1

        return commits
    except Exception as e:
        print(f"Ошибка при запросе коммитов для {owner}/{repo}: {e}")
        return []


def aggregate_commits_by_day(commits):
    """
    Агрегирует список коммитов по датам.

    Преобразует список коммитов в словарь, где ключи — даты, а значения —
    количество коммитов и список авторов за соответствующий день.

    Параметры:
        commits (list[dict]): Список коммитов от GitHub API.

    Возвращает:
        dict: Словарь вида:
        {
            'YYYY-MM-DD': {
                'commits': int,
                'authors': set[str]
            }
        }
    """
    daily_stats = {}

    for c in commits:
        commit_date_str = c['commit']['author']['date']
        commit_date = datetime.fromisoformat(
            commit_date_str.replace('Z', '+00:00'))
        day_str = commit_date.date().isoformat()

        author_name = "Unknown"
        if c['commit']['author'] and 'name' in c['commit']['author']:
            author_name = c['commit']['author']['name']

        if day_str not in daily_stats:
            daily_stats[day_str] = {
                'commits': 0,
                'authors': set()
            }

        daily_stats[day_str]['commits'] += 1
        daily_stats[day_str]['authors'].add(author_name)

    return daily_stats


async def update_activity_in_db(owner: str, repo: str, since: str, until: str):
    """
    Обновляет данные об активности репозитория за указанный период.

    Параметры:
        owner (str): Владелец репозитория.
        repo (str): Полное имя репозитория.
        since (str): Дата начала в формате ISO8601.
        until (str): Дата окончания в формате ISO8601.

    Логика:
        - Получает коммиты через fetch_commits.
        - Агрегирует данные по дням через aggregate_commits_by_day.
        - Записывает данные в таблицу activity через insert_or_update_activity.
    """
    commits = await fetch_commits(owner, repo, since, until)
    daily_stats = aggregate_commits_by_day(commits)

    async with db.connect_to_pool() as connection:
        for date_str, data in daily_stats.items():
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            commits_count = data['commits']
            authors_list = list(data['authors'])
            await upsert_repo_activity(connection, owner, repo, date_obj,
                                       commits_count, authors_list)
