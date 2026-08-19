import os

# Existing application tests focus on learning/exam behavior rather than login.
# Authentication itself is tested separately in test_auth.py.
os.environ.setdefault("LLM_AUTH_TEST_BYPASS", "1")
