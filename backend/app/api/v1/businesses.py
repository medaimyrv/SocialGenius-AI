import uuid

from fastapi import APIRouter

from app.api.deps import DB, CurrentUser
from app.schemas.business import BusinessCreate, BusinessResponse, BusinessUpdate
from app.services import business_service

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.get("", response_model=list[BusinessResponse])
async def list_businesses(db: DB, current_user: CurrentUser):
    return await business_service.get_businesses(db, current_user.id)


@router.post("", response_model=BusinessResponse, status_code=201)
async def create_business(
    data: BusinessCreate, db: DB, current_user: CurrentUser
):
    return await business_service.create_business(db, current_user.id, data)


@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    return await business_service.get_business(db, business_id, current_user.id)


@router.patch("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: uuid.UUID,
    data: BusinessUpdate,
    db: DB,
    current_user: CurrentUser,
):
    return await business_service.update_business(
        db, business_id, current_user.id, data
    )


@router.delete("/{business_id}", status_code=204)
async def delete_business(
    business_id: uuid.UUID, db: DB, current_user: CurrentUser
):
    await business_service.delete_business(db, business_id, current_user.id)
