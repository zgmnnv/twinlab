# config/superset/superset_config.py
import os

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
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:////app/superset_home/superset.db")

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
# Logging Configuration
# -----------------------------------------------------------------------------
LOG_LEVEL = "INFO"
