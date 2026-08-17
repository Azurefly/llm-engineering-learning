from __future__ import annotations

from .exam_v2 import router as exam_v2_router
from .main import app

app.include_router(exam_v2_router)
