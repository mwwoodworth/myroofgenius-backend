"""
Job Documents Management
Handles document upload, storage, and retrieval for jobs
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
import os
import shutil
from pathlib import Path

from database import get_db
from core.supabase_auth import get_current_user  # SUPABASE AUTH
from pydantic import BaseModel, Field

router = APIRouter(prefix="/documents")

# Document upload directory
UPLOAD_DIR = Path("uploads/job_documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class DocumentMetadata(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = Field(None, pattern="^(contract|estimate|invoice|photo|permit|inspection|warranty|other)$")
    tags: Optional[List[str]] = []
    is_public: bool = False

class DocumentResponse(BaseModel):
    id: str
    job_id: str
    name: str
    file_path: str
    file_size: int
    mime_type: str
    category: Optional[str]
    description: Optional[str]
    tags: List[str]
    is_public: bool
    uploaded_by: str
    uploaded_at: datetime
    download_count: int

# ============================================================================
# JOB DOCUMENTS ENDPOINTS
# ============================================================================

@router.post("/{job_id}/documents", response_model=DocumentResponse)
async def upload_job_document(
    job_id: str,
    file: UploadFile = File(...),
    metadata: DocumentMetadata = Depends(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document for a job"""
    try:
        # Verify job exists
        job = db.execute(
            text("SELECT id FROM jobs WHERE id = :id"),
            {"id": job_id}
        ).fetchone()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        # Generate unique filename
        document_id = str(uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        stored_filename = f"{document_id}{file_extension}"
        file_path = UPLOAD_DIR / job_id / stored_filename

        # Create job directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Get file size
        file_size = file_path.stat().st_size

        # Store metadata in database
        result = db.execute(
            text("""
                INSERT INTO job_documents (
                    id, job_id, name, file_path, file_size,
                    mime_type, category, description, tags,
                    is_public, uploaded_by, uploaded_at
                )
                VALUES (
                    :id, :job_id, :name, :file_path, :file_size,
                    :mime_type, :category, :description, :tags::jsonb,
                    :is_public, :uploaded_by, NOW()
                )
                RETURNING *
            """),
            {
                "id": document_id,
                "job_id": job_id,
                "name": metadata.name or file.filename,
                "file_path": str(file_path),
                "file_size": file_size,
                "mime_type": file.content_type,
                "category": metadata.category,
                "description": metadata.description,
                "tags": str(metadata.tags or []),
                "is_public": metadata.is_public,
                "uploaded_by": current_user["id"]
            }
        )
        db.commit()

        document = result.fetchone()
        return DocumentResponse(
            id=str(document.id),
            job_id=str(document.job_id),
            name=document.name,
            file_path=document.file_path,
            file_size=document.file_size,
            mime_type=document.mime_type,
            category=document.category,
            description=document.description,
            tags=document.tags or [],
            is_public=document.is_public,
            uploaded_by=str(document.uploaded_by),
            uploaded_at=document.uploaded_at,
            download_count=document.download_count or 0
        )

    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if database operation failed
        if file_path.exists():
            file_path.unlink()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

@router.get("/{job_id}/documents", response_model=Dict[str, Any])
async def list_job_documents(
    job_id: str,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all documents for a job"""
    try:
        # Build query
        query = """
            SELECT
                d.*,
                u.email as uploaded_by_email
            FROM job_documents d
            LEFT JOIN users u ON d.uploaded_by = u.id
            WHERE d.job_id = :job_id
        """
        params = {"job_id": job_id}

        if category:
            query += " AND d.category = :category"
            params["category"] = category

        if search:
            query += " AND (d.name ILIKE :search OR d.description ILIKE :search)"
            params["search"] = f"%{search}%"

        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) as cnt"
        total = db.execute(text(count_query), params).scalar()

        # Get documents
        query += " ORDER BY d.uploaded_at DESC LIMIT :limit OFFSET :offset"
        params.update({"limit": limit, "offset": offset})

        result = db.execute(text(query), params)
        documents = []

        for doc in result:
            documents.append({
                "id": str(doc.id),
                "job_id": str(doc.job_id),
                "name": doc.name,
                "file_size": doc.file_size,
                "mime_type": doc.mime_type,
                "category": doc.category,
                "description": doc.description,
                "tags": doc.tags or [],
                "is_public": doc.is_public,
                "uploaded_by": str(doc.uploaded_by),
                "uploaded_by_email": doc.uploaded_by_email,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "download_count": doc.download_count or 0
            })

        return {
            "total": total,
            "documents": documents,
            "limit": limit,
            "offset": offset
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )

@router.get("/{job_id}/documents/{document_id}")
async def get_document_info(
    job_id: str,
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document information"""
    try:
        result = db.execute(
            text("""
                SELECT
                    d.*,
                    u.email as uploaded_by_email
                FROM job_documents d
                LEFT JOIN users u ON d.uploaded_by = u.id
                WHERE d.id = :document_id AND d.job_id = :job_id
            """),
            {"document_id": document_id, "job_id": job_id}
        )

        document = result.fetchone()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        return {
            "id": str(document.id),
            "job_id": str(document.job_id),
            "name": document.name,
            "file_path": document.file_path,
            "file_size": document.file_size,
            "mime_type": document.mime_type,
            "category": document.category,
            "description": document.description,
            "tags": document.tags or [],
            "is_public": document.is_public,
            "uploaded_by": str(document.uploaded_by),
            "uploaded_by_email": document.uploaded_by_email,
            "uploaded_at": document.uploaded_at.isoformat(),
            "download_count": document.download_count or 0,
            "download_url": f"/api/v1/jobs/documents/{job_id}/documents/{document_id}/download"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )

@router.delete("/{job_id}/documents/{document_id}")
async def delete_job_document(
    job_id: str,
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a job document"""
    try:
        # Get document info
        result = db.execute(
            text("SELECT file_path FROM job_documents WHERE id = :id AND job_id = :job_id"),
            {"id": document_id, "job_id": job_id}
        )

        document = result.fetchone()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Delete from database
        db.execute(
            text("DELETE FROM job_documents WHERE id = :id"),
            {"id": document_id}
        )
        db.commit()

        # Delete file from filesystem
        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()

        return {"message": "Document deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

@router.post("/{job_id}/documents/bulk-upload")
async def bulk_upload_documents(
    job_id: str,
    files: List[UploadFile] = File(...),
    category: Optional[str] = Query(None, pattern="^(contract|estimate|invoice|photo|permit|inspection|warranty|other)$"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload multiple documents at once"""
    try:
        # Verify job exists
        job = db.execute(
            text("SELECT id FROM jobs WHERE id = :id"),
            {"id": job_id}
        ).fetchone()

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        uploaded_documents = []
        failed_uploads = []

        for file in files:
            try:
                # Generate unique filename
                document_id = str(uuid4())
                file_extension = os.path.splitext(file.filename)[1]
                stored_filename = f"{document_id}{file_extension}"
                file_path = UPLOAD_DIR / job_id / stored_filename

                # Create job directory if it doesn't exist
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Save file
                with file_path.open("wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                # Get file size
                file_size = file_path.stat().st_size

                # Store metadata in database
                db.execute(
                    text("""
                        INSERT INTO job_documents (
                            id, job_id, name, file_path, file_size,
                            mime_type, category, uploaded_by, uploaded_at
                        )
                        VALUES (
                            :id, :job_id, :name, :file_path, :file_size,
                            :mime_type, :category, :uploaded_by, NOW()
                        )
                    """),
                    {
                        "id": document_id,
                        "job_id": job_id,
                        "name": file.filename,
                        "file_path": str(file_path),
                        "file_size": file_size,
                        "mime_type": file.content_type,
                        "category": category,
                        "uploaded_by": current_user["id"]
                    }
                )

                uploaded_documents.append({
                    "id": document_id,
                    "name": file.filename,
                    "size": file_size
                })

            except Exception as e:
                failed_uploads.append({
                    "name": file.filename,
                    "error": str(e)
                })

        db.commit()

        return {
            "uploaded": uploaded_documents,
            "failed": failed_uploads,
            "total_uploaded": len(uploaded_documents),
            "total_failed": len(failed_uploads)
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload documents: {str(e)}"
        )

@router.get("/{job_id}/document-summary")
async def get_document_summary(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary statistics for job documents"""
    try:
        result = db.execute(
            text("""
                SELECT
                    COUNT(*) as total_documents,
                    COALESCE(SUM(file_size), 0) as total_size,
                    COUNT(DISTINCT category) as categories_used,
                    COUNT(*) FILTER (WHERE is_public = true) as public_documents,
                    COUNT(*) FILTER (WHERE uploaded_at > NOW() - INTERVAL '7 days') as recent_uploads,
                    COALESCE(SUM(download_count), 0) as total_downloads
                FROM job_documents
                WHERE job_id = :job_id
            """),
            {"job_id": job_id}
        )

        summary = result.fetchone()

        # Get category breakdown
        category_result = db.execute(
            text("""
                SELECT
                    category,
                    COUNT(*) as count,
                    COALESCE(SUM(file_size), 0) as total_size
                FROM job_documents
                WHERE job_id = :job_id AND category IS NOT NULL
                GROUP BY category
                ORDER BY count DESC
            """),
            {"job_id": job_id}
        )

        categories = []
        for cat in category_result:
            categories.append({
                "category": cat.category,
                "count": cat.count,
                "total_size": cat.total_size
            })

        return {
            "total_documents": summary.total_documents,
            "total_size_bytes": summary.total_size,
            "total_size_mb": round(summary.total_size / (1024 * 1024), 2) if summary.total_size else 0,
            "categories_used": summary.categories_used,
            "public_documents": summary.public_documents,
            "recent_uploads": summary.recent_uploads,
            "total_downloads": summary.total_downloads,
            "category_breakdown": categories
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document summary: {str(e)} RETURNING *"
        )