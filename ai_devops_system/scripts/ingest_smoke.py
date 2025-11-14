#!/usr/bin/env python3
"""
Quick smoke test for the RAG ingestion pipeline.
Processes a handful of files to verify embeddings, storage,
and query paths are working.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rag.service import IngestionOptions, QueryOptions, RagService

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    docs = [
        repo_root / "README.md",
        repo_root / "ai_devops_system" / "README.md",
    ]
    service = RagService()
    options = IngestionOptions(
        paths=[str(path) for path in docs],
        max_files=len(docs),
        chunk_size=512,
        chunk_overlap=64,
        batch_size=16,
        provider="hash",
        model_name="hash://sha256",
        collection_name="rag_smoke",
        reset=True,
    )
    result = service.ingest(options)
    logging.info("Smoke ingestion complete: %s", result)

    query_result = service.query(
        QueryOptions(
            query="RAG system status",
            n_results=2,
            collection_name="rag_smoke",
            provider="hash",
            model_name="hash://sha256",
        )
    )
    logging.info("Query results:")
    for hit in query_result:
        logging.info("%s", hit)


if __name__ == "__main__":
    main()
