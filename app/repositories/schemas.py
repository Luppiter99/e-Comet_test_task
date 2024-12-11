"""
Схемы данных для работы с API репозиториев.

Модели описывают структуры данных, используемые для валидации входных
и выходных данных в эндпоинтах. Используются Pydantic модели для
обеспечения типизации и проверки данных.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import date
from enum import Enum


class SortBy(str, Enum):
    """
    Перечисление для указания поля сортировки в запросах
    к топ-100 репозиториев.
    """
    WATCHERS = "watchers"
    FORKS = "forks"
    OPEN_ISSUES = "open_issues"
    STARS = "stars"


class Order(str, Enum):
    """
    Перечисление для указания порядка сортировки в запросах
    (по возрастанию или убыванию).
    """
    ASC = "ASC"
    DESC = "DESC"


class TopRepo(BaseModel):
    """
    Модель, описывающая репозиторий из таблицы топ-100.

    Поля:
        repo (str): Полное название репозитория (full_name в GitHub API).
        owner (str): Владелец репозитория.
        position_cur (int): Текущая позиция в топе.
        position_prev (Optional[int]): Предыдущая позиция в топе.
        Может быть None.
        stars (int): Количество звёзд (stars).
        watchers (int): Количество просмотров (watchers).
        forks (int): Количество форков (forks).
        open_issues (int): Количество открытых issues.
        language (Optional[str]): Основной язык репозитория. Может быть None.
    """
    repo: str
    owner: str
    position_cur: int
    position_prev: Optional[int] = None
    stars: int
    watchers: int
    forks: int
    open_issues: int
    language: Optional[str] = None


class RepoActivity(BaseModel):
    """
    Модель, описывающая активность репозитория за определённый день.

    Поля:
        date (date): Дата активности (день).
        commits (int): Количество коммитов за день.
        authors (list[str]): Список авторов,
        которые делали коммиты в этот день.
    """
    date: date
    commits: int
    authors: list[str]
