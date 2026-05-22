from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.db.session import Base
import uuid
import enum


class MessageType(str, enum.Enum):
    email = "email"
    slack = "slack"
    note = "note"


class MessageStatus(str, enum.Enum):
    pending = "pending"
    processed = "processed"
    actioned = "actioned"


class TaskStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    done = "done"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[MessageType] = mapped_column(SAEnum(MessageType), nullable=False)
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[MessageStatus] = mapped_column(SAEnum(MessageStatus), default=MessageStatus.pending)

    # AI-generated fields
    message_class: Mapped[str | None] = mapped_column(String(50))   # task, incident, fyi, question
    urgency: Mapped[str | None] = mapped_column(String(20))          # low, medium, high, critical
    priority_score: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)
    reasoning: Mapped[str | None] = mapped_column(Text)
    entities: Mapped[dict | None] = mapped_column(JSONB)             # {people, systems, deadlines}
    ai_metadata: Mapped[dict | None] = mapped_column(JSONB)

    # Vector embedding (text-embedding-3-small = 1536 dims)
    embedding: Mapped[list | None] = mapped_column(Vector(1536))

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))

    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="message", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    assignee: Mapped[str | None] = mapped_column(String(255))
    deadline: Mapped[str | None] = mapped_column(String(100))
    priority: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[TaskStatus] = mapped_column(SAEnum(TaskStatus), default=TaskStatus.open)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    message: Mapped["Message"] = relationship("Message", back_populates="tasks")