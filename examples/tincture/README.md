# Пример: планирование производства настойки «Груша-улун»

Показывает, как цифровой двойник бизнес-процесса работает в TwinLab:
загрузка движения товара → расчёт плана производства и потребности в сырье →
живая 2D-схема процесса.

## Что изменилось по сравнению со старой версией

| Раньше (отдельная программа) | Теперь |
|---|---|
| `TableManager` — чистил CSV в файл | `POST /api/twins/{id}/ingest` |
| `ProductionCalculator` — считал в скрипте | `app/calculations/production.py` в `twin-service`, вызывается через `POST /api/twins/{id}/plan` |
| `DigitalTwinPublisher` — слал в Eclipse Ditto по MQTT | `twin-service` пишет состояние сам; MQTT/Ditto/Hono/Kafka больше не нужны |
| `VisualizationDashboard` — свой дашборд на Dash | 2D-схема `webapp/flow.html` + графики в Superset |

Вся бизнес-логика (формулы прогноза, страховой запас, объём партии, рецептура)
сохранена в `twin-service/app/calculations/production.py` и покрыта тестами
`twin-service/tests/test_production.py`.

## Запуск

Демо-двойник `tincture_ulun` уже создаётся автоматически при первом старте
(`TWIN_SEED_DEMO=true`). Чтобы прогнать сценарий вручную:

```bash
cd examples/tincture
python send_plan.py --activate
# what-if: тот же расчёт с другим горизонтом, без применения
python send_plan.py --forecast-days 14 --weekend-factor 4
```

Затем откройте `http://localhost:8080/flow.html` — схема процесса обновится
в реальном времени.

## Данные

`table/product_movement_data.csv` — выгрузка движения товара (мл): дата,
регламент, приход, расход, остаток. Строка без даты (начальный остаток)
пропускается при импорте.
