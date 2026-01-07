import types

import pytest
from fastapi import HTTPException

from cns_service import BrainOpsCNS


@pytest.mark.asyncio
async def test_cns_service_embedding_requires_openai_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    cns = BrainOpsCNS(db_pool=None)

    with pytest.raises(HTTPException) as exc:
        await cns._generate_embedding("hello")

    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_cns_service_embedding_returns_vector(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    cns = BrainOpsCNS(db_pool=None)

    class DummyEmbeddings:
        async def create(self, model, input):
            return types.SimpleNamespace(data=[types.SimpleNamespace(embedding=[0.3, 0.4])])

    class DummyClient:
        embeddings = DummyEmbeddings()

    monkeypatch.setattr(cns, "_get_openai_client", lambda: DummyClient())

    result = await cns._generate_embedding("hello")

    assert result == [0.3, 0.4]
