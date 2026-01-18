import types

import pytest
from fastapi import HTTPException

from cns_service_simplified import BrainOpsCNS


@pytest.mark.asyncio
async def test_cns_embedding_requires_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_AI_API_KEY", raising=False)

    cns = BrainOpsCNS()

    with pytest.raises(HTTPException) as exc:
        await cns._generate_embedding("hello")

    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_cns_embedding_returns_vector(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_AI_API_KEY", raising=False)

    cns = BrainOpsCNS()

    class DummyEmbeddings:
        async def create(self, model, input):
            return types.SimpleNamespace(data=[types.SimpleNamespace(embedding=[0.1, 0.2])])

    class DummyClient:
        embeddings = DummyEmbeddings()

    monkeypatch.setattr(cns, "_get_openai_client", lambda: DummyClient())

    result = await cns._generate_embedding("hello")

    assert result == [0.1, 0.2]
