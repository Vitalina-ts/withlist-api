# Перевірки лабораторної роботи №4

## Файли та архітектура

CI: `.github/workflows/ci.yml`; Ruff і pytest: `pyproject.toml`.
Залежності API залишаються в `requirements.txt`; тестові залежності — у
`requirements-test.txt`; незалежний швидкий lint — у `requirements-lint.txt`.
Версії прямих і транзитивних залежностей зафіксовані через `==`.
`setup.py` містить інші версії: CI навмисно встановлює requirements, а не пакет через `pip install .`.

API зберігає створення таблиць під час імпорту. Фікстура `api` тимчасово
підміняє лише import-time `create_all`; підключення engine під час імпорту
заборонене. У production ця підміна не застосовується.
Redis отримує SSL-параметр лише для `rediss://`; `redis://` працює без TLS.
`DB_SSLMODE=disable` підходить для локальної БД; для віддаленої можна задати `require`.
Ваші попередні зміни Compose з DB_HOST=postgres збережені.

## Тести

- `test_health_without_database`: HTTP 200, status, Redis-статус і timestamp.
  Перевіряються два випадки: Redis доступний і недоступний. Redis підмінено,
  а підключення PostgreSQL заборонене.
- `test_get_wishlist_from_postgresql`: справжня PostgreSQL, перевірка `SELECT version()`,
  окрема UUID-схема, власник і wishlist, commit, очищення identity map,
  HTTP GET `/wishlists/{id}` та перевірка полів відповіді.
  Підміняється лише dependency сесії на справжню PostgreSQL-сесію.
  Цей публічний endpoint не використовує Redis-кеш чи авторизацію.
  У finally відновлюються dependency overrides і видаляється лише тестова схема.
- `test_real_redis`: справжній Redis повинен відповісти на ping.

Відсутня PostgreSQL або Redis спричиняє помилку, а не skip.
Не використовуйте SQLite як заміну інтеграційного тесту.

## Локальний запуск (PowerShell, Python 3.11)

Запустіть окремі тестові сервіси без портів існуючого Compose:

```powershell
docker run -d --name wishlist-ci-pg -e POSTGRES_USER=ci_user -e POSTGRES_PASSWORD=ci_password -e POSTGRES_DB=wishlist_test -p 55432:5432 postgres:15
docker run -d --name wishlist-ci-redis -p 56379:6379 redis:7
docker exec wishlist-ci-pg pg_isready -U ci_user -d wishlist_test
docker exec wishlist-ci-redis redis-cli ping
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-test.txt
python -m pip check
$env:DB_USER='ci_user'
$env:DB_PASSWORD='ci_password'
$env:DB_HOST='localhost:55432'
$env:DB_NAME='wishlist_test'
$env:DB_SSLMODE='disable'
$env:REDIS_URL='redis://localhost:56379/0'
$env:SECRET_KEY='ci-only-test-signing-key'
$env:ALGORITHM='HS256'
ruff check .
python -m pytest -v
python -c "import pathlib,yaml; yaml.load(pathlib.Path('.github/workflows/ci.yml').read_text(), Loader=yaml.BaseLoader); print('YAML OK')"
```

Виконуйте pytest після успішних відповідей `pg_isready` та `PONG`.
Для окремого health-тесту сервіси не потрібні:
`python -m pytest tests/test_health.py -v`.
Видаляйте лише створені вами тестові контейнери, не volumes та не дані існуючого Compose.

## Пояснення ci.yml для захисту

