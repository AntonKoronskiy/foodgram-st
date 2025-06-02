# Foodgram

"Foodgram" - приложение, позволяющее пользователям опубликовывать рецепты своих блюд, подписываться на других пользователей, просматривать их рецепты, добавлять рецепты в избранное и корзину, а также скачивать сохраненные в корзине рецепты в в формате '.txt'.

## Используемые технологии


## Запуск проекта
### 1. Клонирование проекта
Перед началом работы с приложением, необходимо клонировать репозиторий на свой компьютер. Для этого необходимо выполнить команду
```bash
git clone <URL-репозитория>
```

Перейти в каталог проект с помощью команды
```bash
cd foodgram-st
```
### 2. Создание файла окружения
С перейти в каталог `infra`, находящийся в корневой директории, используя команду
```bash
cd infra
```

В каталоге `infra` создать файл `.env`, который необходимо заполнить согласно примеру
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=foodgram
POSTGRES_USER=django_user
POSTGRES_PASSWORD=mysecretpassword
SECRET_KEY=<secrer-key>
DB_HOST=db
DB_PORT=5432
ALLOWED_HOSTS=localhost
DEBUG=False
```
где SECRET_KEY - уникальный ключ Django

### 3. Запуск проекта, используя Docker
Находясь в каталоге `infra`, выполнить команду
```bash
docker-compose up --build
```

### 4. Выполнить миграции, собрать статику, загрузить данные об ингредиентах в базу данных
Создание и выполнение миграция происходит, используя команды
```bash
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```

Загрузка статики
```bash
docker-compose exec backend python manage.py collectstatic
```

Загрузка ингредиентов в базу данных
```bash
docker-compose exec backend python manage.py load_database
```

## Достуы к проекту
`Главная страница` - `http://localhost:8000/`

`Админка` - `http://localhost/admin/`

`Документация` - `http://localhost//api/docs/`