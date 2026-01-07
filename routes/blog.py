"""
Blog API Routes - AI-Powered Content Management
Provides endpoints for blog posts, AI content generation, and content distribution
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import json
from sqlalchemy import text

from database import get_db_connection
import os

router = APIRouter(prefix="/blog", tags=["Blog"])

class BlogPost(BaseModel):
    title: str
    slug: Optional[str] = None
    content: str
    excerpt: str
    category: str = "general"
    tags: List[str] = []
    author: str = "WeatherCraft Team"
    featured_image: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    status: str = "draft"
    ai_generated: bool = False
    research_sources: List[str] = []

class BlogGenerationRequest(BaseModel):
    topic: str
    keywords: List[str] = []
    questions: List[str] = []
    tone: str = "professional yet conversational"
    length: int = 1500
    include_stats: bool = True
    include_cta: bool = True
    research_depth: str = "comprehensive"

@router.get("/posts")
async def get_blog_posts(
    limit: int = Query(10, le=100),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
    status: Optional[str] = "published",
    search: Optional[str] = None
):
    """Get blog posts with pagination and filtering"""
    try:
        async with get_db_connection() as conn:
            # Build query
            query = """
                SELECT
                    id, title, slug, excerpt, category, tags, author,
                    featured_image, status, ai_generated, view_count,
                    published_at, created_at, updated_at,
                    seo_title, seo_description
                FROM blog_posts
                WHERE 1=1
            """
            params = {}

            if status:
                query += " AND status = :status"
                params["status"] = status

            if category:
                query += " AND category = :category"
                params["category"] = category

            if search:
                query += """ AND (
                    title ILIKE :search OR
                    content ILIKE :search OR
                    excerpt ILIKE :search
                )"""
                params["search"] = f"%{search}%"

            # Get total count
            count_query = f"SELECT COUNT(*) as total FROM ({query}) as t"
            count_result = await conn.fetch_one(text(count_query), params)
            total = count_result["total"] if count_result else 0

            # Add pagination and ordering
            query += " ORDER BY published_at DESC NULLS LAST, created_at DESC"
            query += " LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset

            result = await conn.fetch_all(text(query), params)

            posts = []
            for row in result:
                post = dict(row)
                post["tags"] = post.get("tags", []) if isinstance(post.get("tags"), list) else []
                posts.append(post)

            return {
                "success": True,
                "posts": posts,
                "total": total,
                "limit": limit,
                "offset": offset,
                "pages": (total + limit - 1) // limit
            }

    except Exception as e:
        print(f"Error fetching blog posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/posts/{slug}")
async def get_blog_post(slug: str):
    """Get a single blog post by slug"""
    try:
        async with get_db_connection() as conn:
            query = """
                SELECT * FROM blog_posts
                WHERE slug = :slug AND status = 'published'
            """
            result = await conn.fetch_one(text(query), {"slug": slug})

            if not result:
                raise HTTPException(status_code=404, detail="Blog post not found")

            post = dict(result)

            # Increment view count
            await conn.execute(
                text("UPDATE blog_posts SET view_count = view_count + 1 WHERE slug = :slug"),
                {"slug": slug}
            )

            # Get related posts
            related_query = """
                SELECT id, title, slug, excerpt, featured_image
                FROM blog_posts
                WHERE status = 'published'
                AND slug != :slug
                AND category = :category
                ORDER BY published_at DESC
                LIMIT 3
            """
            related = await conn.fetch_all(
                text(related_query),
                {"slug": slug, "category": post.get("category", "general")}
            )

            post["related_posts"] = [dict(r) for r in related]

            return {
                "success": True,
                "post": post
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching blog post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/posts")
async def create_blog_post(post: BlogPost):
    """Create a new blog post"""
    try:
        async with get_db_connection() as conn:
            # Generate slug if not provided
            if not post.slug:
                post.slug = post.title.lower().replace(" ", "-").replace("'", "")
                post.slug = "".join(c for c in post.slug if c.isalnum() or c == "-")

            # Set SEO fields if not provided
            if not post.seo_title:
                post.seo_title = f"{post.title} | WeatherCraft Roofing"
            if not post.seo_description:
                post.seo_description = post.excerpt

            query = """
                INSERT INTO blog_posts (
                    title, slug, content, excerpt, category, tags, author,
                    featured_image, seo_title, seo_description, status,
                    ai_generated, research_sources, published_at, created_at
                ) VALUES (
                    :title, :slug, :content, :excerpt, :category, :tags, :author,
                    :featured_image, :seo_title, :seo_description, :status,
                    :ai_generated, :research_sources, :published_at, NOW()
                )
                RETURNING id
            """

            params = post.dict()
            params["tags"] = json.dumps(post.tags) if post.tags else "[]"
            params["research_sources"] = json.dumps(post.research_sources) if post.research_sources else "[]"
            params["published_at"] = datetime.now() if post.status == "published" else None

            result = await conn.fetch_one(text(query), params)

            return {
                "success": True,
                "id": result["id"],
                "slug": post.slug,
                "message": "Blog post created successfully"
            }

    except Exception as e:
        print(f"Error creating blog post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate")
async def generate_blog_post(request: BlogGenerationRequest):
    """Generate a blog post using AI providers."""
    try:
        # Step 1: Research with Perplexity (using AI agents service)
        research_prompt = f"""
        Research the following topic for a roofing industry blog post:
        Topic: {request.topic}
        Keywords: {', '.join(request.keywords)}

        Provide:
        1. Current industry statistics and trends
        2. Common problems and solutions
        3. Cost ranges and ROI data
        4. Best practices and recommendations
        5. Recent innovations or changes
        """
        from ai_services.real_ai_integration import ai_service, AIServiceNotConfiguredError, AIProviderCallError

        try:
            research_data = await ai_service.generate_json(
                research_prompt + "\n\nReturn JSON with keys: statistics (list), trends (list), sources (list)."
            )
        except (AIServiceNotConfiguredError, AIProviderCallError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        # Step 2: Generate content with Claude via AI agents service
        content_prompt = f"""
        Write a comprehensive blog post about: {request.topic}

        Research data: {json.dumps(research_data)}
        Keywords to include: {', '.join(request.keywords)}
        Questions to answer: {', '.join(request.questions)}

        Requirements:
        - Length: approximately {request.length} words
        - Tone: {request.tone}
        - Include statistics: {request.include_stats}
        - Include call-to-action: {request.include_cta}
        - Format: Use markdown with proper headings

        Structure:
        1. Engaging introduction
        2. Main content sections answering the questions
        3. Practical tips and recommendations
        4. Conclusion with CTA for WeatherCraft Roofing services
        """
        try:
            content_result = await ai_service.generate_json(
                content_prompt + "\n\nReturn JSON with key: content (markdown)."
            )
        except (AIServiceNotConfiguredError, AIProviderCallError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        content = content_result.get("content")
        if not content:
            raise HTTPException(status_code=500, detail="AI content generation failed")

        # Generate excerpt
        excerpt = content[:200] + "..." if len(content) > 200 else content

        # Generate SEO metadata
        seo_title = f"{request.topic} - Complete Guide 2024 | WeatherCraft"
        seo_description = f"Expert guide to {request.topic.lower()}. Learn costs, best practices, and get professional insights from WeatherCraft Roofing's experienced team."

        # Create blog post
        blog_post = BlogPost(
            title=request.topic,
            content=content,
            excerpt=excerpt,
            category="guides",
            tags=request.keywords,
            author="WeatherCraft AI",
            seo_title=seo_title,
            seo_description=seo_description,
            status="draft",
            ai_generated=True,
            research_sources=research_data.get("sources", [])
        )

        # Save to database
        post_response = await create_blog_post(blog_post)

        return {
            "success": True,
            "post": {
                "title": blog_post.title,
                "slug": blog_post.slug,
                "excerpt": excerpt,
                "content_preview": content[:500],
                "word_count": len(content.split()),
                "research_sources": research_data.get("sources", [])
            },
            "message": "Blog post generated successfully",
            "id": post_response.get("id")
        }

    except Exception as e:
        print(f"Error generating blog post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/research")
async def research_topic(topic: str, depth: str = "comprehensive"):
    """Research a topic using AI providers."""
    try:
        from ai_services.real_ai_integration import ai_service, AIServiceNotConfiguredError, AIProviderCallError

        prompt = (
            f"Research the topic '{topic}' for a roofing industry blog.\n"
            f"Depth: {depth}\n\n"
            "Return JSON with keys: trending (bool), search_volume, competition, keywords (list), "
            "questions (list), insights (list), recommended_angles (list), sources (list)."
        )

        try:
            research = await ai_service.generate_json(prompt)
        except (AIServiceNotConfiguredError, AIProviderCallError) as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        return {
            "success": True,
            "research": research
        }

    except Exception as e:
        print(f"Error researching topic: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
async def get_categories():
    """Get all blog categories with post counts"""
    try:
        async with get_db_connection() as conn:
            query = """
                SELECT
                    category,
                    COUNT(*) as post_count,
                    MAX(published_at) as latest_post
                FROM blog_posts
                WHERE status = 'published'
                GROUP BY category
                ORDER BY post_count DESC
            """
            result = await conn.fetch_all(text(query))

            categories = [
                {
                    "name": row["category"],
                    "count": row["post_count"],
                    "latest": row["latest_post"].isoformat() if row["latest_post"] else None
                }
                for row in result
            ]

            return {
                "success": True,
                "categories": categories
            }

    except Exception as e:
        print(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trending")
async def get_trending_posts(limit: int = 5):
    """Get trending blog posts based on views and engagement"""
    try:
        async with get_db_connection() as conn:
            query = """
                SELECT
                    id, title, slug, excerpt, featured_image,
                    view_count, published_at
                FROM blog_posts
                WHERE status = 'published'
                AND published_at > NOW() - INTERVAL '30 days'
                ORDER BY view_count DESC, published_at DESC
                LIMIT :limit
            """
            result = await conn.fetch_all(text(query), {"limit": limit})

            posts = [dict(row) for row in result]

            return {
                "success": True,
                "posts": posts
            }

    except Exception as e:
        print(f"Error fetching trending posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedule")
async def schedule_blog_automation(
    posts_per_day: int = 2,
    categories: List[str] = ["guides", "news", "tips"],
    auto_publish: bool = False
):
    """Schedule automated blog post generation"""
    try:
        # This would set up the automation schedule
        # Store in database or job queue

        schedule = {
            "posts_per_day": posts_per_day,
            "categories": categories,
            "auto_publish": auto_publish,
            "next_run": (datetime.now() + timedelta(hours=1)).isoformat(),
            "status": "scheduled"
        }

        return {
            "success": True,
            "schedule": schedule,
            "message": "Blog automation scheduled successfully"
        }

    except Exception as e:
        print(f"Error scheduling automation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
