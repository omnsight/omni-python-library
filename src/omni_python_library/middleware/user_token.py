from typing import Dict, List, Optional

import jwt
from fastapi import Depends, Header, HTTPException


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict | None:
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication")

    try:
        return jwt.decode(parts[1], options={"verify_signature": False})
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication")


async def get_owner_from_token(user: dict | None = Depends(get_current_user)) -> str:
    """
    Extracts the owner ID from the user token.
    Aliyun IDaaS uses 'sub' as the unique identifier for the user.
    """
    if user is None:
        return ""
    owner = user.get("sub")
    if not owner or not isinstance(owner, str):
        return ""
    return owner


async def get_user_roles(user: dict | None = Depends(get_current_user)) -> List[str]:
    """
    Extracts the user roles from the token.
    """
    if user is None:
        return ["guest"]

    roles = user.get("roles")
    if roles is None:
        roles = user.get("realm_access", {}).get("roles", ["guest"])

    if not isinstance(roles, list):
        raise HTTPException(status_code=401, detail="Invalid authentication")
    return roles


async def get_user_context(
    user_id: str = Depends(get_owner_from_token),
    roles: List[str] = Depends(get_user_roles),
) -> dict:
    return {"user_id": user_id, "roles": roles}


async def validate_create_permission(
    roles: List[str] = Depends(get_user_roles),
) -> None:
    """
    Validates that the user has 'pro' or 'admin' role.
    """
    if not any(role in roles for role in ["pro", "paid", "admin"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions to create resources")
