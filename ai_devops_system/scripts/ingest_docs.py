#!/usr/bin/env python3
"""
Command-line entry point for RAG ingestion.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from rag.service import IngestionOptions, RagService

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RAG ingestion CLI")
    parser.add_argument(
        "--paths",
        nargs="+",
        default=[".."],
        help="Paths to ingest (defaults to repo root)",
    )
    parser.add_argument(
        "--pattern",
        action="append",
        dest="patterns",
        help="Glob pattern (repeatable). Default covers md/py/ts/json files.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=int(os.getenv("INGEST_CHUNK_SIZE", 1000)),
        help="Chunk size in characters (default 1000)",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=int(os.getenv("INGEST_CHUNK_OVERLAP", 200)),
        help="Overlap between chunks (default 200)",
    )
    parser.add_argument(
        "--provider",
        default=os.getenv("EMBED_PROVIDER", "sentence-transformers"),
        help="Embedding provider",
    )
    parser.add_argument(
        "--model-name",
        default=os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2"),
        help="Embedding model name",
    )
    parser.add_argument(
        "--collection",
        default=os.getenv("RAG_COLLECTION", "local_docs"),
        help="Chroma collection name",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate the collection before ingesting",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        help="Limit the number of files ingested (useful for smoke tests)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.getenv("INGEST_BATCH_SIZE", 64)),
        help="Embedding batch size",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    service = RagService()
    options = IngestionOptions(
        paths=args.paths,
        glob_patterns=args.patterns or None,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        provider=args.provider,
        model_name=args.model_name,
        collection_name=args.collection,
        batch_size=args.batch_size,
        reset=args.reset,
        max_files=args.max_files,
    )
    result = service.ingest(options)
    logging.info("Ingestion summary: %s", result)


if __name__ == "__main__":
    main()
