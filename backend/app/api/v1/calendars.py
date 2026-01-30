import uuid

from fastapi import APIRouter, Query

from app.api.deps import DB, CurrentUser
from app.schemas.content_calendar import ContentCalendarResponse, ContentCalendarUpdate
from app.schemas.content_piece import ContentPieceResponse
from app.core.exceptions import NotFoundError, ForbiddenError
from app.models.content_calendar import ContentCalendar
from app.models.business import Business

from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/calendars", tags=["calendars"])


@router.get("", response_model=list[ContentCalendarResponse])
async def list_calendars(
    db: DB,
    current_user: CurrentUser,
    business_id: uuid.UUID | None = Query(None),
):
    query = (
        select(ContentCalendar)
        .join(Business)
        .where(Business.owner_id == current_user.id)
    )
    if business_id:
        query = query.where(ContentCalendar.business_id == business_id)

    result = await db.execute(query.order_by(ContentCalendar.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{calendar_id}", response_model=ContentCalendarResponse)
async def get_calendar(
    calendar_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    result = await db.execute(
        select(ContentCalendar)
        .options(selectinload(ContentCalendar.content_pieces))
        .join(Business)
        .where(
            ContentCalendar.id == calendar_id,
            Business.owner_id == current_user.id,
        )
    )
    calendar = result.scalar_one_or_none()
    if not calendar:
        raise NotFoundError("Calendar not found")
    return calendar


@router.get("/{calendar_id}/pieces", response_model=list[ContentPieceResponse])
async def get_calendar_pieces(
    calendar_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    calendar = await get_calendar(calendar_id, db, current_user)
    result = await db.execute(
        select(ContentCalendar)
        .options(selectinload(ContentCalendar.content_pieces))
        .where(ContentCalendar.id == calendar_id)
    )
    cal = result.scalar_one()
    return cal.content_pieces


@router.patch("/{calendar_id}", response_model=ContentCalendarResponse)
async def update_calendar(
    calendar_id: uuid.UUID,
    data: ContentCalendarUpdate,
    db: DB,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(ContentCalendar)
        .join(Business)
        .where(
            ContentCalendar.id == calendar_id,
            Business.owner_id == current_user.id,
        )
    )
    calendar = result.scalar_one_or_none()
    if not calendar:
        raise NotFoundError("Calendar not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(calendar, key, value)
    await db.flush()
    return calendar


@router.delete("/{calendar_id}", status_code=204)
async def delete_calendar(
    calendar_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    result = await db.execute(
        select(ContentCalendar)
        .join(Business)
        .where(
            ContentCalendar.id == calendar_id,
            Business.owner_id == current_user.id,
        )
    )
    calendar = result.scalar_one_or_none()
    if not calendar:
        raise NotFoundError("Calendar not found")
    await db.delete(calendar)
