"""
RAG System Implementation for MyRoofGenius
Provides intelligent document retrieval and AI-powered responses
"""

import os
import asyncio
import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import asyncpg
import numpy as np
from openai import OpenAI
import httpx
from datetime import datetime
import hashlib
import re

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class RAGSystem:
    """
    Retrieval-Augmented Generation system for roofing knowledge
    """
    
    def __init__(self, pg_pool):
        self.pg_pool = pg_pool
        self.max_context_tokens = 4000  # Leave room for query and response
        self.similarity_threshold = 0.7
        self.max_retrieved_docs = 5
        
        # Initialize embedding cache
        self.embedding_cache = {}
        
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate OpenAI embedding for text"""
        # Check cache first
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.embedding_cache:
            return self.embedding_cache[text_hash]
            
        try:
            response = openai_client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            embedding = response.data[0].embedding
            
            # Cache the result
            self.embedding_cache[text_hash] = embedding
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 1536

    async def retrieve_documents(
        self, 
        query: str, 
        category: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using vector similarity search
        """
        start_time = time.time()
        
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            async with self.pg_pool.acquire() as conn:
                # Use the search function
                results = await conn.fetch('''
                    SELECT * FROM search_knowledge_base($1::vector, $2, $3, $4)
                ''', query_embedding, category, max_results, self.similarity_threshold)
                
                documents = []
                for row in results:
                    documents.append({
                        'id': str(row['id']),
                        'title': row['title'],
                        'content': row['content'],
                        'category': row['category'],
                        'subcategory': row['subcategory'],
                        'similarity_score': float(row['similarity_score']),
                        'metadata': row['metadata'],
                        'tags': list(row['tags']) if row['tags'] else []
                    })
                
                # Update access statistics
                if documents:
                    doc_ids = [doc['id'] for doc in documents]
                    await conn.execute('''
                        UPDATE knowledge_base 
                        SET view_count = view_count + 1,
                            last_accessed = NOW()
                        WHERE id = ANY($1::uuid[])
                    ''', doc_ids)
                
                retrieval_time = (time.time() - start_time) * 1000
                logger.info(f"Retrieved {len(documents)} documents in {retrieval_time:.2f}ms")
                
                return documents
                
        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            return []

    async def build_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Build context from retrieved documents for LLM
        """
        if not documents:
            return "No relevant documentation found."
            
        context_parts = []
        total_tokens = 0
        
        for i, doc in enumerate(documents):
            # Estimate token count (rough approximation)
            content_tokens = len(doc['content'].split()) * 1.3
            
            if total_tokens + content_tokens > self.max_context_tokens:
                break
                
            context_part = f"""
Document {i+1}: {doc['title']}
Category: {doc['category']} - {doc['subcategory']}
Similarity: {doc['similarity_score']:.3f}
Content: {doc['content']}
---"""
            
            context_parts.append(context_part)
            total_tokens += content_tokens
        
        return "\n".join(context_parts)

    async def classify_query_intent(self, query: str) -> str:
        """
        Classify the intent of the user query
        """
        query_lower = query.lower()
        
        # Simple rule-based classification (could be enhanced with ML)
        if any(word in query_lower for word in ['cost', 'price', 'estimate', 'budget']):
            return 'cost_estimation'
        elif any(word in query_lower for word in ['install', 'installation', 'how to']):
            return 'installation'
        elif any(word in query_lower for word in ['safety', 'osha', 'protection', 'hazard']):
            return 'safety'
        elif any(word in query_lower for word in ['material', 'shingle', 'metal', 'tile']):
            return 'materials'
        elif any(word in query_lower for word in ['code', 'regulation', 'compliance', 'permit']):
            return 'regulations'
        elif any(word in query_lower for word in ['repair', 'fix', 'damage', 'leak']):
            return 'repair'
        elif any(word in query_lower for word in ['design', 'plan', 'layout', 'structure']):
            return 'design'
        else:
            return 'general'

    async def generate_response(
        self,
        query: str,
        context: str,
        intent: str = 'general'
    ) -> Tuple[str, float]:
        """
        Generate AI response using retrieved context
        """
        start_time = time.time()
        
        try:
            # Build prompt based on intent
            system_prompt = self.build_system_prompt(intent)
            
            user_prompt = f"""
Query: {query}

Relevant Documentation:
{context}

Please provide a comprehensive, accurate answer based on the documentation above. 
If the documentation doesn't contain enough information, clearly state what's missing.
Include specific recommendations and best practices when applicable.
"""

            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for factual responses
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content
            response_time = (time.time() - start_time) * 1000
            
            # Simple quality scoring based on length and completeness
            quality_score = min(len(response_text) / 500, 1.0) * 0.8 + 0.2
            
            return response_text, quality_score
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again later.", 0.1

    def build_system_prompt(self, intent: str) -> str:
        """
        Build intent-specific system prompt
        """
        base_prompt = """You are MyRoofGenius AI, an expert roofing consultant with deep knowledge of:
- Roofing materials and installation techniques
- Building codes and regulations
- Cost estimation and project planning
- Safety protocols and OSHA requirements
- Repair and maintenance procedures

Provide accurate, practical advice based on industry best practices."""

        intent_specific = {
            'cost_estimation': """
Focus on providing detailed cost breakdowns, labor estimates, and material pricing.
Include factors that affect pricing and cost-saving recommendations.""",
            
            'installation': """
Provide step-by-step installation guidance with emphasis on proper techniques,
tool requirements, and quality checkpoints.""",
            
            'safety': """
Prioritize safety protocols, OSHA compliance, and hazard prevention.
Always emphasize proper safety equipment and procedures.""",
            
            'materials': """
