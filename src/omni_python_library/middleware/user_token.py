from fastapi import Header, HTTPException, Depends
import jwt
from typing import Optional, List, Dict


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Extracts and parses the JWT token from the Authorization header.
    Assumes the token follows Aliyun IDaaS format.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    token = parts[1]

    try:
        # Decode the token without verification (as we don't have the public key configured yet)
        # In a production environment, you should configure the public key and verify the signature.
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token parsing error: {str(e)}")


async def get_owner_from_token(user: dict = Depends(get_current_user)) -> str:
    """
    Extracts the owner ID from the user token.
    Aliyun IDaaS uses 'sub' as the unique identifier for the user.
    """
    owner = user.get("sub")
    if not owner:
        raise HTTPException(status_code=401, detail="Token missing 'sub' claim")
    return owner


async def get_user_roles(user: dict = Depends(get_current_user)) -> List[str]:
    """
    Extracts the user roles from the token.
    """
    roles = user.get("roles", [])
    if not isinstance(roles, list):
        # Handle case where roles might be a comma-separated string or missing
        return []
    return roles


async def get_user_context(
    user_id: str = Depends(get_owner_from_token),
    roles: List[str] = Depends(get_user_roles),
) -> Dict:
    return {"user_id": user_id, "roles": roles}


async def validate_create_permission(
    roles: List[str] = Depends(get_user_roles),
) -> None:
    """
    Validates that the user has 'pro' or 'admin' role.
    """
    if not any(role in roles for role in ["pro", "admin"]):
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to create resources"
        )
