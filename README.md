# DataOx Junior Python Developer Test #4 | Remediation | Async Web Scraping www.kijiji.ca site #
Async Web Scraping www.kijiji.ca site with asyncio and save scraped information into PostgreSQL DB where ads id used as table id. Correction of remarks after code review.
***
### The project is built on libraries: ###
asyncio

aiohttp

BeautifulSoup

psycopg2

SQLAlchemy


### Для запуска программы: ###
1. Создать файл config.py по образцу config_example.py в котором указать параметры подключения к БД PostgreSQL для создания БД проекта, пользователя и таблицы.
2. После этого запустить файл database.py. Будет создана БД, пользователь БД и таблица для записи данных.
3. Запустить файл main.py

Парсинг производиться асинхронно. На моем компьютере это занимает 2,5 минуты на 3200 записей. 

После code review https://github.com/akatendra/DataOx-2-Async-ID исправлены 3 замечания:
1. Работа с "сырыми" SQL-запросами заменена на ORM SQLAlchemy.
2. Сокращена длина функции parse_html() за счет разделения ее на отдельные функции.
3. Добавлено программное определение количества страниц в пагинации.

В файле requirements.txt - список установленных в venv библиотек.
***
