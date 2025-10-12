from typing import List, Optional
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.auth.models import Role, UserRole
from app.auth.security import decode_token

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


async def get_user_roles(db: AsyncSession, user_id: int) -> List[str]:
    # fetch role names for user
    role_q = await db.execute(
        select(Role.name).join(UserRole, Role.id == UserRole.role_id).where(UserRole.user_id == user_id)
    )
    return [r[0] for r in role_q.all()]


def role_required(required_role: str):
    async def dependency(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> User:
        roles = await get_user_roles(db, user.id)
        if required_role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return dependency


async def get_current_user_ws(token: str) -> Optional[User]:
    try:
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as s:
            res = await s.execute(select(User).where(User.id == int(user_id)))
            user = res.scalar_one_or_none()
            if user and user.is_active:
                return user
    except Exception:
        logger.exception("WS auth failed")
    return None