| Рядок / блок | Призначення |
| --- | --- |
| `name` | Назва workflow у вкладці Actions. |
| `on` | Перелік подій запуску. |
| `push`, `branches: [main]` | Push лише в main. |
| `pull_request`, `branches: [main]` | PR, цільовою гілкою якого є main. |
| `permissions`, `contents: read` | Токен має лише читання репозиторію. |
| `jobs` | Дві незалежні перевірки, без `needs`. |
| `lint` / `name` | Ідентифікатор і читабельна назва перевірки стилю. |
| `runs-on: ubuntu-24.04` | Фіксована версія ОС runner. |
| `timeout-minutes: 5` | Обмеження часу lint. |
| `steps` | Послідовні кроки job. |
| `actions/checkout@v4.2.2` | Отримання коду; конкретний release. |
| `actions/setup-python@v5.6.0` | Налаштування Python; конкретний release. |
| `with`, `python-version: '3.11'` | Параметри action, версія Python. |
| `cache: pip` | Відновлення кешу завантажених pip-пакетів. |
| `cache-dependency-path` | Хеш файлів залежностей бере участь у ключі кешу. |
| `Install Ruff`, `run` | Встановлення тільки зафіксованої версії Ruff. |
| `ruff check .` | Перевірка Python-коду без автоматичного виправлення у CI. |
| `tests` / `name` | Інтеграційний job. |
| `timeout-minutes: 10` | Обмеження часу job тестів. |
| `env` | Змінні середовища для всіх кроків тестового job. |
| `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Тестові облікові дані, узгоджені із PostgreSQL service. |
| `DB_HOST: localhost:5432` | Тести працюють на runner, порт контейнера опублікований на host. |
| `DB_SSLMODE: disable` | Локальний PostgreSQL без вимоги SSL. |
| `REDIS_URL` | Redis доступний через порт runner 6379. |
| `SECRET_KEY`, `ALGORITHM` | Лише тестова конфігурація JWT. |
| `services` | GitHub запускає контейнери перед кроками job. |
| `postgres`, `image: postgres:15` | PostgreSQL major 15. |
| `env: POSTGRES_*` | Створення тестового користувача та БД при старті контейнера. |
| `ports: 5432:5432` | Публікація порту контейнера на runner. |
| `options: >-` | YAML складає наступні рядки в один рядок Docker options. |
| `--health-cmd pg_isready ...` | Перевірка готовності PostgreSQL приймати з'єднання. |
| `--health-interval 5s` | Інтервал повторних перевірок. |
| `--health-timeout 5s` | Максимальний час однієї перевірки. |
| `--health-retries 12` | Після послідовних невдач service стає unhealthy і job не починає тести. |
| `redis`, `image: redis:7` | Redis major 7. |
| `ports: 6379:6379` | Порт Redis на runner. |
| `--health-cmd redis-cli ping` | Redis має відповісти PONG. Решта параметрів аналогічні PostgreSQL. |
| Checkout/setup-python у tests | Jobs мають окремі середовища, тому кроки повторюються. |
| Два `cache-dependency-path` | Ключ тестового кешу враховує API і тестові залежності; Ruff також зафіксований у test requirements. |
| `pip install -r requirements-test.txt` | Встановлення API та тестових залежностей із фіксованими версіями. Навіть при cache hit встановлення виконується. |
| `pip check` | Перевірка сумісності встановлених залежностей. |
| `python -m pytest -v` | Виконання всіх тестів після readiness services та встановлення залежностей. |

Кеш pip зберігає завантажені пакети, а не запущені сервіси чи БД.
Теги Docker 15/7 і minor Python 3.11 можуть отримувати patch-оновлення;
зафіксовані requirements забезпечують стабільні версії Python-пакетів.

## Гілка, коміт і Pull Request

Перегляньте `git diff` і `git status`, зокрема свої попередні зміни database.py/Compose.

```powershell
git switch -c lab4/github-actions-ci
git add .github/workflows/ci.yml tests docs pyproject.toml requirements-lint.txt requirements-test.txt main.py database.py crud.py schemas.py alembic/versions/b53f680d0719_create_initial_tables.py .env.example .gitignore docker-compose.yml
git diff --cached
git commit -m "Add Python API CI with PostgreSQL and Redis tests"
git push -u origin lab4/github-actions-ci
```

На GitHub створіть PR із цієї гілки до main. Дочекайтеся обох jobs.
Справжні скриншоти додайте у `docs/assets/` після запуску Actions.
Автоматичних commit/push під час виконання цієї роботи немає.

Офіційні джерела:
- https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers
- https://github.com/actions/setup-python

## Фактичні результати локальної перевірки (25.10.2026)

Перевірено у Docker, Python 3.11.17, PostgreSQL 15, Redis 7:

| Команда / перевірка | Результат |
| --- | --- |
| `python -m pip install -r requirements-test.txt` | Усі зафіксовані залежності встановлені. |
| `python -m pip check` | No broken requirements found. |
| `ruff check . --fix` | Видалено 6 невикористаних імпортів. |
| `ruff check .` | All checks passed! |
| `python -m pytest -v` | 4 passed, 10 warnings, 4.58s. |
| PyYAML BaseLoader + assertions | YAML валідний; тригери лише push/PR у main; permissions, runner, незалежність jobs, версії actions і health-check options перевірені. |
| `pg_isready -U ci_user -d wishlist_test` | accepting connections. |
| `redis-cli ping` | PONG. |
| `git diff --check` | Без помилок. |

Локальний Python на Windows — 3.13.5, тому залежності та тести запускалися
у потрібному Python 3.11 через Docker. `.venv-ci/` — локальне Linux-середовище
перевірки; воно виключене з Git і Ruff та не використовується GitHub Actions.
Контейнери запускалися в окремій мережі `wishlist-lab4-ci`, без host-портів,
з DB_HOST=postgres:5432 та REDIS_URL=redis://redis:6379/0. У CI процес працює
безпосередньо на runner і використовує localhost.

Створено: ci.yml, tests/conftest.py, tests/test_health.py, tests/test_database.py,
pyproject.toml, requirements-lint.txt, requirements-test.txt, docs/checks.md,
docs/assets/.gitkeep.
Змінено: database.py (керований sslmode), main.py (Redis TLS і виняток),
.env.example (ALGORITHM і DB_SSLMODE), .gitignore (локальні кеші).
У crud.py, schemas.py, main.py та початковій міграції прибрано невикористані імпорти.
Зміни docker-compose.yml були наявні до початку роботи; вони збережені.

Залишилися попередження deprecated API у SQLAlchemy, Pydantic, passlib та
httpx/Starlette. Вони не приховані й не спричиняють провал тестів.
GitHub Actions тут не запускався: його статус і скриншоти можна отримати
лише після вашого push/PR. Комітів і push не виконано; wishlist-ui не змінено.

Додаткова перевірка ізоляції: `python -m pytest tests/test_health.py -v`
у контейнері з `--network none`, DB_HOST=unreachable.invalid:5432:
**2 passed, 8 warnings, 3.92s**. Health-тест не потребує доступних PostgreSQL/Redis.
Після інтеграційного тесту запит до information_schema підтвердив:
кількість тимчасових схем `ci_*` дорівнює **0**.
Створені для перевірки контейнери wishlist-lab4-pg/wishlist-lab4-redis та їхня
окрема мережа видалені після тестів; volumes користувача не видалялися.
