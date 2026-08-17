from __future__ import annotations

from .adaptive_v5 import router as adaptive_v5_router
from .main_v4 import app

# V5 adds sequential computerized adaptive testing on top of the V4 mastery layer.
# Existing weekly, stage, timed and coding assessments remain compatible.
app.include_router(adaptive_v5_router)
