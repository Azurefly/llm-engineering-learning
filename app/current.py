from __future__ import annotations

# Stable application composition. Versioned main_v*.py files remain only as
# backwards-compatible entrypoints; the supported runtime no longer chains them.
from . import adaptive_exposure
from . import bank_extension  # noqa: F401 - installs the expanded question bank
from . import code_challenges_v5  # noqa: F401 - fills coding labs for Week 2-18
from . import grading_v5
from . import question_snapshot
from . import adaptive_v5 as adaptive_v5_module
from . import code_exam as code_exam_module
from . import exam_system as exam_system_module
from . import exam_v2 as exam_v2_module
from . import exam_v3 as exam_v3_module
from .adaptive import router as adaptive_router
from .adaptive_v5 import router as adaptive_v5_router
from .auth import install_auth, router as auth_router
from .auto_backup import maybe_create_auto_backup
from .code_exam import router as code_exam_router
from .data_management import router as data_management_router
from .db import Database
from .diagnostics import router as diagnostics_router
from .exam_v2 import db, router as exam_v2_router
from .exam_v3 import router as exam_v3_router
from .hardening import install_security_headers
from .main import app
from .search import router as search_router

# Freeze question definitions regardless of module import order, harden rubric
# matching, and count CAT exposure only once after formal result materialization.
question_snapshot.install()
adaptive_exposure.install()
grading_v5.install()

# Ordering is intentional: V3 overrides compatible timed V2 paths, while the V2
# result/history routes remain available. All other feature routers are distinct.
app.include_router(auth_router)
app.include_router(exam_v3_router)
app.include_router(code_exam_router)
app.include_router(exam_v2_router)
app.include_router(adaptive_router)
app.include_router(adaptive_v5_router)
app.include_router(data_management_router)
app.include_router(diagnostics_router)
app.include_router(search_router)


def _initialize_current_user_database() -> None:
    """Create/upgrade every schema inside the authenticated user's own SQLite file."""
    Database(db.path)  # base progress/thought/resource tables
    exam_system_module.init_tables()
    exam_v2_module.init_tables()
    exam_v3_module.init_tables()
    code_exam_module.init_tables()
    adaptive_v5_module.init_tables()
    question_snapshot.init_tables()
    maybe_create_auto_backup(db)


install_security_headers(app)
install_auth(app, initializer=_initialize_current_user_database)
