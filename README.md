# TwinLab

Лёгкий цифровой двойник **бизнес-процесса**: модель состояния + история +
расчёты (прогноз, план, what-if) + 2D-схема потока + дашборды.

Четыре контейнера, `docker compose up`, запускается на ноутбуке. Без Eclipse
Ditto, Hono, Kafka, MQTT, InfluxDB, Grafana, MongoDB и 3D.

> Предыдущая архитектура на OpenTwins (Kubernetes, ~25–35 подов) перенесена в
> [`deploy/legacy-opentwins-k8s/`](deploy/legacy-opentwins-k8s/) — она нужна
> только для device-scale IoT, мультитенантности Ditto или 3D-сцен.

> **Ветка `lean-version` — прототип в работе.** Что уже сделано и что осталось —
> в [`docs/lean-version-status.md`](docs/lean-version-status.md).

## Быстрый старт

```bash
cp .env.example .env
# отредактируйте пароли и SUPERSET_SECRET_KEY (openssl rand -hex 32)
docker compose up -d --build
```

| URL | Что |
|---|---|
| http://localhost:8080 | навигатор по сервисам |
| http://localhost:8080/flow.html | живая 2D-схема процесса |
| http://localhost:8080/analytics/ | Apache Superset (логин из `.env`) |
| http://localhost:8080/api/docs | OpenAPI twin-service |

При первом старте создаётся демо-двойник `tincture_ulun` (планирование
производства настойки) с загруженной историей и активным планом.

Опциональные профили:

```bash
docker compose --profile reports up -d      # Superset Alerts & Reports
docker compose --profile notebooks up -d    # Jupyter Lab на /jupyter/
```

## Что внутри

| Контейнер | Роль |
|---|---|
| **postgres** (TimescaleDB) | домен-модель двойника + временные ряды + KPI-агрегаты; отдельная БД для Superset |
| **twin-service** (FastAPI) | состояние двойника, расчёты, планы, what-if, события, WebSocket |
| **superset** | единственный BI-инструмент, читает Б-Д двойника напрямую |
| **gateway** (nginx) | единая точка входа :8080 |

Подробно — [`docs/architecture.md`](docs/architecture.md).

## Демо-сценарий

```bash
cd examples/tincture
python send_plan.py --activate                       # загрузить CSV + применить план
python send_plan.py --forecast-days 14 --weekend-factor 4   # what-if без применения
```

Схема на `/flow.html` обновится в реальном времени; узел «Склад продукции»
краснеет, когда остаток ниже страхового запаса.

## Разработка

```bash
# тесты бизнес-логики (без БД)
cd twin-service && pip install -r requirements.txt pytest && python -m pytest

# твин-сервис локально против запущенной БД
TWIN_DATABASE_URL=postgresql://twin:twin@localhost:5432/twin \
  uvicorn app.main:app --reload
```

## Структура

```
twinlab/
├── docker-compose.yml            # четыре сервиса + опц. профили
├── twin-service/                 # ядро двойника (FastAPI)
│   ├── app/
│   │   ├── main.py               # API + WebSocket
│   │   ├── store.py              # SQL
│   │   ├── calculations/         # чистые бизнес-функции (+ тесты)
│   │   ├── flow.py               # статусы узлов схемы
│   │   ├── ingest.py             # разбор CSV движения
│   │   └── schema.sql            # схема БД (Timescale)
│   └── seed/                     # демо-двойник tincture_ulun
├── webapp/
│   ├── index.html                # навигатор
│   └── flow.html                 # живая 2D-схема процесса
├── config/
│   ├── nginx/nginx.conf          # gateway
│   └── superset/superset_config.py
├── examples/tincture/            # демо-сценарий + данные
├── docs/architecture.md
└── deploy/legacy-opentwins-k8s/  # старый стек, для справки
```

## Безопасность

Конфигурация — для разработки. Для продакшена: сменить все пароли и
`SUPERSET_SECRET_KEY`, включить TLS на gateway, вынести секреты в менеджер
секретов, закрыть Postgres от внешней сети.
