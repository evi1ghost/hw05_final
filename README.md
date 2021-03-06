# Yuatube / HobbyWorld
**_Учебный проект_**

### Краткое описание:
Социальная сеть, в которой пользователи могут публиковать записи/сообщения и просматривать сообщению других пользователей. Реализованы механизм комментариев к записям, возможность подписки на публикации интересующий авторов, добавление изображений к публикациям, регистрация пользователей.
В проекте использованы следующие инструменты:
_Python3, Django, DjangoORM. SQLite_

## Подготовка проекта
### Создать и активировать виртуальное окружение, установить зависимости:
```sh
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
## Переименовать файл .env.example (/project_dir/reference_book/reference_book/.env.example) в .env и указать в нем недостающую информацию:
Для генерации SECRET_KEY:
```sh
openssl rand -hex 32
```
Полученное значение копируем в .env

## Создать базу и применить миграции:
Из директории /project_dir/yatube/ выполнить:
```sh
python manage.py migrate
```

## Создание суперпользователя:
Выполнить команду и следовать инструкциям:
```sh
python manage.py createsuperuser
```
После создания супепользователя можно использовать данные учетной записи для страницы администрирования - http://127.0.0.1:8000/admin/

## Запустить проект:
```sh
python manage.py runserver
```
**_В репозитории отсутствуют статик-файлы. Для корректного отображения страниц необходимо подключить bootstrap v4._**
