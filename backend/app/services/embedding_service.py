from openai import AsyncOpenAI
from app.core.config import get_settings

settings = get_settings()
client = AsyncOpenAI(api_key=settings.openai_api_key)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS = 1536


async def embed_text(text: str) -> list[float]:
    """Generate an embedding vector for a given text string."""
    response = await client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text.replace("\n", " "),
    )
    return response.data[0].embedding


def build_message_text(sender: str, subject: str | None, body: str) -> str:
    """Combine message fields into a single string for embedding."""
    parts = [f"From: {sender}"]
    if subject:
        parts.append(f"Subject: {subject}")
    parts.append(f"Body: {body}")
    return "\n".join(parts)