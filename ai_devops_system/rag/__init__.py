"""
RAG (Retrieval-Augmented Generation) package

This module exposes the core RagService along with ingestion and query options.
"""

from .service import RagService, IngestionOptions, QueryOptions

__all__ = ["RagService", "IngestionOptions", "QueryOptions"]
