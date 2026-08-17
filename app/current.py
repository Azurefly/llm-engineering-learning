from __future__ import annotations

# Stable application composition. Versioned main_v*.py files remain only as
# backwards-compatible entrypoints; the supported runtime no longer chains them.
from . import bank_extension  # noqa: F401 - installs the expanded question bank
from . import question_snapshot
from .adaptive import router as adaptive_router
from .adaptive_v5 import router as adaptive_v5_router
from .auto_backup import maybe_create_auto_backup
from .code_exam import router as code_exam_router
from .data_management import router as data_management_router
from .diagnostics import router as diagnostics_router
from .exam_v2 import db, router as exam_v2_router
from .exam_v3 import router as exam_v3_router
from .hardening import install_security_headers
from .main import app
from .search import router as search_router
from . import adaptive_exposure

# Freeze question definitions regardless of module import order and ensure CAT
# exposure is counted only once after a session becomes a formal exam attempt.
question_snapshot.install()
adaptive_exposure.install()

# Ordering is intentional: V3 overrides compatible timed V2 paths, while the V2
# result/history routes remain available. All other feature routers are distinct.
app.include_router(exam_v3_router)
app.include_router(code_exam_router)
app.include_router(exam_v2_router)
app.include_router(adaptive_router)
app.include_router(adaptive_v5_router)
app.include_router(data_management_router)
app.include_router(diagnostics_router)
app.include_router(search_router)

install_security_headers(app)
maybe_create_auto_backup(db)
