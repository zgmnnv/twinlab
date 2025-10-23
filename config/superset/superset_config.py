# config/superset/superset_config.py
import os
import json
from datetime import datetime, date

# -----------------------------------------------------------------------------
# Secret Key
# -----------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "CHANGE_ME")

# -----------------------------------------------------------------------------
# JWT Secret Key for async queries
# -----------------------------------------------------------------------------
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "CHANGE_ME")

# -----------------------------------------------------------------------------
# Force HTTP for development (disable HTTPS redirects)
# -----------------------------------------------------------------------------
PREFERRED_URL_SCHEME = "http"

# -----------------------------------------------------------------------------
# Disable HTTPS redirects completely
# -----------------------------------------------------------------------------
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# -----------------------------------------------------------------------------
# Session and Cookie Configuration
# -----------------------------------------------------------------------------
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------
# Use PostgreSQL instead of SQLite
POSTGRES_DB = os.environ.get("POSTGRES_DB", "superset")
POSTGRES_USER = os.environ.get("POSTGRES_USER", "superset")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "superset")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")

SQLALCHEMY_DATABASE_URI = os.environ.get(
    "DATABASE_URL", 
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# PostgreSQL engine options
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "pool_size": 10,
    "max_overflow": 20,
}

# Custom JSON encoder for datetime handling
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

# Set custom JSON encoder
JSON_AS_ASCII = False
JSON_SORT_KEYS = True

# -----------------------------------------------------------------------------
# Feature flags
# -----------------------------------------------------------------------------
FEATURE_FLAGS = {
    # Asynchronous queries disabled in prod unless needed
    "GLOBAL_ASYNC_QUERIES": False,

    # Enable embedded Superset for iframe integration
    "EMBEDDED_SUPERSET": True,

    # Enable dashboard native filters & cross-filtering
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,

    # Role-based access control for dashboards
    "DASHBOARD_RBAC": True,

    # Enable Jinja/SQL template processing
    "ENABLE_TEMPLATE_PROCESSING": True,

    # CSRF protection for Explore JSON API
    "ENABLE_EXPLORE_JSON_CSRF_PROTECTION": True,

    # **Important**: allow CSV/file uploads to default database
    "ALLOW_FILE_UPLOAD": True,

    # Optional: enable verbose logging for production troubleshooting
    "ENABLE_EXPLORE_LOGGING": True,

    # Optional: enable caching for faster dashboards
    "CACHE_DEFAULT_TIMEOUT": 300,

    # Optional: enable row-level security
    "ENABLE_ROW_LEVEL_SECURITY": True,
    # Warning this is only for dev purposes never
    "ENABLE_DATASET_SOURCE_PREVIEW": True,
    "ALERT_REPORTS": True, 
}


