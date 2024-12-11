# GitHub Repository Activity API на FastAPI и Docker

## Описание проекта

Данный проект представляет собой **RESTful API-приложение**, разработанное на базе **FastAPI**, обёрнутое в **Docker Compose** и интегрированное с **Яндекс.Облаком** для периодического обновления данных о репозиториях GitHub. Сервис позволяет получить:

- **Топ-100 репозиториев** по количеству звёзд  
- **Активность (коммиты)** выбранного репозитория за определённый промежуток времени  

Периодическое обновление данных обеспечивается облачной функцией (Serverless Function), развёрнутой в Яндекс.Облаке.

## Стек технологий

- Backend: FastAPI  
- База данных: PostgreSQL  
- HTTP-клиент для GitHub API: ghapi  
- Контейнеризация: Docker, Docker Compose  
- Облачные функции: Яндекс.Облако (Yandex.Cloud) Serverless Functions  
- Асинхронная работа с БД: asyncpg  

## Установка и запуск проекта

### Требования

- Python 3.11+  
- Docker и Docker Compose  

### Локальная установка
1. **Клонируйте репозиторий:**

git clone <URL репозитория>
cd e-Comet_test_task

2. **Создайте виртуальное окружение и активируйте его:**

python3 -m venv venv
source venv/bin/activate  # Для Linux/Mac
.\venv\Scripts\activate   # Для Windows

3. **Установите зависимости:**

pip install -r requirements.txt

4. **Запустите проект через Docker Compose:**
docker-compose up --build

API будет доступно по адресу:
http://127.0.0.1:8000

**Если вы хотите использовать глобальное подключение,  вам необходимо изменить конфигурацию Docker**

## Работа с Яндекс.Облаком

1) Разверните функцию с помощью скрипта: Используйте предоставленный файл deploy.sh для автоматического развёртывания функции и триггера:

# Деплой функции
bash deploy.sh

2) Задайте переменные окружения: Замените значения на ваши:

DB_USER: имя пользователя базы данных.
DB_PASSWORD: пароль.
DB_HOST: хост базы данных.
DB_PORT: порт (по умолчанию 5432).
DB_NAME: имя базы данных.

## Использование API


# Документация API
# После запуска приложения документация доступна:

Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc

## Основные эндпоинты
# Получение топ-100 репозиториев
GET /api/repos/top100

**Параметры запроса:**
sort_by: Поле для сортировки (stars, watchers, forks, open_issues). По умолчанию stars.
order: Порядок сортировки (ASC, DESC). По умолчанию DESC.

**Пример запроса:**
curl -X GET "http://127.0.0.1:8000/api/repos/top100?sort_by=stars&order=desc" -H "accept: application/json"


# Получение активности репозитория
GET /api/repos/{owner}/{repo}/activity

**Параметры запроса:**

since: Начальная дата в формате YYYY-MM-DD.
until: Конечная дата в формате YYYY-MM-DD.
**Пример запроса:**

curl -X GET "http://127.0.0.1:8000/api/repos/{owner}/{repo}/activity?since=2023-01-01&until=2023-01-31" -H "accept: application/json"
```

## Структура проекта

```plaintext
e-Comet_test_task/
│  Dockerfile               # Файл для сборки Docker-образа
│  docker-compose.yml       # Конфигурация Docker Compose
│  deploy.sh                # Скрипт для деплоя в Яндекс.Облако
│  requirements.txt         # Зависимости проекта
│  update_data.py           # Скрипт для обновления данных
│  function.zip             # Архив для деплоя функции в облако
│
├── app/                    # Основной код приложения
│   ├── db/                 # Подключение к базе данных
│   ├── services/           # Логика получения данных из GitHub API
│   ├── repositories/       # Логика работы с маршрутами и круд
│   ├── main.py             # Точка входа в приложение FastAPI
│   └── __init__.py         # Инициализация модуля
│
├── dependencies/           # Зависимости для облачной функции
```

## Особенности


- Периодический парсинг данных: Ежедневное обновление данных через облачную функцию.
- Чистый SQL: Запросы к базе данных выполняются напрямую для повышения производительности.
- Асинхронная обработка: Использование asyncpg для эффективного взаимодействия с базой данных.

