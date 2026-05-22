from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.models import MessageType, MessageStatus, TaskStatus


# ── Inbound ──────────────────────────────────────────────
class MessageCreate(BaseModel):
    type: MessageType
    sender: str
    subject: Optional[str] = None
    body: str


# ── Outbound ─────────────────────────────────────────────
class TaskOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    assignee: Optional[str]
    deadline: Optional[str]
    priority: Optional[str]
    status: TaskStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: UUID
    type: MessageType
    sender: str
    subject: Optional[str]
    body: str
    status: MessageStatus
    message_class: Optional[str]
    urgency: Optional[str]
    priority_score: Optional[float]
    summary: Optional[str]
    reasoning: Optional[str]
    entities: Optional[dict]
    created_at: datetime
    tasks: list[TaskOut] = []

    model_config = {"from_attributes": True}


class MessageListOut(BaseModel):
    messages: list[MessageOut]
    total: int


class ProcessResponse(BaseModel):
    message_id: UUID
    status: str
    priority_score: Optional[float]
    message_class: Optional[str]
    urgency: Optional[str]
    summary: Optional[str]
    reasoning: Optional[str]
    tasks_created: int


class SimilarMessage(BaseModel):
    id: UUID
    sender: str
    subject: Optional[str]
    summary: Optional[str]
    similarity: float
    created_at: datetime