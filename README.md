# TwinLab Development Environment

Проект перешел на использование **Helm** для развертывания в Kubernetes.

## 🏗️ Архитектура

Система построена на основе платформы OpenTwins и включает следующие компоненты:

### Поток данных:
1. **IoT устройства** отправляют данные через протоколы (MQTT, HTTP) в **HONO** (Protocol Adapter).
2. **HONO** нормализует данные и отправляет в **Message Queue** (Kafka/RabbitMQ).
3. **Jupyter** может интегрироваться с MQ для обработки данных.
4. **Message Queue** распределяет данные в **Eclipse Ditto** (для управления цифровыми двойниками) и **Telegraf** (для сбора метрик).
5. **Eclipse Ditto** хранит состояние в **MongoDB** и взаимодействует с **Grafana** для живых дашбордов.
6. **Telegraf** отправляет временные ряды в **InfluxDB**.
7. **InfluxDB** предоставляет данные для аналитики в **Superset**.
8. **Grafana** может обратно взаимодействовать с **Ditto** для обновления состояний.

## 📋 Компоненты и Сервисы

В состав среды входят следующие интегрированные компоненты:

### 1. OpenTwins
Основная платформа для управления цифровыми двойниками. Обеспечивает связность и управление жизненным циклом двойников.
- **Репозиторий**: [ertis-research/opentwins](https://github.com/ertis-research/opentwins)

### 2. Eclipse Ditto
Фреймворк для создания и управления цифровыми двойниками (Digital Twins). Предоставляет API для взаимодействия с устройствами как с цифровыми объектами.
- Хранит состояние цифровых двойников в **MongoDB**.
- Интегрируется с **Grafana** для живых дашбордов.

### 3. HONO (Eclipse Hono)
Протокол-адаптер для IoT устройств. Нормализует данные от различных протоколов (MQTT, HTTP, AMQP) и отправляет их в очередь сообщений.
- Обеспечивает безопасное и масштабируемое подключение IoT устройств.

### 4. Message Queue (Kafka / RabbitMQ)
Очередь сообщений для асинхронной обработки данных.
- Используется для маршрутизации данных между компонентами системы.

### 5. Telegraf
Коллектор метрик и данных временных рядов.
- Собирает данные из очередей и отправляет в базы данных временных рядов.

### 6. InfluxDB
База данных для временных рядов.
- Хранит телеметрию и метрики от IoT устройств для последующего анализа.

### 7. MongoDB
Документоориентированная база данных.
- Используется **Eclipse Ditto** для хранения состояния цифровых двойников.

### 8. Apache Superset
Мощная система бизнес-аналитики (BI) и визуализации данных.
- **Назначение**: Визуализация телеметрии и аналитика данных из **InfluxDB**.
- **Особенности**: Преднастроенные дашборды и подключение к источникам данных.

### 9. Grafana
Платформа для мониторинга и визуализации данных в реальном времени.
- **Назначение**: Живые дашборды для цифровых двойников из **Ditto**.
- Интегрируется с **MongoDB** и **InfluxDB**.

### 10. Jupyter Lab
Интерактивная среда разработки для Data Science.
- **Назначение**: Анализ данных, прототипирование ML-моделей и работа с данными OpenTwins через Python.
- **Особенности**: Предустановленные библиотеки для анализа данных. Может интегрироваться с **Message Queue**.

### 11. PostgreSQL
Надежная реляционная база данных.
- Используется как хранилище метаданных для **Superset** и других сервисов (не для Ditto).

## ☸️ Развертывание через Helm

Это **основной и рекомендуемый** способ развертывания. Все необходимые конфигурационные файлы находятся в директории `helm/`.

### Предварительные требования

Перед началом установки убедитесь, что:
- Установлен **Helm** (версия 3.x или выше).
- Установлен **kubectl** и настроен доступ к кластеру Kubernetes.
- Кластер имеет достаточные ресурсы (CPU, память) для развертывания всех компонентов.
- Установлены необходимые зависимости, такие как MongoDB, InfluxDB, Kafka/RabbitMQ (если не включены в чарты).

### Структура конфигурации

В папке `helm/values/` находятся файлы значений (`values.yaml`) для тонкой настройки каждого компонента при деплое:

*   `opentwins.yaml`: Специфичные настройки платформы OpenTwins.
*   `ditto.yaml`: Конфигурация Eclipse Ditto (подключения, полиси).
*   `superset.yaml`: Настройки Apache Superset (креденшиалы, инициализация).
*   `jupyter.yaml`: Настройки окружения Jupyter Lab.
*   `postgresql.yaml`: Параметры базы данных.

### Установка

Для развертывания стека используются отдельные официальные Helm-чарты для каждого компонента.

Сначала добавьте необходимые репозитории чартов:

```bash
# Добавление репозиториев
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add eclipse-ditto https://eclipse-ditto.github.io/charts/
helm repo add superset https://apache.github.io/superset/tree/master/helm/superset
helm repo add jupyterhub https://jupyterhub.github.io/helm-chart/
helm repo add ertis https://ertis-research.github.io/Helm-charts/

# Обновление репозиториев
helm repo update
```

Примеры команд установки для каждого компонента (используйте соответствующие values-файлы из `helm/values/`):

```bash
# PostgreSQL
helm upgrade --install postgresql bitnami/postgresql \
  -f helm/values/postgresql.yaml

# Eclipse Ditto
helm upgrade --install ditto eclipse-ditto/ditto \
  -f helm/values/ditto.yaml

# Apache Superset
helm upgrade --install superset superset/superset \
  -f helm/values/superset.yaml

# Jupyter Lab
helm upgrade --install jupyter jupyterhub/jupyterhub \
  -f helm/values/jupyter.yaml

# OpenTwins
helm upgrade --install opentwins ertis/opentwins \
  -f helm/values/opentwins.yaml
```

### Проверка развертывания

После установки проверьте статус подов:

```bash
kubectl get pods
```

Для доступа к сервисам используйте `kubectl port-forward` или настройте Ingress.

### Удаление

Для удаления компонентов:

```bash
helm uninstall superset
helm uninstall opentwins
# и т.д. для остальных
```
```
![schema](chema.png)

### Поток данных:
1. **IoT устройства** отправляют данные через протоколы (MQTT, HTTP) в **HONO** (Protocol Adapter).
2. **HONO** нормализует данные и отправляет в **Message Queue** (Kafka/RabbitMQ).
3. **Jupyter** может интегрироваться с MQ для обработки данных.
4. **Message Queue** распределяет данные в **Eclipse Ditto** (для управления цифровыми двойниками) и **Telegraf** (для сбора метрик).
5. **Eclipse Ditto** хранит состояние в **MongoDB** и взаимодействует с **Grafana** для живых дашбордов.
6. **Telegraf** отправляет временные ряды в **InfluxDB**.
7. **InfluxDB** предоставляет данные для аналитики в **Superset**.
8. **Grafana** может обратно взаимодействовать с **Ditto** для обновления состояний.

## 📋 Компоненты и Сервисы

В состав среды входят следующие интегрированные компоненты:

### 1. OpenTwins
Основная платформа для управления цифровыми двойниками. Обеспечивает связность и управление жизненным циклом двойников.
- **Репозиторий**: [ertis-research/opentwins](https://github.com/ertis-research/opentwins)

### 2. Eclipse Ditto
Фреймворк для создания и управления цифровыми двойниками (Digital Twins). Предоставляет API для взаимодействия с устройствами как с цифровыми объектами.
- Хранит состояние цифровых двойников в **MongoDB**.
- Интегрируется с **Grafana** для живых дашбордов.

### 3. HONO (Eclipse Hono)
Протокол-адаптер для IoT устройств. Нормализует данные от различных протоколов (MQTT, HTTP, AMQP) и отправляет их в очередь сообщений.
- Обеспечивает безопасное и масштабируемое подключение IoT устройств.

### 4. Message Queue (Kafka / RabbitMQ)
Очередь сообщений для асинхронной обработки данных.
- Используется для маршрутизации данных между компонентами системы.

### 5. Telegraf
Коллектор метрик и данных временных рядов.
- Собирает данные из очередей и отправляет в базы данных временных рядов.

### 6. InfluxDB
База данных для временных рядов.
- Хранит телеметрию и метрики от IoT устройств для последующего анализа.

### 7. MongoDB
Документоориентированная база данных.
- Используется **Eclipse Ditto** для хранения состояния цифровых двойников.

### 8. Apache Superset
Мощная система бизнес-аналитики (BI) и визуализации данных.
- **Назначение**: Визуализация телеметрии и аналитика данных из **InfluxDB**.
- **Особенности**: Преднастроенные дашборды и подключение к источникам данных.

### 9. Grafana
Платформа для мониторинга и визуализации данных в реальном времени.
- **Назначение**: Живые дашборды для цифровых двойников из **Ditto**.
- Интегрируется с **MongoDB** и **InfluxDB**.

### 10. Jupyter Lab
Интерактивная среда разработки для Data Science.
- **Назначение**: Анализ данных, прототипирование ML-моделей и работа с данными OpenTwins через Python.
- **Особенности**: Предустановленные библиотеки для анализа данных. Может интегрироваться с **Message Queue**.

### 11. PostgreSQL
Надежная реляционная база данных.
- Используется как хранилище метаданных для **Superset** и других сервисов (не для Ditto).

## ☸️ Развертывание через Helm

Это **основной и рекомендуемый** способ развертывания. Все необходимые конфигурационные файлы находятся в директории `helm/`.

### Структура конфигурации

В папке `helm/values/` находятся файлы значений (`values.yaml`) для тонкой настройки каждого компонента при деплое:

*   `opentwins.yaml`: Специфичные настройки платформы OpenTwins.
*   `ditto.yaml`: Конфигурация Eclipse Ditto (подключения, полиси).
*   `superset.yaml`: Настройки Apache Superset (креденшиалы, инициализация).
*   `jupyter.yaml`: Настройки окружения Jupyter Lab.
*   `postgresql.yaml`: Параметры базы данных.

### Установка

Для развертывания стека используются отдельные официальные Helm-чарты для каждого компонента. Убедитесь, что у вас настроен доступ к кластеру Kubernetes и установлен Helm.

Примеры команд установки для каждого компонента (используйте соответствующие values-файлы из `helm/values/`):

```bash
# PostgreSQL
helm upgrade --install postgresql bitnami/postgresql \
  -f helm/values/postgresql.yaml

# Eclipse Ditto
helm upgrade --install ditto eclipse-ditto/ditto \
  -f helm/values/ditto.yaml

# Apache Superset
helm upgrade --install superset apache/superset \
  -f helm/values/superset.yaml

# Jupyter Lab
helm upgrade --install jupyter jupyterhub/jupyterhub \
  -f helm/values/jupyter.yaml

# OpenTwins (предполагается пользовательский чарт)
helm upgrade --install opentwins <репозиторий-opentwins> \
  -f helm/values/opentwins.yaml
```

**Примечание:** Для OpenTwins укажите актуальный репозиторий чарта. Убедитесь, что все зависимости (например, MongoDB, InfluxDB, Kafka) развернуты отдельно или включены в чарты.

## 📁 Структура Проекта

```
twinlab/
├── docker-compose.yml          # Main orchestration
├── .env                        # Environment variables
├── setup.sh                    # Quick setup script
├── config/
│   └── superset/superset_config.py
├── docker/
│   ├── superset/Dockerfile.superset
│   ├── jupyter/Dockerfile.jupyter
│   └── webapp/Dockerfile.webapp
├── webapp/
│   └── index.html              # Homepage
└── notebooks/                  # Jupyter notebooks
```

## 🔒 Безопасность

Данная конфигурация предназначена **только для разработки (Development)**.

Для использования в продакшене (Production):
1.  **Смените все пароли**: В файлах конфигурации используются стандартные пароли (например, `admin`/`admin`).
2.  **Настройте HTTPS**: Используйте Ingress с TLS сертификатами.
3.  **Управление секретами**: Не храните пароли в открытом виде в values-файлах, используйте Kubernetes Secrets или внешние хранилища секретов.
4.  **Network Policies**: Ограничьте сетевой доступ между сервисами.
