from datetime import date
import asyncpg  # type: ignore

from .schemas import TopRepo, SortBy, Order, RepoActivity


SORT_BY_MAPPING = {
    SortBy.WATCHERS: "watchers",
    SortBy.FORKS: "forks",
    SortBy.OPEN_ISSUES: "open_issues",
    SortBy.STARS: "stars"
}

ORDER_MAPPING = {
    Order.ASC: "ASC",
    Order.DESC: "DESC"
}


async def get_top_repos(
    connection: asyncpg.Connection,
    sort_by: SortBy = SortBy.STARS,
    order: Order = Order.DESC
) -> list[TopRepo]:
    sort_field = SORT_BY_MAPPING.get(sort_by)
    sort_order = ORDER_MAPPING.get(order)

    query = f"""
        SELECT repo, owner, position_cur, position_prev,
        stars, watchers, forks, open_issues, language
        FROM top100
        ORDER BY {sort_field} {sort_order}
        LIMIT 100
    """
    try:
        rows = await connection.fetch(query)
        return [TopRepo(**dict(row)) for row in rows]
    except asyncpg.PostgresError as e:
        raise RuntimeError(f"Database error: {str(e)}")


async def fetch_repo_activity(
    connection: asyncpg.Connection,
    owner: str,
    repo: str,
    since: date,
    until: date
) -> list[RepoActivity]:
    query = """
    SELECT date, commits, authors
    FROM activity
    WHERE owner = $1 and repo = $2
    AND date BETWEEN $3 AND $4
    ORDER BY date
    """
    try:
        rows = await connection.fetch(query, owner, repo, since, until)
        return [RepoActivity(**row) for row in rows]
    except asyncpg.PostgresError as e:
        raise RuntimeError(f"Database error: {str(e)}")


async def upsert_top_100_repo(
    connection: asyncpg.Connection,
    repo_data: dict
) -> None:
    """
    Вставляет или обновляет запись в таблицу top100.
    Если записи нет — вставляет, если есть — обновляет.

    Параметры:
        connection: asyncpg.Connection - активное подключение к БД
        repo_data: dict - словарь с ключами:
            "repo": str — уникальное имя репозитория (full_name)
            "owner": str — владелец
            "position_cur": int — текущая позиция в топе
            "position_prev": Optional[int] — предыдущая позиция
            (может быть None)
            "stars": int — количество звёзд
            "watchers": int — количество просмотров
            "forks": int — количество форков
            "open_issues": int — количество открытых issues
            "language": Optional[str] — язык (может быть None)
    """

    try:
        update_result = await connection.execute(
            """
            UPDATE top100
            SET position_prev = position_cur,
                position_cur = $2,
                stars = $3,
                watchers = $4,
                forks = $5,
                open_issues = $6,
                language = $7
            WHERE repo = $1
            """,
            repo_data["repo"],
            repo_data["position_cur"],
            repo_data["stars"],
            repo_data["watchers"],
            repo_data["forks"],
            repo_data["open_issues"],
            repo_data["language"]
        )

        # Проверяем, были ли затронуты строки
        if update_result == "UPDATE 0":
            # Если запись не обновлена, значит её нет. Вставляем.
            await connection.execute(
                """
                INSERT INTO top100 (repo, owner, position_cur, position_prev,
                stars, watchers, forks, open_issues, language)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                repo_data["repo"],
                repo_data["owner"],
                repo_data["position_cur"],
                repo_data["position_prev"],
                repo_data["stars"],
                repo_data["watchers"],
                repo_data["forks"],
                repo_data["open_issues"],
                repo_data["language"]
            )
    except asyncpg.PostgresError as e:
        raise RuntimeError(f"Database error in insert_or_update_top100: {e}")


async def upsert_repo_activity(
    connection: asyncpg.Connection,
    owner: str,
    repo: str,
    date: date,
    commits: int,
    authors: list[str]
) -> None:
    """
    Вставляет или обновляет запись в таблице activity.
    Если записи нет — вставляет, если есть — обновляет.

    Параметры:
        connection: asyncpg.Connection - активное подключение к БД
        owner: str - владелец репозитория
        repo: str - имя репозитория
        date: date - дата (формат: YYYY-MM-DD)
        commits: int - количество коммитов за день
        authors: List[str] - список логинов авторов коммитов
    """

    try:
        update_result = await connection.execute(
            """
            UPDATE activity
            SET commits = $4,
                authors = $5
            WHERE owner = $1 AND repo = $2 AND date = $3
            """,
            owner, repo, date, commits, authors
        )

        if update_result == "UPDATE 0":
            await connection.execute(
                """
                INSERT INTO activity (owner, repo, date, commits, authors)
                VALUES ($1, $2, $3, $4, $5)
                """,
                owner,
                repo,
                date,
                commits,
                authors
            )
    except asyncpg.PostgresError as e:
        raise RuntimeError(f"Database error in insert_or_update_activity: {e}")
