from __future__ import annotations

from .data_management import router as data_management_router
from .main_v5 import app

# Stable runtime entrypoint. Versioned modules remain as compatibility layers,
# while run.py and tests should target app.current:app from now on.
app.include_router(data_management_router)
