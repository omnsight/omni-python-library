import json
from typing import List, Optional

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

    if "roles" in user:
        if isinstance(user["roles"], list):
            return user["roles"]
        elif isinstance(user["roles"], str):
            return user["roles"].split(",")
        else:
            raise HTTPException(status_code=401, detail=f"Invalid roles in auth - {user['roles']}")
    elif "realm_access" in user and "roles" in user["realm_access"]:
        if isinstance(user["realm_access"]["roles"], list):
            return user["realm_access"]["roles"]
        else:
            raise HTTPException(status_code=401, detail=f"Invalid realm_access.roles in auth - {user['realm_access']['roles']}")
    elif "cognito:groups" in user:
        if isinstance(user["cognito:groups"], list):
            return user["cognito:groups"]
        else:
            raise HTTPException(status_code=401, detail=f"Invalid cognito:groups in auth - {user['cognito:groups']}")
    else:
        return ["guest"]


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
