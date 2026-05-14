"""OpenAI dense embeddings — Step 5.2."""

from __future__ import annotations

from openai import OpenAI

from app.config.env import get_env


def embed_texts_batch(texts: list[str]) -> list[list[float]]:
    """Embed each string with OpenAI embeddings (batched requests)."""
    if not texts:
        return []

    env = get_env()
    api_key = env.openai_api_key
    if not api_key:
        msg = "OPENAI_API_KEY is required to compute embeddings"
        raise ValueError(msg)

    client = OpenAI(api_key=api_key)
    model = env.openai_embedding_model
    batch_cap = 64
    all_out: list[list[float]] = []

    for start in range(0, len(texts), batch_cap):
        chunk = texts[start : start + batch_cap]
        response = client.embeddings.create(model=model, input=list(chunk))
        batch_vectors: list[list[float] | None] = [None] * len(chunk)
        for item in response.data:
            if item.index >= len(chunk):
                continue
            batch_vectors[item.index] = list(item.embedding)
        if None in batch_vectors:
            msg = "OpenAI embeddings response missing one or more indices"
            raise RuntimeError(msg)
        all_out.extend([v for v in batch_vectors if v is not None])

    return all_out
