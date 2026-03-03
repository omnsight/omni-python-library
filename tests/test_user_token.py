from unittest.mock import patch

import pytest
from fastapi import HTTPException

from omni_python_library.middleware.user_token import (
    get_current_user,
    get_owner_from_token,
    get_user_context,
    get_user_roles,
    validate_create_permission,
)

# A sample JWT payload
SAMPLE_PAYLOAD = {
    "sub": "user123",
    "roles": ["user", "pro"],
    "exp": 2609459200,  # Some time in the future
}

# A sample encoded JWT token (header.payload.signature) - signature is not verified
# You can generate one from jwt.io
SAMPLE_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwicm9sZXMiOlsidXNlciIsInBybyJdLCJleHAiOjI2MDk0NTkyMDB9.fake_signature"


@pytest.mark.asyncio
class TestUserTokenMiddleware:
    async def test_get_current_user_success(self):
        with patch("jwt.decode", return_value=SAMPLE_PAYLOAD) as mock_decode:
            payload = await get_current_user(f"Bearer {SAMPLE_TOKEN}")
            assert payload == SAMPLE_PAYLOAD
            mock_decode.assert_called_once_with(SAMPLE_TOKEN, options={"verify_signature": False})

    async def test_get_current_user_no_header(self):
        with pytest.raises(HTTPException, match="Authorization header missing") as e:
            await get_current_user(None)
        assert e.value.status_code == 401

    async def test_get_current_user_invalid_scheme(self):
        with pytest.raises(HTTPException, match="Invalid authentication scheme") as e:
            await get_current_user(f"Basic {SAMPLE_TOKEN}")
        assert e.value.status_code == 401

    async def test_get_current_user_malformed_header(self):
        with pytest.raises(HTTPException, match="Invalid authentication scheme") as e:
            await get_current_user("BearerTokenWithoutSpace")
        assert e.value.status_code == 401

    async def test_get_current_user_decode_error(self):
        with patch("jwt.decode", side_effect=Exception("decode error")):
            with pytest.raises(HTTPException, match="Token parsing error: decode error") as e:
                await get_current_user(f"Bearer {SAMPLE_TOKEN}")
            assert e.value.status_code == 401

    async def test_get_owner_from_token_success(self):
        owner = await get_owner_from_token(user=SAMPLE_PAYLOAD)
        assert owner == "user123"

    async def test_get_owner_from_token_missing_sub(self):
        with pytest.raises(HTTPException, match="Token missing 'sub' claim") as e:
            await get_owner_from_token(user={"roles": ["user"]})
        assert e.value.status_code == 401

    async def test_get_user_roles_success(self):
        roles = await get_user_roles(user=SAMPLE_PAYLOAD)
        assert roles == ["user", "pro"]

    async def test_get_user_roles_missing(self):
        roles = await get_user_roles(user={"sub": "user123"})
        assert roles == []

    async def test_get_user_roles_not_a_list(self):
        roles = await get_user_roles(user={"sub": "user123", "roles": "user,pro"})
        assert roles == []

    async def test_get_user_roles_from_realm_access(self):
        payload = {"sub": "user123", "realm_access": {"roles": ["user", "guest"]}}
        roles = await get_user_roles(user=payload)
        assert roles == ["user", "guest"]

    async def test_get_user_context(self):
        context = await get_user_context(user_id="user123", roles=["user", "pro"])
        assert context == {"user_id": "user123", "roles": ["user", "pro"]}

    async def test_validate_create_permission_pro(self):
        try:
            await validate_create_permission(roles=["user", "pro"])
        except HTTPException:
            pytest.fail("validate_create_permission() raised HTTPException unexpectedly!")

    async def test_validate_create_permission_admin(self):
        try:
            await validate_create_permission(roles=["admin"])
        except HTTPException:
            pytest.fail("validate_create_permission() raised HTTPException unexpectedly!")

    async def test_validate_create_permission_insufficient(self):
        with pytest.raises(HTTPException, match="Insufficient permissions to create resources") as e:
            await validate_create_permission(roles=["user"])
        assert e.value.status_code == 403


if __name__ == "__main__":
    pytest.main()
