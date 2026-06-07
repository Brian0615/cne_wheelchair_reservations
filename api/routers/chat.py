from fastapi import APIRouter

from api.src.chat_service import ChatService
from api.src.utils import auto_process_database_errors
from common.data_models import ChatRequest

chat_service = ChatService()
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask")
@auto_process_database_errors
def ask(request: ChatRequest) -> str:
    """Answer a chatbot question about CNE rentals, reservations, and inventory"""
    return chat_service.answer(message=request.message, history=request.history)
