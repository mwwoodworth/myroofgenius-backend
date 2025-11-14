"""
Core RAG service that powers ingestion and query flows for the AI DevOps system.
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import chromadb

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - optional dependency
    def tqdm(sequence, **_kwargs):
        return sequence

from .embeddings import EmbeddingProvider, batch

logger = logging.getLogger(__name__)

EXCLUDED_DIRS = {
    ".git",
    ".next",
    ".turbo",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "venv",
}

DEFAULT_PATTERNS = [
    "*.md",
    "*.mdx",
    "*.txt",
    "*.py",
    "*.ts",
    "*.tsx",
    "*.json",
]


@dataclass
class IngestionOptions:
    paths: List[str] = field(default_factory=lambda: [".."])
    glob_patterns: List[str] | None = field(default_factory=lambda: list(DEFAULT_PATTERNS))
    chunk_size: int = 1000
    chunk_overlap: int = 200
    provider: str = os.getenv("EMBED_PROVIDER", "sentence-transformers")
    model_name: str = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
    collection_name: str = "local_docs"
    batch_size: int = 64
    reset: bool = False
    max_files: int | None = None


@dataclass
class QueryOptions:
    query: str
    n_results: int = 5
    provider: str | None = None
    model_name: str | None = None
    collection_name: str = "local_docs"


class RagService:
    """Encapsulates ingestion and semantic search over local repositories."""

    def __init__(
        self,
        storage_path: Path | None = None,
        repo_root: Path | None = None,
    ) -> None:
        self.repo_root = repo_root or Path(__file__).resolve().parents[1]
        self.storage_path = storage_path or (Path(__file__).resolve().parent / "chroma_db")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(path=str(self.storage_path))
        self._collections: Dict[str, object] = {}
        self._embedding_provider = EmbeddingProvider()

    def ingest(self, options: IngestionOptions) -> Dict[str, int | str]:
        """Ingest documents into ChromaDB using the provided options."""
        logger.info("Starting ingestion with options: %s", options)
        if options.reset:
            self._reset_collection(options.collection_name)

        collection = self._get_collection(options.collection_name)
        patterns = options.glob_patterns or list(DEFAULT_PATTERNS)
        files = self._resolve_files(options.paths, patterns)

        if options.max_files:
            files = files[: options.max_files]

        logger.info("Found %s files for ingestion", len(files))

        documents: List[str] = []
        metadatas: List[Dict[str, str]] = []
        ids: List[str] = []

        for file_path in tqdm(files, desc="Reading files"):
            try:
                text = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = file_path.read_text(encoding="latin-1", errors="ignore")

            chunks = list(
                chunk_text(text, chunk_size=options.chunk_size, overlap=options.chunk_overlap)
            )
            relative_source = str(file_path.relative_to(self.repo_root))
            for idx, chunk in enumerate(chunks):
                chunk_id = f"{relative_source}::{idx}::{uuid.uuid4().hex}"
                documents.append(chunk)
                metadatas.append(
                    {
                        "source": relative_source,
                        "chunk_index": str(idx),
                        "provider": options.provider,
                        "model": options.model_name,
                    }
                )
                ids.append(chunk_id)

        if not documents:
            logger.warning("No documents collected for ingestion.")
            return {
                "files_processed": 0,
                "chunks_added": 0,
                "collection": options.collection_name,
                "provider": options.provider,
            }

        total_chunks = len(documents)
        logger.info("Embedding %s chunks", total_chunks)
        chunks_processed = 0
        for batch_docs, batch_ids, batch_meta in zip(
            batch(documents, options.batch_size),
            batch(ids, options.batch_size),
            batch(metadatas, options.batch_size),
        ):
            embeddings = self._embedding_provider.embed_documents(
                list(batch_docs),
                provider=options.provider,
                model_name=options.model_name,
            )
            collection.add(
                ids=list(batch_ids),
                documents=list(batch_docs),
                metadatas=list(batch_meta),
                embeddings=embeddings,
            )
            chunks_processed += len(batch_docs)

        logger.info("Ingestion complete: %s chunks", chunks_processed)
        return {
            "files_processed": len(files),
            "chunks_added": chunks_processed,
            "collection": options.collection_name,
            "provider": options.provider,
            "model": options.model_name,
        }

    def query(self, options: QueryOptions) -> List[Dict[str, object]]:
        """Query the vector store for relevant chunks."""
        if not options.query.strip():
            raise ValueError("Query text must not be empty")

        collection = self._get_collection(options.collection_name)
        embedding_provider = self._embedding_provider
        embedding = embedding_provider.embed_query(
            options.query,
            provider=options.provider,
            model_name=options.model_name,
        )
        results = collection.query(
            query_embeddings=[embedding],
            n_results=options.n_results,
            include=["documents", "metadatas", "distances"],
        )
        documents = results.get("documents", [[]])[0] if results else []
        metadatas = results.get("metadatas", [[]])[0] if results else []
        distances = results.get("distances", [[]])[0] if results else []
        response: List[Dict[str, object]] = []
        for doc, metadata, distance in zip(documents, metadatas, distances):
            similarity = 1 - float(distance) if distance is not None else 0.0
            response.append(
                {
                    "content": doc,
                    "similarity": similarity,
                    "metadata": metadata or {},
                }
            )
        return response

    def get_status(self, collection_name: str = "local_docs") -> Dict[str, str | int]:
        """Return collection statistics."""
        collection = self._get_collection(collection_name)
        return {
            "collection": collection_name,
            "document_count": collection.count(),
            "storage_path": str(self.storage_path),
        }

    def _reset_collection(self, name: str) -> None:
        logger.info("Resetting collection %s", name)
        try:
            self._client.delete_collection(name)
        except chromadb.errors.NotFoundError:
            pass
        self._collections.pop(name, None)

    def _get_collection(self, name: str):
        if name not in self._collections:
            self._collections[name] = self._client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[name]

    def _resolve_files(self, paths: List[str], patterns: List[str]) -> List[Path]:
        resolved_files: List[Path] = []
        for raw_path in paths:
            path = Path(raw_path)
            if not path.is_absolute():
                path = (self.repo_root / raw_path).resolve()
            if path.is_file():
                resolved_files.append(path)
                continue
            if not path.exists():
                logger.warning("Path %s does not exist, skipping", raw_path)
                continue
            for pattern in patterns:
                for file_path in path.rglob(pattern):
                    if not file_path.is_file():
                        continue
                    if any(part in EXCLUDED_DIRS for part in file_path.parts):
                        continue
                    resolved_files.append(file_path)
        # Deduplicate while preserving order
        seen: set[Path] = set()
        unique_files: List[Path] = []
        for file_path in resolved_files:
            if file_path in seen:
                continue
            seen.add(file_path)
            unique_files.append(file_path)
        return unique_files


def chunk_text(text: str, chunk_size: int, overlap: int) -> Iterable[str]:
    """Split text into overlapping character chunks."""
    cleaned = normalize_whitespace(text)
    if chunk_size <= 0:
        chunk_size = 1000
    if overlap >= chunk_size:
        overlap = chunk_size // 4
    step = max(chunk_size - overlap, 1)
    for start in range(0, len(cleaned), step):
        end = start + chunk_size
        yield cleaned[start:end]


def normalize_whitespace(text: str) -> str:
    """Collapse excessive whitespace for more consistent embeddings."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\n{3,}", "\n\n", text)
