# Legacy: OpenTwins on Kubernetes

These Helm values are the **previous** TwinLab architecture — the full
OpenTwins stack (Eclipse Ditto + Hono + Kafka + Mosquitto + Telegraf +
InfluxDB + Grafana + MongoDB + Superset + JupyterHub), ~25–35 pods.

It is kept for reference only. The lean stack in the repository root
(`docker-compose.yml` + `twin-service/`) replaces it for business-process
digital twins.

**Use this path only if you genuinely need:**

- device-scale IoT ingestion (thousands of things, MQTT/AMQP/LoRaWAN);
- multi-tenant twin management with Ditto policies;
- 3D scene visualisation (the OpenTwins Grafana + Unity panel).

If you just need to model a process, forecast, run what-if and show
2D dashboards — use the lean stack instead. See the root `README.md` and
`docs/architecture.md`.

## Install (unchanged)

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add eclipse-ditto https://eclipse-ditto.github.io/charts/
helm repo add ertis https://ertis-research.github.io/Helm-charts/
helm repo update

helm upgrade --install postgresql bitnami/postgresql -f values/postgresql.yaml
helm upgrade --install ditto eclipse-ditto/ditto       -f values/ditto.yaml
helm upgrade --install superset superset/superset      -f values/superset.yaml
helm upgrade --install opentwins ertis/opentwins       -f values/opentwins.yaml
```

> The Bitnami image references in `values/superset.yaml` point at
> `bitnamilegacy/*` repositories and will need updating — Bitnami moved the
> free catalogue. This is one of the reasons the lean stack exists.
