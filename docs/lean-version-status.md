# Ветка `lean-version` — статус

Первый сырой прототип плана A: максимально облегчённый цифровой двойник
бизнес-процесса. Отходим от OpenTwins/Ditto/Hono/Kafka и 3D — к схеме
`PostgreSQL + twin-service + Superset + 2D-схема потока`.

## Сделано

### Архитектура и развёртывание
- `docker-compose.yml` — 4 сервиса вместо ~30 подов:
  `postgres` (TimescaleDB) · `twin-service` (FastAPI) · `superset` · `gateway` (nginx).
- Опциональные профили: `--profile reports` (Redis + Celery + MailHog для
  Superset Alerts & Reports), `--profile notebooks` (Jupyter Lab).
- Единая точка входа — `http://localhost:8080` (nginx проксирует
  `/api`, `/analytics`, `/jupyter`, отдаёт `webapp/`).
- Старый стек OpenTwins на Kubernetes перенесён в
  `deploy/legacy-opentwins-k8s/` (только для справки).
- **Проверено локально:** `docker compose up --build` поднимает весь стек,
  все контейнеры healthy, Superset отвечает на `/analytics/health`.

### twin-service (ядро двойника)
- FastAPI + asyncpg, схема БД применяется на старте (`app/schema.sql`).
- Модель данных: `twin`, `twin_state_history`, `measurement` (hypertable),
  `measurement_daily` (continuous aggregate для Superset), `plan`, `event`.
- REST + WebSocket API: `/api/twins`, `/state`, `/history`, `/ingest`,
  `/measurements`, `/plan` (+ what-if), `/flow`, `/ws`.
- Бизнес-логика планирования производства перенесена из старого
  `ProductionCalculator` в `app/calculations/production.py` — чистые функции,
  покрыты юнит-тестами (`tests/test_production.py`, проходят без БД).
- Разбор CSV движения товара (был `TableManager`) → `app/ingest.py`,
  конфигурируемый маппинг колонок.
- Демо-двойник `tincture_ulun` создаётся автоматически при первом старте
  (`app/seed.py` + `seed/`).
- **Проверено:** демо-двойник поднимается, `/flow` отдаёт узлы со статусами,
  правило «остаток < страхового запаса» корректно красит узел «Склад
  продукции».

### 2D-визуализация потока
- `webapp/flow.html` — живая SVG-схема процесса: узлы красятся по статусу
  (ok/warn/low), рёбра показывают поток с 2D-анимацией (бегущий пунктир +
  точка), панель «Активный план», форма «Что если» с предпросмотром.
- Обновление через WebSocket + fallback-поллинг.
- `webapp/index.html` — навигатор по сервисам, вычищен (убран телефон,
  хардкод-креды вынесены в подпись).
- **Проверено в браузере:** схема рендерится, статусы цветные, форма
  «Что если» пересчитывает план (пик-фактор 3→6 поднимает требуемое
  производство 6→14), WebSocket «в реальном времени» подключается.

### Чистка
- `superset_config.py` переписан: убраны дубли (`import os` ×2,
  `WTF_CSRF` ×2), `CACHE_DEFAULT_TIMEOUT` вынесен из `FEATURE_FLAGS`;
  Redis/Celery подключаются только при заданном `REDIS_URL`.
- `Dockerfile.superset` — убраны Chrome + ChromeDriver + Playwright/Chromium
  (~250 МБ); Alerts & Reports работают в TEXT-режиме.
- Superset запускается на `gthread`-воркерах (в базовом образе нет gevent).
- `Dockerfile.jupyter` — поддерживаемый базовый образ `scipy-notebook`,
  один env вместо двух собираемых venv.
- `.env.example` без реальных секретов; `.gitlab-ci.yml` — реальный
  pipeline (тесты + `compose config` + build) вместо пустого шаблона.
- Удалён устаревший `schema.png` (источник — mermaid в `docs/architecture.md`).

## Надо сделать

### Ближайшее
- [ ] **What-if не должен плодить строки `plan`.** Исправлено в коде
  (`POST /plan` без `?activate=true` теперь только считает, не пишет) —
  нужно пересобрать образ и перепроверить на чистой БД (`docker compose
  down -v && up`).
- [ ] Прогнать `examples/tincture/send_plan.py` против живого стека
  (клиент готов, end-to-end ещё не гонял).
- [ ] Эталонный дашборд Superset поверх БД `twin` (шаг 6 плана): временные
  ряды `stock`/`outflow`, KPI-плитки из активного плана, таблица истории
  планов. Сейчас регистрируется только подключение к БД.
- [ ] Проверить Superset под префиксом `/analytics/` целиком (логин,
  статика, Explore) — базовый `/health` отвечает, полный UI не гонял.
- [ ] `notebooks/test.ipynb` ссылается на несуществующий kernel
  `data_analysis` → переkey на `python3`.

### Двойник
- [ ] Диспетчеризация расчётов по `twin.kind` в обработчике `/plan`
  (сейчас всегда `plan_production`).
- [ ] Планировщик: периодический пересчёт активного плана при новых данных
  (сейчас только по запросу).
- [ ] Правила/алерты: событие при расхождении план/факт больше порога
  (сейчас есть только подсветка узла).
- [ ] Аутентификация на `twin-service` (сейчас открыт, ок только для лабы).
- [ ] Пагинация/ретенция для `event` и `twin_state_history`.

### Инфраструктура
- [ ] Healthcheck и `depends_on: condition: service_healthy` для
  `twin-service` в compose (образ healthcheck есть, в compose не связан).
- [ ] Alembic вместо применения `schema.sql` на старте — когда схема
  начнёт меняться.
- [ ] Прод-профиль: TLS на gateway, секреты, закрыть порт Postgres.
- [ ] Обновить `deploy/legacy-opentwins-k8s/values/superset.yaml`
  (ссылки на `bitnamilegacy/*`) либо удалить legacy-путь совсем.

## Как запустить

```bash
cp .env.example .env      # заменить пароли и SUPERSET_SECRET_KEY
docker compose up -d --build
open http://localhost:8080/flow.html
```

Тесты бизнес-логики:

```bash
cd twin-service && pip install -r requirements.txt pytest && python -m pytest
```
