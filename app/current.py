from __future__ import annotations

# Install data/model extensions before versioned route modules import exam_v2.
from . import bank_extension  # noqa: F401
from . import question_snapshot
from .main_v5 import app
from .data_management import router as data_management_router
from .diagnostics import router as diagnostics_router
from .hardening import install_security_headers
from .search import router as search_router

# Re-apply snapshot-aware function aliases after all versioned route modules are
# loaded so behavior is deterministic even when tests imported them earlier.
question_snapshot.install()

# Stable runtime entrypoint. Versioned modules remain as compatibility layers,
# while run.py and tests should target app.current:app from now on.
app.include_router(data_management_router)
app.include_router(diagnostics_router)
app.include_router(search_router)
install_security_headers(app)
