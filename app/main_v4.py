from __future__ import annotations

from .adaptive import router as adaptive_router
from .main_v3 import app

# V4 keeps all V3 timed-exam and coding-lab routes, then adds a derived adaptive
# mastery layer based on system-graded evidence. No manual mastery state is stored.
app.include_router(adaptive_router)
