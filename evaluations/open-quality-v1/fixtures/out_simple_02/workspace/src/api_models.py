from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class UserResponse:
    id: int
    name: str


def user_from_mapping(payload: Mapping[str, Any]) -> UserResponse:
    """Build a public response while ignoring unknown storage fields."""
    return UserResponse(id=int(payload["id"]), name=str(payload["name"]))
