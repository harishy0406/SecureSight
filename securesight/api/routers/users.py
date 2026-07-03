from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from securesight.api.core.database import get_session
from securesight.api.dependencies import get_current_user, require_superuser
from securesight.api.models.user import User
from securesight.api.schemas.common import Message, PaginatedResponse
from securesight.api.schemas.user import UserCreate, UserPublic, UserUpdate

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[UserPublic])
async def list_users(
    page: int = 1,
    per_page: int = 50,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_superuser),
):
    query = select(User).order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await session.execute(query)
    users = result.scalars().all()
    total_result = await session.execute(select(func.count(User.id)))
    total = total_result.scalar() or 0

    return PaginatedResponse(
        items=[UserPublic.model_validate(u) for u in users],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
    )


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserPublic.model_validate(user)


@router.put("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: int,
    request: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.id != user_id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    await session.flush()
    await session.refresh(user)
    return UserPublic.model_validate(user)


@router.delete("/{user_id}", response_model=Message)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_superuser),
):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await session.delete(user)
    await session.flush()
    return Message(detail="User deleted successfully")
