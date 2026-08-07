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


class ChatResponse(BaseModel):
    """Response body for the chatbot endpoint"""
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(title="Answer")
    model: str = Field(title="Model", description="The Gemini model that produced this answer.")
    input_tokens: int = Field(title="Input Tokens")
    output_tokens: int = Field(title="Output Tokens")
    cache_read_tokens: int = Field(title="Cache Read Tokens", description="Input tokens served from cache.")
    total_tokens: int = Field(title="Total Tokens", description="Input tokens plus output tokens.")