Compare different material options with pros/cons, durability ratings,
and best-use scenarios for each type.""",
            
            'regulations': """
Focus on building code compliance, permit requirements, and regulatory standards.
Cite specific code sections when available."""
        }
        
        if intent in intent_specific:
            return f"{base_prompt}\n\n{intent_specific[intent]}"
        else:
            return base_prompt

    async def query_rag(
        self,
        query: str,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve, augment, generate
        """
        start_time = time.time()
        
        try:
            # Classify intent
            intent = await self.classify_query_intent(query)
            
            # Retrieve relevant documents
            documents = await self.retrieve_documents(query, category)
            
            # Build context
            context = await self.build_context(documents)
            
            # Generate response
            response_text, quality_score = await self.generate_response(query, context, intent)
            
            total_time = int((time.time() - start_time) * 1000)
            
            # Log interaction
            query_embedding = await self.generate_embedding(query)
            interaction_id = await self.log_interaction(
                query, query_embedding, intent, documents,
                context, response_text, total_time,
                user_id, session_id
            )
            
            return {
                'query': query,
                'response': response_text,
                'intent': intent,
                'documents_retrieved': len(documents),
                'similarity_scores': [doc['similarity_score'] for doc in documents],
                'response_time_ms': total_time,
                'quality_score': quality_score,
                'interaction_id': str(interaction_id),
                'sources': [
                    {
                        'title': doc['title'],
                        'category': doc['category'],
                        'similarity': doc['similarity_score']
                    }
                    for doc in documents[:3]  # Top 3 sources
                ]
            }
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return {
                'query': query,
                'response': "I'm sorry, I encountered an error processing your question. Please try again.",
                'intent': 'error',
                'error': str(e),
                'response_time_ms': int((time.time() - start_time) * 1000)
            }

    async def log_interaction(
        self,
        query: str,
        query_embedding: List[float],
        intent: str,
        documents: List[Dict],
        context: str,
        response: str,
        response_time: int,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Log RAG interaction for analytics
        """
        try:
            async with self.pg_pool.acquire() as conn:
                interaction_id = await conn.fetchval('''
                    SELECT log_rag_interaction($1, $2::vector, $3, $4, $5, $6, $7, $8, $9)
                ''', 
                query, query_embedding, intent,
                json.dumps([{
                    'id': doc['id'],
                    'title': doc['title'],
                    'similarity_score': doc['similarity_score']
                } for doc in documents]),
                context, response, response_time, user_id, session_id)
                
                return str(interaction_id)
                
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
            return "unknown"

    async def add_knowledge_document(
        self,
        title: str,
        content: str,
        category: str,
        subcategory: str = None,
        source: str = None,
        tags: List[str] = None,
        metadata: Dict = None
    ) -> str:
        """
        Add new document to knowledge base
        """
        try:
            # Generate embedding for content
            embedding = await self.generate_embedding(content)
            
            async with self.pg_pool.acquire() as conn:
                doc_id = await conn.fetchval('''
                    INSERT INTO knowledge_base (
                        title, content, category, subcategory, source,
                        embedding, tags, metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6::vector, $7, $8)
                    RETURNING id
                ''', 
                title, content, category, subcategory, source,
                embedding, tags or [], metadata or {})
                
                logger.info(f"Added knowledge document: {title}")
                return str(doc_id)
                
        except Exception as e:
            logger.error(f"Failed to add knowledge document: {e}")
            raise

    async def update_daily_metrics(self):
        """
        Update daily RAG performance metrics
        """
        try:
            async with self.pg_pool.acquire() as conn:
                await conn.execute('SELECT update_daily_rag_metrics()')
                logger.info("Updated daily RAG metrics")
        except Exception as e:
            logger.error(f"Failed to update daily metrics: {e}")

    async def get_rag_stats(self) -> Dict[str, Any]:
        """
        Get RAG system statistics
        """
        try:
            async with self.pg_pool.acquire() as conn:
                # Knowledge base stats
                kb_stats = await conn.fetchrow('''
                    SELECT 
                        COUNT(*) as total_documents,
                        COUNT(DISTINCT category) as categories,
                        AVG(quality_score) as avg_quality,
                        SUM(view_count) as total_views
                    FROM knowledge_base
                    WHERE is_active = true
                ''')
                
                # Recent interaction stats
                interaction_stats = await conn.fetchrow('''
                    SELECT 
                        COUNT(*) as total_queries,
                        AVG(response_time_ms) as avg_response_time,
                        AVG(response_quality_score) as avg_quality_score
                    FROM rag_interactions
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                ''')
                
                # Popular categories
                popular_categories = await conn.fetch('''
                    SELECT 
                        kb.category,
                        COUNT(*) as query_count
                    FROM rag_interactions ri
                    JOIN jsonb_array_elements(ri.retrieved_documents) doc ON true
                    JOIN knowledge_base kb ON kb.id = (doc->>'id')::uuid
                    WHERE ri.created_at >= NOW() - INTERVAL '7 days'
                    GROUP BY kb.category
                    ORDER BY query_count DESC
                    LIMIT 5
                ''')
                
                return {
                    'knowledge_base': dict(kb_stats) if kb_stats else {},
                    'interactions': dict(interaction_stats) if interaction_stats else {},
                    'popular_categories': [
                        {'category': row['category'], 'queries': row['query_count']}
                        for row in popular_categories
                    ],
                    'updated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get RAG stats: {e}")
            return {'error': str(e)}

# Global RAG system instance
rag_system = None

async def get_rag_system(pg_pool) -> RAGSystem:
    """Get the RAG system instance"""
    global rag_system
    if rag_system is None:
        rag_system = RAGSystem(pg_pool)
    return rag_system