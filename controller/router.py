from fastapi import APIRouter
from controller.v2 import (
    dialogo_controller,
    chatbot_controller,
    qdrant_controller,
)
router = APIRouter()
router.include_router(dialogo_controller.router)
router.include_router(chatbot_controller.chatbot_router)
router.include_router(qdrant_controller.qdrant)