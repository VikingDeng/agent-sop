from __future__ import annotations

import json

from .api_models import UserResponse


def serialize_user(response: UserResponse) -> bytes:
    payload = {"id": response.id, "name": response.name}
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
