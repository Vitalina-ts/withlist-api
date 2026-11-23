# Wishlist у Docker Compose

Для команд Docker Compose у цій інструкції потрібні файли з backend PR #4 і frontend PR #2. Розділ GHCR нижче описує незалежні збірки образів у GitHub Actions.

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

## Публікація Docker-образів у GHCR

GitHub Actions перевіряє код перед збіркою образів. Backend запускає Ruff і pytest з PostgreSQL та Redis. Frontend запускає ESLint, перевірку типів через `vue-tsc`, збірку Vite та HTTP-тест, який відкриває `/login` і завантажує JavaScript зі збірки.

- API — `ghcr.io/vitalina-ts/wishlist-api`, вихідний репозиторій — `Vitalina-ts/withlist-api`.
- UI — `ghcr.io/vitalina-ts/wishlist-ui`, вихідний репозиторій — `Vitalina-ts/wishlist-ui`.

| Подія | Результат після успішних перевірок |
|---|---|
| Pull request у `main` | Job `Docker build` збирає образ без входу в GHCR і без публікації. |
| Push у `main` | Job `Docker publish` публікує `main` і `sha-<повний SHA>`. |
| Push Git-тега `v1.0.0` | Job `Docker publish` публікує `1.0.0`, `1.0`, `1` і `latest`. |

Docker metadata action формує SemVer-теги та OCI labels, зокрема `org.opencontainers.image.source`. `latest` з'являється лише для стабільного версійного релізу. Некоректний Git-тег із префіксом `v` завершує публікаційний job помилкою за відсутності Docker-тегів. Workflow за замовчуванням має `contents: read`. Лише окремий job публікації отримує `packages: write` та входить у GHCR за допомогою автоматичного `GITHUB_TOKEN`.

### Обов'язкова перевірка для main

Обидва репозиторії публічні й підтримують branch rulesets. На момент перевірки активні rulesets [wishlist-api](https://github.com/Vitalina-ts/withlist-api/rules/25418282) і [wishlist-ui](https://github.com/Vitalina-ts/wishlist-ui/rules/25417443) застосовувалися до `main`, а список required checks був порожній.

1. Спочатку інтегруйте Docker PR backend #4 і frontend #2. Зіставте frontend PR #1 зі змінами GHCR, оскільки вони торкаються тих самих файлів CI та ESLint.
2. У кожному GHCR PR у вкладці **Checks** дочекайтеся успішного job **Docker build**. У списку перевірок PR він може відображатися з префіксом workflow **Python API CI** або **Frontend CI**.
3. У кожному власному репозиторії відкрийте **Settings → Rules → Rulesets**, відредагуйте чинний активний ruleset для `main` і відкрийте **Require status checks to pass**.
4. Натисніть **Add checks**, виберіть **Docker build**, джерело **GitHub Actions**, і збережіть. Збережіть також наявну вимогу щодо погодження PR. Перевірте, що job відображається як required у PR. [GitHub Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/creating-rulesets-for-a-repository)

### Реліз v1.0.0

Після злиття GHCR PR у кожному репозиторії відкрийте **Actions** і переконайтеся, що запуск для push у `main` успішний, включно з **Docker publish**. Скопіюйте повний SHA цього запуску. У PowerShell з відповідного каталогу перевірте, що саме цей SHA є на `origin/main` і містить GHCR workflow.

```powershell
$verifiedSha = Read-Host 'Повний SHA успішного запуску main'
git fetch origin main --tags
if ($LASTEXITCODE -ne 0) { throw 'Fetch failed' }
if ((git rev-parse origin/main) -ne $verifiedSha) { throw 'Verify the current main run first' }
if (-not (git show "${verifiedSha}:.github/workflows/ci.yml" | Select-String 'name: Docker publish')) { throw 'GHCR workflow missing' }
if (git tag --list v1.0.0) { throw 'Tag v1.0.0 already exists' }
git tag -a v1.0.0 $verifiedSha -m 'v1.0.0'
if ($LASTEXITCODE -ne 0) { throw 'Tag creation failed' }
git push origin refs/tags/v1.0.0
if ($LASTEXITCODE -ne 0) { throw 'Tag push failed' }
```

Дочекайтеся успішного **Docker publish** для `v1.0.0`, встановіть публічну видимість пакета та перевірте завантаження. Потім створіть GitHub Release для наявного тега в **Releases → Draft a new release → Choose a tag → v1.0.0 → Publish release**. Еквівалент із встановленим і авторизованим GitHub CLI з кожного каталогу:

```powershell
gh release create v1.0.0 --verify-tag --title v1.0.0 --generate-notes
```

### Публічність і перевірка завантаження

Після першої успішної публікації відкрийте профіль [Vitalina-ts → Packages](https://github.com/Vitalina-ts?tab=packages). Для `wishlist-api` і `wishlist-ui` відкрийте **Package settings → Danger Zone → Change visibility → Public** і підтвердьте назву пакета. На сторінці пакета перевірте позначку **Public** і список тегів. [GitHub Docs](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility)

PowerShell використовує окремий Docker-конфіг без доступу до збережених облікових даних. Обидві команди мають завершитися з кодом `0`.

```powershell
$anonymousConfig = Join-Path ([IO.Path]::GetTempPath()) ('wishlist-ghcr-' + [guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($anonymousConfig) | Out-Null
[IO.File]::WriteAllText((Join-Path $anonymousConfig 'config.json'), '{"auths":{"ghcr.io":{}}}')
docker --config $anonymousConfig pull ghcr.io/vitalina-ts/wishlist-api:1.0.0
docker --config $anonymousConfig pull ghcr.io/vitalina-ts/wishlist-ui:1.0.0
```

Місця для скриншотів після публікації:

- **API** — сторінка GitHub Packages із позначкою **Public** і тегами `1.0.0`, `1.0`, `1`, `latest`.
- **UI** — сторінка GitHub Packages із позначкою **Public** і тегами `1.0.0`, `1.0`, `1`, `latest`.

### Фактичні результати перевірки GHCR

- Локально зібрано обидва Docker-образи. Backend — Ruff та `pip check` пройшли, pytest — `4 passed` із PostgreSQL і Redis. Frontend — ESLint та збірка з перевіркою типів пройшли, HTTP-тест — `1 passed`.
- GitHub API повернув `404` для Git-тега `v1.0.0` в обох репозиторіях. Обидва анонімні `docker pull` для `:1.0.0` повернули `denied` і код `1`. Цей результат ще не підтверджує наявність чи видимість пакетів.
- Запуски змінених workflows на GitHub, застосування required check, релізи, публічна видимість і успішне анонімне завантаження очікують виконання на GitHub.
- `actionlint 1.7.12` перевірив обидва workflows. Локальний запуск закріпленого Docker metadata action з тестовими подіями підтвердив повний SHA та `main`, чотири теги для `v1.0.0`, лише `1.0.0-rc.1` для prerelease та правильні OCI source labels для обох репозиторіїв.
