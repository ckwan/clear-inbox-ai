from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.models.models import Message, Task, MessageStatus
from app.schemas.schema import MessageCreate
from app.services.embedding_service import embed_text, build_message_text


async def create_message(db: AsyncSession, data: MessageCreate) -> Message:
    """Persist a new message and generate its embedding."""
    msg = Message(
        type=data.type,
        sender=data.sender,
        subject=data.subject,
        body=data.body,
    )
    db.add(msg)
    await db.flush()  # get the ID before embedding

    # Generate and store embedding
    text_to_embed = build_message_text(data.sender, data.subject, data.body)
    msg.embedding = await embed_text(text_to_embed)

    await db.commit()
    await db.refresh(msg)
    return msg


async def get_message(db: AsyncSession, message_id: UUID) -> Message | None:
    result = await db.execute(
        select(Message)
        .options(selectinload(Message.tasks))
        .where(Message.id == message_id)
    )
    return result.scalar_one_or_none()


async def list_messages(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
) -> tuple[list[Message], int]:
    query = select(Message).options(selectinload(Message.tasks))
    count_query = select(func.count(Message.id))

    if status:
        query = query.where(Message.status == status)
        count_query = count_query.where(Message.status == status)

    query = query.order_by(Message.priority_score.desc().nullslast(), Message.created_at.desc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    count_result = await db.execute(count_query)

    return result.scalars().all(), count_result.scalar_one()


async def find_similar_messages(
    db: AsyncSession,
    message_id: UUID,
    limit: int = 5,
) -> list[tuple[Message, float]]:
    """Find semantically similar messages using pgvector cosine similarity."""
    msg = await get_message(db, message_id)
    if not msg or msg.embedding is None:
        return []

    result = await db.execute(
        text("""
            SELECT id, 1 - (embedding <=> :embedding) AS similarity
            FROM messages
            WHERE id != :message_id
              AND embedding IS NOT NULL
            ORDER BY embedding <=> :embedding
            LIMIT :limit
        """),
        {
            "embedding": str(msg.embedding),
            "message_id": str(message_id),
            "limit": limit,
        },
    )
    rows = result.fetchall()

    similar = []
    for row in rows:
        related = await get_message(db, row.id)
        if related:
            similar.append((related, float(row.similarity)))
    return similar


async def update_message_ai_fields(
    db: AsyncSession,
    message_id: UUID,
    *,
    message_class: str,
    urgency: str,
    priority_score: float,
    summary: str,
    reasoning: str,
    entities: dict,
    ai_metadata: dict,
) -> Message | None:
    msg = await get_message(db, message_id)
    if not msg:
        return None

    msg.message_class = message_class
    msg.urgency = urgency
    msg.priority_score = priority_score
    msg.summary = summary
    msg.reasoning = reasoning
    msg.entities = entities
    msg.ai_metadata = ai_metadata
    msg.status = MessageStatus.processed

    await db.commit()
    await db.refresh(msg)
    return msg


async def create_tasks_for_message(
    db: AsyncSession,
    message_id: UUID,
    tasks_data: list[dict],
) -> list[Task]:
    tasks = []
    for t in tasks_data:
        task = Task(
            message_id=message_id,
            title=t.get("title", "Untitled task"),
            description=t.get("description"),
            assignee=t.get("assignee"),
            deadline=t.get("deadline"),
            priority=t.get("priority", "medium"),
        )
        db.add(task)
        tasks.append(task)

    await db.commit()
    return tasks