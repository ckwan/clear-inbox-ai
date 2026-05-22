from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.db.session import get_db
from app.schemas.schema import MessageCreate, MessageOut, MessageListOut, SimilarMessage
from app.services import message_service

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=MessageOut, status_code=201)
async def ingest_message(payload: MessageCreate, db: AsyncSession = Depends(get_db)):
    """Ingest a new message (email, Slack, or note) and generate its embedding."""
    msg = await message_service.create_message(db, payload)
    return msg


@router.get("/", response_model=MessageListOut)
async def list_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return messages sorted by priority score descending."""
    messages, total = await message_service.list_messages(db, skip=skip, limit=limit, status=status)
    return {"messages": messages, "total": total}


@router.get("/{message_id}", response_model=MessageOut)
async def get_message(message_id: UUID, db: AsyncSession = Depends(get_db)):
    msg = await message_service.get_message(db, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return msg


@router.get("/{message_id}/similar", response_model=list[SimilarMessage])
async def get_similar_messages(
    message_id: UUID,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """Find semantically related messages using pgvector cosine similarity."""
    similar = await message_service.find_similar_messages(db, message_id, limit=limit)
    return [
        SimilarMessage(
            id=msg.id,
            sender=msg.sender,
            subject=msg.subject,
            summary=msg.summary,
            similarity=score,
            created_at=msg.created_at,
        )
        for msg, score in similar
    ]