# -----------------------------------------------------------------------------
# Security Configuration - Disable HTTPS enforcement
# -----------------------------------------------------------------------------
TALISMAN_CONFIG = {
    "force_https": False,
    "force_https_permanent": False,
    "content_security_policy": {
        "base-uri": ["'self'"],
        "default-src": ["'self'"],
        "img-src": ["'self'", "data:", "blob:"],
        "worker-src": ["'self'", "blob:"],
        "connect-src": [
            "'self'",
            "https://api.mapbox.com",
            "https://events.mapbox.com",
        ],
        "script-src": ["'self'", "'strict-dynamic'", "'unsafe-inline'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "object-src": "'none'",
    },
    "content_security_policy_nonce_in": ["script-src"],
}

# -----------------------------------------------------------------------------
# CORS Configuration
# -----------------------------------------------------------------------------
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# -----------------------------------------------------------------------------
# Cache Configuration
# -----------------------------------------------------------------------------
CACHE_CONFIG = {
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
}

# -----------------------------------------------------------------------------
# Celery Configuration for Alerts & Reports
# -----------------------------------------------------------------------------
class CeleryConfig:
    broker_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
    result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
    task_serializer = "json"
    accept_content = ["json"]
    result_serializer = "json"
    timezone = "UTC"
    enable_utc = True
    task_track_started = True
    task_time_limit = 30 * 60  # 30 minutes
    task_soft_time_limit = 25 * 60  # 25 minutes
    worker_prefetch_multiplier = 1
    task_acks_late = True
    
    # Beat schedule for alerts and reports
    beat_schedule = {
        'reports.scheduler': {
            'task': 'reports.scheduler',
            'schedule': 60.0,  # Run every 60 seconds
        },
        'reports.prune_log': {
            'task': 'reports.prune_log',
            'schedule': 3600.0,  # Run every hour
        },
    }

CELERY_CONFIG = CeleryConfig

# -----------------------------------------------------------------------------
# Email Configuration for Alerts & Reports
# -----------------------------------------------------------------------------
SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_STARTTLS = os.environ.get("SMTP_STARTTLS", "true").lower() == "true"
SMTP_SSL = os.environ.get("SMTP_SSL", "false").lower() == "true"
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_MAIL_FROM = os.environ.get("SMTP_MAIL_FROM", "noreply@superset.com")

# Email configuration for Superset
EMAIL_NOTIFICATIONS = True
SMTP_MAIL_SERVER = SMTP_HOST
SMTP_MAIL_PORT = SMTP_PORT
SMTP_MAIL_USE_TLS = SMTP_STARTTLS
SMTP_MAIL_USE_SSL = SMTP_SSL
SMTP_MAIL_USERNAME = SMTP_USER
SMTP_MAIL_PASSWORD = SMTP_PASSWORD
SMTP_MAIL_DEFAULT_SENDER = SMTP_MAIL_FROM

# -----------------------------------------------------------------------------
# Alerts & Reports Configuration
# -----------------------------------------------------------------------------
# Disable PDF generation - just send dashboard links
ALERT_REPORTS_NOTIFICATION_DRY_RUN = False

# Dashboard URL configuration for alerts
ALERT_REPORTS_WEBDRIVER_BASEURL = "http://superset:8088"
ALERT_REPORTS_WEBDRIVER_BASEURL_USER_FRIENDLY = "http://localhost:8088"



# Override the base URL for dashboard links in emails
import os
os.environ['WEBDRIVER_BASEURL_USER_FRIENDLY'] = "http://localhost:8088"
os.environ['ALERT_REPORTS_WEBDRIVER_BASEURL_USER_FRIENDLY'] = "http://localhost:8088"

# Force the correct URL format for dashboard links
SUPERSET_WEBSERVER_PROTOCOL = "http"
SUPERSET_WEBSERVER_ADDRESS = "0.0.0.0"
SUPERSET_WEBSERVER_PORT = 8088

# Override the default webdriver configuration
WEBDRIVER_BASEURL = "http://superset:8088"
WEBDRIVER_BASEURL_USER_FRIENDLY = "http://localhost:8088"

# Force the correct URL in Flask app configuration
import os
os.environ['SUPERSET_WEBSERVER_PROTOCOL'] = "http"
os.environ['SUPERSET_WEBSERVER_ADDRESS'] = "0.0.0.0"
os.environ['SUPERSET_WEBSERVER_PORT'] = "8088"

# Disable screenshot generation - send only text with dashboard links
ALERT_REPORTS_ENABLE_SCREENSHOTS = False
REPORTS_CONFIG = {
    'report_format': 'TEXT',
}

# Custom email templates for alerts
ALERT_REPORTS_EMAIL_TEMPLATE = """
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .content { margin: 20px 0; }
        .dashboard-link { 
            display: inline-block; 
            background-color: #007bff; 
            color: white; 
            padding: 10px 20px; 
            text-decoration: none; 
            border-radius: 5px; 
            margin: 10px 0;
        }
        .dashboard-link:hover { background-color: #0056b3; }
        .footer { margin-top: 30px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h2>🚨 Alert Notification</h2>
        <p>Hello! This is an automated alert from your Superset dashboard.</p>
    </div>
    
    <div class="content">
        <p><strong>Alert Name:</strong> {alert_name}</p>
        <p><strong>Triggered at:</strong> {triggered_at}</p>
        <p><strong>Message:</strong> {alert_message}</p>
        
        <p>Click the link below to view your dashboard:</p>
        <a href="http://localhost:8088{dashboard_path}" class="dashboard-link">📊 View Dashboard in Superset</a>
    </div>
    
    <div class="footer">
        <p>This is an automated message from Superset. Please do not reply to this email.</p>
    </div>
</body>
</html>
"""

# Also try setting the template via environment variable
os.environ['ALERT_REPORTS_EMAIL_TEMPLATE'] = ALERT_REPORTS_EMAIL_TEMPLATE

# Log retention settings (fixes the error you encountered)
LOG_RETENTION = 30  # Keep logs for 30 days
ALERT_REPORTS_LOG_RETENTION = 30  # Keep alert/report logs for 30 days

# WebDriver disabled - using dashboard links only
WEBDRIVER_TYPE = "chrome"

# -----------------------------------------------------------------------------
# Alerts & Reports Executor Configuration
# -----------------------------------------------------------------------------
ALERT_REPORTS_EXECUTE_AS = ["self"]

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
LOG_LEVEL = "INFO"
