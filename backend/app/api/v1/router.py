from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.businesses import router as businesses_router
from app.api.v1.calendars import router as calendars_router
from app.api.v1.chat import router as chat_router
from app.api.v1.content import router as content_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.subscriptions import router as subscriptions_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(businesses_router)
api_v1_router.include_router(conversations_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(calendars_router)
api_v1_router.include_router(content_router)
api_v1_router.include_router(subscriptions_router)
api_v1_router.include_router(admin_router)
