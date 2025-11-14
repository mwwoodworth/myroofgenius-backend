"""
Embedding provider utilities for the RagService.

Provides multiple backends with automatic fallback:
- sentence-transformers (preferred quality)
- Ollama embeddings API
- Deterministic hash-based vectors (always available fallback)
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass, replace
from typing import Iterable, List, Sequence

import requests

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmbeddingConfig:
    """Configuration for embedding generation."""

    provider: str = os.getenv("EMBED_PROVIDER", "sentence-transformers")
    model_name: str = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")


class EmbeddingProvider:
    """High-level embedding interface with automatic provider fallback."""

    def __init__(self) -> None:
        self._cache: dict[str, object] = {}

    def embed_documents(
        self,
        texts: Sequence[str],
        provider: str | None = None,
        model_name: str | None = None,
    ) -> List[List[float]]:
        config = self._resolve_config(provider, model_name)
        return self._run_with_fallback(texts, config)

    def embed_query(
        self,
        text: str,
        provider: str | None = None,
        model_name: str | None = None,
    ) -> List[float]:
        config = self._resolve_config(provider, model_name)
        embeddings = self._run_with_fallback([text], config)
        return embeddings[0]

    def _resolve_config(
        self, provider: str | None, model_name: str | None
    ) -> EmbeddingConfig:
        base = EmbeddingConfig()
        if provider or model_name:
            return EmbeddingConfig(
                provider=provider or base.provider,
                model_name=model_name or base.model_name,
                ollama_url=base.ollama_url,
            )
        return base

    def _run_with_fallback(
        self, texts: Sequence[str], config: EmbeddingConfig
    ) -> List[List[float]]:
        try:
            return self._generate_embeddings(texts, config)
        except Exception as exc:
            logger.warning(
                "Primary embedding provider '%s' failed (%s). Falling back to hash embeddings.",
                config.provider,
                exc,
            )
            if config.provider == "hash":
                # Nothing else we can do—re-raise original error
                raise
            fallback_config = replace(config, provider="hash", model_name="hash://sha256")
            return self._generate_embeddings(texts, fallback_config)

    def _generate_embeddings(
        self, texts: Sequence[str], config: EmbeddingConfig
    ) -> List[List[float]]:
        provider = config.provider.lower()
        if provider == "sentence-transformers":
            return self._embed_sentence_transformers(texts, config.model_name)
        if provider == "ollama":
            return self._embed_ollama(texts, config)
        if provider == "hash":
            return [self._hash_embedding(text) for text in texts]
        raise ValueError(f"Unsupported embedding provider '{config.provider}'")

    def _embed_sentence_transformers(
        self, texts: Sequence[str], model_name: str
    ) -> List[List[float]]:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. "
                "Install it or choose a different embedding provider."
            ) from exc

        cache_key = f"st::{model_name}"
        if cache_key not in self._cache:
            logger.info("Loading sentence-transformers model %s", model_name)
            self._cache[cache_key] = SentenceTransformer(model_name)
        model: SentenceTransformer = self._cache[cache_key]  # type: ignore[assignment]
        embeddings = model.encode(
            list(texts),
            normalize_embeddings=False,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def _embed_ollama(
        self, texts: Sequence[str], config: EmbeddingConfig
    ) -> List[List[float]]:
        url = config.ollama_url.rstrip("/")
        endpoint = f"{url}/api/embeddings"
        embeddings: List[List[float]] = []
        for text in texts:
            response = requests.post(
                endpoint,
                json={"model": config.model_name, "prompt": text},
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            embedding = data.get("embedding")
            if not embedding:
                raise RuntimeError("Ollama embeddings API returned no embedding.")
            embeddings.append(list(map(float, embedding)))
        return embeddings

    def _hash_embedding(self, text: str, dim: int = 256) -> List[float]:
        """Create deterministic pseudo-embeddings from SHA256 hashes."""
        if not text:
            text = "empty"
        vector: List[float] = []
        # Use incremental hashing to fill the desired dimension
        salt = 0
        while len(vector) < dim:
            payload = f"{salt}:{text}".encode("utf-8")
            digest = hashlib.sha256(payload).digest()
            # Convert bytes to floats in range [-1, 1]
            vector.extend(
                ((byte / 255.0) * 2.0) - 1.0
                for byte in digest
            )
            salt += 1
        return vector[:dim]


def batch(iterable: Sequence[str], batch_size: int) -> Iterable[Sequence[str]]:
    """Yield chunks from a sequence."""
    for idx in range(0, len(iterable), batch_size):
        yield iterable[idx : idx + batch_size]
