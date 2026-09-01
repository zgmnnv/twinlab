"""Runtime configuration, read from the environment."""
import os

DATABASE_URL = os.environ.get(
    "TWIN_DATABASE_URL",
    "postgresql://twin:twin@postgres:5432/twin",
)

# Seed the demo twin (tincture production planning) on first start when the
# database is empty. Set to "false" to start with no twins.
SEED_DEMO = os.environ.get("TWIN_SEED_DEMO", "true").lower() == "true"

# CORS origins allowed to call the API (the flow-view SPA / Superset embed).
CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get("TWIN_CORS_ORIGINS", "*").split(",")
    if o.strip()
]
