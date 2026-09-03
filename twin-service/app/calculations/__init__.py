"""Registry of business-process calculators, keyed by twin.kind."""
from .production import plan_production

CALCULATORS = {
    "production_planning": plan_production,
}


def get_calculator(kind: str):
    """Return the calculator for a twin kind, or None if unknown."""
    return CALCULATORS.get(kind)


__all__ = ["plan_production", "get_calculator", "CALCULATORS"]
