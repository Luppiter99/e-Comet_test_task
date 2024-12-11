# Создание функции (если уже есть, команда не упадёт из-за `|| true`)
yc serverless function create --name github-parser || true

# Создание новой версии функции с абстрактными переменными окружения
yc serverless function version create \
  --function-name github-parser \
  --runtime python311 \
  --entrypoint update_data.handler \
  --memory 512m \
  --execution-timeout 300s \
  --environment DB_USER=example_user \
  --environment DB_PASSWORD=example_password \
  --environment DB_HOST=example_host \
  --environment DB_PORT=5432 \
  --environment DB_NAME=example_db \
  --source-path function.zip

# Создание триггера на ежедневный запуск
yc serverless trigger create cron \
  --name github_parser_trigger \
  --function-name github-parser \
  --cron-expression "0 0 * * *" \
  --invoke-function-with "{}"
