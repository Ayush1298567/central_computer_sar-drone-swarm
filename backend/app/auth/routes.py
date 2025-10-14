from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from app.core.database import get_db
from app.models.user import User
from app.auth.models import Role, UserRole
from app.auth.schemas import UserCreate, UserLogin, TokenResponse, TokenRefreshRequest, UserResponse
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # Idempotent register: if user exists, ensure roles and return
    res_existing = await db.execute(select(User).where((User.username == user_in.username) | (User.email == user_in.email)))
    user = res_existing.scalar_one_or_none()
    if not user:
        user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hash_password(user_in.password),
            is_active=True,
            is_admin=False,
        )
        db.add(user)
        await db.flush()

    # Ensure roles exist (admin, operator, viewer)
    role_map = {}
    for name in ["admin", "operator", "viewer"]:
        res = await db.execute(select(Role).where(Role.name == name))
        role = res.scalar_one_or_none()
        if not role:
            role = Role(name=name, is_system=True)
            db.add(role)
            await db.flush()
        role_map[name] = role

    # Assign requested roles or default viewer (avoid duplicates)
    role_names = user_in.roles or ["viewer"]
    existing_roles = set()
    role_rows = await db.execute(select(Role.name).join(UserRole, Role.id == UserRole.role_id).where(UserRole.user_id == user.id))
    existing_roles.update([r[0] for r in role_rows.all()])
    for rname in role_names:
        if rname in existing_roles:
            continue
        role = role_map.get(rname)
        if role:
            db.add(UserRole(user_id=user.id, role_id=role.id))

    await db.commit()

    # Build response
    final_role_rows = await db.execute(select(Role.name).join(UserRole, Role.id == UserRole.role_id).where(UserRole.user_id == user.id))
    res_roles = [r[0] for r in final_role_rows.all()]
    return UserResponse(id=user.id, username=user.username, email=user.email, is_active=user.is_active, roles=res_roles)


@router.post("/login", response_model=TokenResponse)
async def login(login_in: UserLogin, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.username == login_in.username))
    user = res.scalar_one_or_none()
    if not user or not verify_password(login_in.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # collect roles
    role_rows = await db.execute(select(Role.name).join(UserRole, Role.id == UserRole.role_id).where(UserRole.user_id == user.id))
    roles = [r[0] for r in role_rows.all()]

    access = create_access_token(str(user.id), roles)
    refresh = create_refresh_token(str(user.id))
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")
    res = await db.execute(select(User).where(User.id == int(user_id)))
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    role_rows = await db.execute(select(Role.name).join(UserRole, Role.id == UserRole.role_id).where(UserRole.user_id == user.id))
    roles = [r[0] for r in role_rows.all()]

    access = create_access_token(str(user.id), roles)
    new_refresh = create_refresh_token(str(user.id))
    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

