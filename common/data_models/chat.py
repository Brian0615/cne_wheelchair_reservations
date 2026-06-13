from enum import StrEnum
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class ChatRole(StrEnum):
    """Role of a participant in a chat conversation"""
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """A single message in a chatbot conversation"""
    model_config = ConfigDict(extra="forbid")

    role: ChatRole = Field(title="Role")
    content: str = Field(title="Content")


class ChatRequest(BaseModel):
    """Request body for the chatbot endpoint"""
    model_config = ConfigDict(extra="forbid")

    message: str = Field(title="Message")
    history: List[ChatMessage] = Field(title="Conversation History", default_factory=list)
