from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.api.deps import DbSession
from app.auth import get_current_user
from app.models.company import Company
from app.models.user import User
from app.models.user_tracked_event import UserTrackedEvent
from app.schemas.user import UserOut

router = APIRouter(prefix="/api", tags=["users"])


async def get_or_create_user(db: DbSession, clerk_user: dict) -> User:
    """Get existing user by clerk_id or create a new one."""
    clerk_id = clerk_user.get("sub", "")
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()
    if user:
        return user

    user = User(
        clerk_id=clerk_id,
        email=clerk_user.get("email", ""),
        name=clerk_user.get("name"),
    )
    db.add(user)
    await db.flush()
    return user


@router.get("/me", response_model=UserOut)
async def get_me(db: DbSession, user: dict = Depends(get_current_user)):
    """Return the current authenticated user, creating if needed."""
    db_user = await get_or_create_user(db, user)

    # Count tracked events
    count_result = await db.execute(
        select(func.count(UserTrackedEvent.id)).where(UserTrackedEvent.user_id == db_user.id)
    )
    tracked_count = count_result.scalar_one()

    # Count companies
    company_count_result = await db.execute(
        select(func.count(Company.id)).where(Company.user_id == db_user.id)
    )
    company_count = company_count_result.scalar_one()

    return UserOut(
        id=db_user.id,
        clerk_id=db_user.clerk_id,
        email=db_user.email,
        name=db_user.name,
        created_at=db_user.created_at,
        company_count=company_count,
        tracked_event_count=tracked_count,
    )
