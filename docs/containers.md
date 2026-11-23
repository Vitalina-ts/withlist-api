# Wishlist у Docker Compose

## Підготовка

Потрібні Git, запущений Docker Desktop у режимі Linux-контейнерів або Docker Engine із плагіном Compose v2 чи новішим, а також браузер. Python і Node.js встановлюються в образах під час збірки.

Клонуйте обидва репозиторії в один каталог на ревізіях, які містять цю конфігурацію. Для наявних копій перейдіть у `withlist-api` і перевірте, що `wishlist-ui` лежить поруч.

```powershell
git clone https://github.com/Vitalina-ts/withlist-api.git
git clone https://github.com/Vitalina-ts/wishlist-ui.git
cd withlist-api
```

Створіть `.env` із шаблону, якщо файл ще відсутній.

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

- `DB_USER` і `DB_NAME` задають користувача й назву PostgreSQL. Для нового стеку можна використати значення з шаблону.
- `DB_PASSWORD` і `SECRET_KEY` обов'язкові. Заповніть їх двома різними випадковими значеннями. Для секретів зі спеціальними символами використовуйте одинарні лапки в `.env`, щоб Compose читав значення буквально.
- `ALGORITHM` за замовчуванням має значення `HS256`. За потреби змініть порти хоста через `UI_PORT` і `API_PORT`.
- Compose задає API адреси `postgres` і `redis` у внутрішній мережі. Значення `DB_HOST`, `DB_SSLMODE` і `REDIS_URL` у шаблоні призначені для прямого запуску API на хості. Redis у цьому локальному стеку доступний контейнерам мережі й працює без окремого пароля.

PostgreSQL застосовує початкові облікові дані під час створення порожнього тому. Для зміни пароля у вже ініціалізованій базі оновіть пароль ролі в PostgreSQL та узгодьте його з `.env`.

## Запуск і керування

Виконуйте команди з `withlist-api`. Compose за замовчуванням вибирає `compose.yaml`. Попередній стек API доступний за явною командою `docker compose -f docker-compose.dev.yml up -d` і використовує свій попередній том. Для вже ініціалізованого тому задайте в `.env` чинний пароль його ролі PostgreSQL.

```powershell
docker compose -f compose.yaml up -d --build --wait
```

- UI — http://127.0.0.1:5173
- API та OpenAPI — http://127.0.0.1:8000/docs
- Health API — http://127.0.0.1:8000/health
- Той самий endpoint через Nginx UI — http://127.0.0.1:5173/api/health

```powershell
docker compose -f compose.yaml config --quiet
docker compose -f compose.yaml ps
docker compose -f compose.yaml logs -f
docker compose -f compose.yaml logs -f api ui
docker compose -f compose.yaml stop
docker compose -f compose.yaml down
```

`stop` зупиняє контейнери. `down` видаляє контейнери й мережу, але залишає іменований том PostgreSQL.

## Перевірка збереження даних

Створіть окремий Compose-проєкт із власним томом. Використовуйте лише це ім'я проєкту для команд із `down -v`. Приклад для PowerShell з `withlist-api` після заповнення `.env`.

```powershell
$testProject = 'wishlist-persistence-' + [guid]::NewGuid().ToString('N').Substring(0, 10)
$env:UI_PORT = '15173'
$env:API_PORT = '18000'
docker compose -f compose.yaml -p $testProject up -d --build --wait
```

Відкрийте http://127.0.0.1:15173, зареєструйте тестовий обліковий запис, увійдіть і створіть список. Відкрийте список і запам'ятайте ID з URL. У наступних командах підставте цей ID.

```powershell
$recordId = 1
$recordUrl = "http://127.0.0.1:15173/api/wishlists/$recordId"
Invoke-RestMethod $recordUrl
docker compose -f compose.yaml -p $testProject down
docker compose -f compose.yaml -p $testProject up -d --wait
Invoke-RestMethod $recordUrl
docker compose -f compose.yaml -p $testProject down -v
docker compose -f compose.yaml -p $testProject up -d --wait
curl.exe -i $recordUrl
docker compose -f compose.yaml -p $testProject down -v
Remove-Item Env:UI_PORT, Env:API_PORT
```

Після першого повторного запуску API має повернути той самий список. Після видалення тестового тому API має відповісти `404 Not Found`.

## Результати перевірки

Фрагменти фактичного виводу Docker Engine 29.2.1 і Compose v5.1.0. Перевірку виконано в окремому проєкті `wishlist-lab-check-1824b117bb`.

```text
config --quiet: exit 0
error while interpolating services.postgres.environment.POSTGRES_PASSWORD: required variable DB_PASSWORD is missing a value: Set DB_PASSWORD in .env
empty DB_PASSWORD: exit 1
unset DB_PASSWORD: exit 1
Image wishlist-lab-check-1824b117bb-api Built
Image wishlist-lab-check-1824b117bb-ui Built
GET /login: 200
GET /api/health: {"status":"healthy","redis":"healthy","timestamp":"2026-11-23T07:12:40.289866"}
postgres: healthy {}
redis: healthy {}
api: healthy {"8000/tcp":[{"HostIp":"127.0.0.1","HostPort":"18000"}]}
ui: healthy {"80/tcp":[{"HostIp":"127.0.0.1","HostPort":"15173"}]}
POST /api/wishlists: id=1
GET /api/wishlists/{id} after down: HTTP 200, title matches
Volume wishlist-lab-check-1824b117bb_postgres_data Removed
Volume wishlist-lab-check-1824b117bb_postgres_data Created
GET /api/wishlists/{id} after down -v: HTTP 404
```

Усі контейнери отримали статус `healthy`. Порожні прив'язки портів PostgreSQL і Redis підтверджують, що ці сервіси доступні всередині мережі Compose. Запис створено через Nginx і FastAPI. Звичайний `down` зберіг запис, а `down -v` видалив тестовий том із цим записом.

В окремому стеку запущено Edge у фоновому режимі. Браузер відобразив Vue-форму входу і виконав HTTP-запит із тієї самої адреси, з якої завантажив UI.

```text
Edge: Vue /login rendered; built API base /api; browser fetch /api/health HTTP 200
```
