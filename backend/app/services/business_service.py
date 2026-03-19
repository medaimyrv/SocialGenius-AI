from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.business import Business
from app.models.user_activity import UserActivity
from app.schemas.business import BusinessCreate, BusinessUpdate


async def create_business(
    db: AsyncSession, user_id: UUID, data: BusinessCreate
) -> Business:
    business = Business(owner_id=user_id, **data.model_dump())
    db.add(business)
    db.add(UserActivity(user_id=user_id, event_type="business_created",
                        metadata_={"name": data.name}))
    await db.flush()
    return business


async def get_businesses(db: AsyncSession, user_id: UUID) -> list[Business]:
    result = await db.execute(
        select(Business)
        .where(Business.owner_id == user_id)
        .order_by(Business.created_at.desc())
    )
    return list(result.scalars().all())


async def get_business(
    db: AsyncSession, business_id: UUID, user_id: UUID
) -> Business:
    result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise NotFoundError("Business not found")
    if business.owner_id != user_id:
        raise ForbiddenError("Not your business")
    return business


async def update_business(
    db: AsyncSession, business_id: UUID, user_id: UUID, data: BusinessUpdate
) -> Business:
    business = await get_business(db, business_id, user_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(business, key, value)
    db.add(UserActivity(user_id=user_id, event_type="business_updated",
                        metadata_={"business_id": str(business_id)}))
    await db.flush()
    await db.refresh(business)
    return business


async def delete_business(
    db: AsyncSession, business_id: UUID, user_id: UUID
) -> None:
    business = await get_business(db, business_id, user_id)
    db.add(UserActivity(user_id=user_id, event_type="business_deleted",
                        metadata_={"name": business.name, "business_id": str(business_id)}))
    await db.delete(business)
