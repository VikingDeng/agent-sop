from __future__ import annotations

import unittest

from src.api_models import UserResponse, user_from_mapping
from src.serializer import serialize_user


class UserResponseTests(unittest.TestCase):
    def test_existing_response_bytes_are_stable(self) -> None:
        response = UserResponse(id=7, name="Ada")
        self.assertEqual(serialize_user(response), b'{"id":7,"name":"Ada"}')

    def test_unknown_storage_fields_are_ignored(self) -> None:
        response = user_from_mapping({"id": "8", "name": "Grace", "internal_rank": 99})
        self.assertEqual(response, UserResponse(id=8, name="Grace"))


if __name__ == "__main__":
    unittest.main()
