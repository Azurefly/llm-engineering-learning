from __future__ import annotations

# Install data/model extensions before versioned route modules import exam_v2
# functions by name. This keeps new attempts reproducible and expands the bank.
from . import bank_extension  # noqa: F401
from . import question_snapshot  # noqa: F401
from .main_v5 import app
from .data_management import router as data_management_router
from .search import router as search_router

# Stable runtime entrypoint. Versioned modules remain as compatibility layers,
# while run.py and tests should target app.current:app from now on.
app.include_router(data_management_router)
app.include_router(search_router)
