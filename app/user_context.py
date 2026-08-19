from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass


@dataclass(frozen=True)
class UserContext:
    user_id: int
    storage_key: str
    username: str
    display_name: str


_CURRENT_USER: ContextVar[UserContext | None] = ContextVar("llm_learning_current_user", default=None)


def get_current_user() -> UserContext | None:
    return _CURRENT_USER.get()


def current_storage_key() -> str | None:
    user = get_current_user()
    return user.storage_key if user else None


def set_current_user(user: UserContext) -> Token:
    return _CURRENT_USER.set(user)


def reset_current_user(token: Token) -> None:
    _CURRENT_USER.reset(token)
