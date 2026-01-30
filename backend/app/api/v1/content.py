import uuid

from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DB, CurrentUser
from app.core.exceptions import NotFoundError
from app.models.business import Business
from app.models.content_calendar import ContentCalendar
from app.models.content_piece import ContentPiece
from app.schemas.content_piece import ContentPieceResponse, ContentPieceUpdate

router = APIRouter(prefix="/content", tags=["content"])


@router.get("", response_model=list[ContentPieceResponse])
async def list_content(
    db: DB,
    current_user: CurrentUser,
    calendar_id: uuid.UUID | None = Query(None),
    platform: str | None = Query(None),
):
    query = (
        select(ContentPiece)
        .join(ContentCalendar)
        .join(Business)
        .where(Business.owner_id == current_user.id)
    )
    if calendar_id:
        query = query.where(ContentPiece.calendar_id == calendar_id)
    if platform:
        query = query.where(ContentPiece.platform == platform)

    result = await db.execute(
        query.order_by(ContentPiece.scheduled_date, ContentPiece.scheduled_time)
    )
    return list(result.scalars().all())


@router.get("/{piece_id}", response_model=ContentPieceResponse)
async def get_content_piece(
    piece_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    result = await db.execute(
        select(ContentPiece)
        .join(ContentCalendar)
        .join(Business)
        .where(
            ContentPiece.id == piece_id,
            Business.owner_id == current_user.id,
        )
    )
    piece = result.scalar_one_or_none()
    if not piece:
        raise NotFoundError("Content piece not found")
    return piece


@router.patch("/{piece_id}", response_model=ContentPieceResponse)
async def update_content_piece(
    piece_id: uuid.UUID,
    data: ContentPieceUpdate,
    db: DB,
    current_user: CurrentUser,
):
    result = await db.execute(
        select(ContentPiece)
        .join(ContentCalendar)
        .join(Business)
        .where(
            ContentPiece.id == piece_id,
            Business.owner_id == current_user.id,
        )
    )
    piece = result.scalar_one_or_none()
    if not piece:
        raise NotFoundError("Content piece not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(piece, key, value)
    await db.flush()
    return piece


@router.delete("/{piece_id}", status_code=204)
async def delete_content_piece(
    piece_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    result = await db.execute(
        select(ContentPiece)
        .join(ContentCalendar)
        .join(Business)
        .where(
            ContentPiece.id == piece_id,
            Business.owner_id == current_user.id,
        )
    )
    piece = result.scalar_one_or_none()
    if not piece:
        raise NotFoundError("Content piece not found")
    await db.delete(piece)
