from __future__ import annotations

from .code_exam import router as code_exam_router
from .exam_v2 import router as exam_v2_router
from .exam_v3 import router as exam_v3_router
from .main import app

# V3 routes are registered before V2 so compatible paths such as
# /exams/{week}/random-start and /exam-v2/attempt/{id} gain server-enforced
# deadlines/autosave while the V2 result/history routes remain reusable.
app.include_router(exam_v3_router)
app.include_router(code_exam_router)
app.include_router(exam_v2_router)
