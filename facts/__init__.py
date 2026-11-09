"""لایه‌ی واقعیت: تبدیل داده خام (sources) به بسته‌های واقعیت JSON."""

from .build import (
    FactsUnavailable,
    build,
    build_fixtures,
    build_hat_tricks,
    build_reminder,
    build_recap,
    build_scorers,
    build_standings,
)

__all__ = [
    "FactsUnavailable",
    "build",
    "build_fixtures",
    "build_recap",
    "build_scorers",
    "build_standings",
    "build_hat_tricks",
    "build_reminder",
]
