"""Superset configuration for the TwinLab lean stack.

Superset is the only BI / dashboard tool here. It reads the twin database
(PostgreSQL + TimescaleDB) directly. Redis + Celery are optional and only
wired up when REDIS_URL is set (docker compose --profile reports).
"""
import os

# --- core -----------------------------------------------------------------
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "CHANGE_ME_32_CHARS_MINIMUM")

SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://twin:twin@postgres:5432/superset",
)
SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}

# Development stack served over plain HTTP behind the nginx gateway.
PREFERRED_URL_SCHEME = "http"
ENABLE_PROXY_FIX = True
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Lax"
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None
TALISMAN_ENABLED = False

# --- feature flags ------------------------------------------------------
FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
    "DASHBOARD_RBAC": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "ALERT_REPORTS": True,
}
CACHE_DEFAULT_TIMEOUT = 300

# --- caching / async: Redis when available, in-memory otherwise ----------
_redis_url = os.environ.get("REDIS_URL", "").strip()
if _redis_url:
    CACHE_CONFIG = {
        "CACHE_TYPE": "RedisCache",
        "CACHE_DEFAULT_TIMEOUT": 300,
        "CACHE_KEY_PREFIX": "superset_",
        "CACHE_REDIS_URL": _redis_url,
    }
    DATA_CACHE_CONFIG = CACHE_CONFIG

    class CeleryConfig:
        broker_url = _redis_url
        result_backend = _redis_url
        task_serializer = "json"
        accept_content = ["json"]
        result_serializer = "json"
        worker_prefetch_multiplier = 1
        task_acks_late = True
        beat_schedule = {
            "reports.scheduler": {
                "task": "reports.scheduler",
                "schedule": 60.0,
            },
            "reports.prune_log": {
                "task": "reports.prune_log",
                "schedule": 3600.0,
            },
        }

    CELERY_CONFIG = CeleryConfig
else:
    CACHE_CONFIG = {"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 300}
    DATA_CACHE_CONFIG = CACHE_CONFIG

# --- Alerts & Reports: text-only, no headless browser -------------------
ALERT_REPORTS_NOTIFICATION_DRY_RUN = os.environ.get("ALERT_REPORTS_DRY_RUN", "false").lower() == "true"
ALERT_REPORTS_EXECUTE_AS = ["owner"]
REPORTS_CONFIG = {"report_format": "TEXT"}

SMTP_HOST = os.environ.get("SMTP_HOST", "mailhog")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "1025"))
SMTP_STARTTLS = os.environ.get("SMTP_STARTTLS", "false").lower() == "true"
SMTP_SSL = os.environ.get("SMTP_SSL", "false").lower() == "true"
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_MAIL_FROM = os.environ.get("SMTP_MAIL_FROM", "twinlab@localhost")
WEBDRIVER_BASEURL = "http://superset:8088/"
WEBDRIVER_BASEURL_USER_FRIENDLY = os.environ.get(
    "SUPERSET_PUBLIC_URL", "http://localhost:8080/analytics/"
)

LOG_LEVEL = os.environ.get("SUPERSET_LOG_LEVEL", "INFO")
