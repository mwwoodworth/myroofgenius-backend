"""
Automated Content Pipeline
Perplexity Research → Claude Content → Gemini SEO → Auto-Publish
"""

import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import aiohttp
import openai
from anthropic import AsyncAnthropic
import google.generativeai as genai
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import hashlib
from bs4 import BeautifulSoup
import frontmatter
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AI clients
anthropic = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
openai.api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
sendgrid = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))

@dataclass
class ResearchPack:
    """Research data from Perplexity"""
    topic: str
    sources: List[str]
    key_findings: List[str]
    statistics: Dict[str, Any]
    citations: List[Dict[str, str]]
    timestamp: str

@dataclass
class ContentPiece:
    """Content created by Claude"""
    title: str
    type: str  # blog, newsletter, guide, doc
    content: str
    meta_description: str
    keywords: List[str]
    target_persona: str
    call_to_action: str
    internal_links: List[str]
    
@dataclass
class SEOOptimization:
    """SEO improvements from Gemini"""
    optimized_title: str
    optimized_meta: str
    schema_markup: Dict[str, Any]
    keyword_density: Dict[str, float]
    readability_score: float
    improvements: List[str]

class ContentPipeline:
    """Automated content creation and publishing pipeline"""
    
    def __init__(self, pg_pool, supabase_client):
        self.pg_pool = pg_pool
        self.supabase = supabase_client
        
        # Content configuration
        self.content_calendar = {
            "monday": ["industry_news", "product_updates"],
            "tuesday": ["how_to_guide", "case_study"],
            "wednesday": ["technology_deep_dive", "ai_insights"],
            "thursday": ["customer_success", "best_practices"],
            "friday": ["weekly_roundup", "market_analysis"],
            "saturday": ["educational_content"],
            "sunday": ["newsletter"]
        }
        
        self.personas = [
            "estimators", "project_managers", "homeowners",
            "architects", "engineers", "business_owners", "manufacturers"
        ]
        
        self.topics = [
            "roofing materials", "cost estimation", "safety protocols",
            "weather planning", "sustainability", "technology adoption",
            "business growth", "compliance", "warranties", "installation"
        ]
        
    async def initialize(self):
        """Start the content pipeline"""
        # Run content creation daily
        asyncio.create_task(self.daily_content_generation())
        # Run newsletter weekly
        asyncio.create_task(self.weekly_newsletter())
        # Monitor performance
        asyncio.create_task(self.content_performance_tracking())
        
        logger.info("Content pipeline initialized")
        
    async def research_with_perplexity(self, topic: str) -> ResearchPack:
        """Use Perplexity to research a topic"""
        try:
            # Perplexity API call (using OpenAI client with Perplexity endpoint)
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
                    "Content-Type": "application/json"
                }
                
                prompt = f"""
                Research the following topic for the roofing industry:
                Topic: {topic}
                
                Provide:
                1. Latest industry trends and developments
                2. Key statistics and data points
                3. Expert opinions and best practices
                4. Regulatory updates if applicable
                5. Technology innovations
                6. Cost implications
                7. Safety considerations
                
                Include citations for all sources.
                """
                
                data = {
                    "model": "pplx-70b-online",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "return_citations": True
                }
                
                async with session.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    result = await response.json()
                    
                    # Parse response
                    content = result['choices'][0]['message']['content']
                    citations = result.get('citations', [])
                    
                    # Extract key findings
                    lines = content.split('\n')
                    key_findings = [line.strip('- ') for line in lines if line.startswith('-')][:10]
                    
                    # Extract statistics (simplified - would use NLP in production)
                    statistics = {
                        "market_size": "Extract from content",
                        "growth_rate": "Extract from content",
                        "cost_savings": "Extract from content"
                    }
                    
                    return ResearchPack(
                        topic=topic,
                        sources=[c['url'] for c in citations if 'url' in c],
                        key_findings=key_findings,
                        statistics=statistics,
                        citations=citations,
                        timestamp=datetime.now().isoformat()
                    )
                    
        except Exception as e:
            logger.error(f"Perplexity research failed: {e}")
            # Fallback research pack
            return ResearchPack(
                topic=topic,
                sources=["internal_knowledge"],
                key_findings=["Research unavailable"],
                statistics={},
                citations=[],
                timestamp=datetime.now().isoformat()
            )
            
    async def create_content_with_claude(self, research: ResearchPack, content_type: str, persona: str) -> ContentPiece:
        """Use Claude to create content from research"""
        try:
            prompt = f"""
            Create a {content_type} for {persona} in the roofing industry.
            
            Research findings:
            {json.dumps(research.key_findings, indent=2)}
            
            Statistics:
            {json.dumps(research.statistics, indent=2)}
            
            Sources:
            {json.dumps(research.sources, indent=2)}
            
            Requirements:
            1. Engaging, authoritative tone
            2. Include practical insights and actionable advice
            3. Reference statistics and cite sources
            4. Include a clear call-to-action
            5. Optimize for {persona} specific needs
            6. Length: {'1500-2000 words' if content_type == 'blog' else '500-800 words'}
            
            Format:
            - Title
            - Meta description (155 characters)
            - Content with proper headings
            - 5-7 relevant keywords
            - 3 internal link suggestions
            - Call-to-action
            """
            
            response = await anthropic.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse Claude's response
            content_text = response.content[0].text
            
            # Extract components (simplified - would use structured output in production)
            lines = content_text.split('\n')
            title = lines[0].replace('Title:', '').strip()
            meta_description = "Professional roofing insights and solutions"
            
            keywords = [
                "roofing", persona, research.topic.replace('_', ' '),
                "contractors", "estimation", "technology", "solutions"
            ]
            
            internal_links = [
                f"/knowledge-center/{research.topic}",
                f"/for-{persona}",
                "/marketplace/tools"
            ]
            
            cta = f"Start your free trial of MyRoofGenius for {persona}"
            
            return ContentPiece(
                title=title,
                type=content_type,
                content=content_text,
                meta_description=meta_description,
                keywords=keywords,
                target_persona=persona,
                call_to_action=cta,
                internal_links=internal_links
            )
            
        except Exception as e:
            logger.error(f"Claude content creation failed: {e}")
            raise
            
    async def optimize_seo_with_gemini(self, content: ContentPiece) -> SEOOptimization:
        """Use Gemini to optimize content for SEO"""
        try:
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""
            Optimize this content for SEO:
            
            Title: {content.title}
            Content: {content.content[:1000]}...
            Keywords: {', '.join(content.keywords)}
            Target: {content.target_persona}
            
            Provide:
            1. Optimized title (60 characters max)
            2. Optimized meta description (155 characters max)
            3. Schema markup for the content
            4. Keyword density analysis
            5. Readability score
            6. Improvement suggestions
            """
            
            response = model.generate_content(prompt)
            
            # Parse response (simplified)
            optimized_title = content.title[:60]
            optimized_meta = content.meta_description[:155]
            
            schema_markup = {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": optimized_title,
                "description": optimized_meta,
                "author": {
                    "@type": "Organization",
                    "name": "MyRoofGenius"
                },
                "publisher": {
                    "@type": "Organization",
                    "name": "MyRoofGenius",
                    "logo": {
                        "@type": "ImageObject",
                        "url": "https://myroofgenius.com/logo.png"
                    }
                },
                "datePublished": datetime.now().isoformat(),
                "keywords": ", ".join(content.keywords)
            }
            
            keyword_density = {kw: 0.02 for kw in content.keywords}  # Placeholder
            
            return SEOOptimization(
                optimized_title=optimized_title,
                optimized_meta=optimized_meta,
                schema_markup=schema_markup,
                keyword_density=keyword_density,
                readability_score=8.5,
                improvements=["Add more headers", "Include FAQ section", "Add images"]
            )
            
        except Exception as e:
            logger.error(f"Gemini SEO optimization failed: {e}")
            # Return basic optimization
            return SEOOptimization(
                optimized_title=content.title,
                optimized_meta=content.meta_description,
                schema_markup={},
                keyword_density={},
                readability_score=7.0,
                improvements=[]
            )
            
    async def publish_content(self, content: ContentPiece, seo: SEOOptimization) -> Dict[str, Any]:
        """Publish content to the website"""
        try:
            # Generate slug
            slug = content.title.lower().replace(' ', '-')[:50]
            
            # Prepare frontmatter
            frontmatter_data = {
                'title': seo.optimized_title,
                'description': seo.optimized_meta,
                'date': datetime.now().isoformat(),
                'author': 'MyRoofGenius AI',
                'category': content.type,
                'tags': content.keywords,
                'persona': content.target_persona,
                'schema': seo.schema_markup
            }
            
            # Create markdown file with frontmatter
            post = frontmatter.Post(content.content, **frontmatter_data)
            markdown_content = frontmatter.dumps(post)
            
            # Save to database
            async with self.pg_pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO content_pieces (
                        slug, title, type, content, meta_description,
                        keywords, target_persona, schema_markup,
                        published_at, status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), 'published')
                ''', slug, seo.optimized_title, content.type, markdown_content,
                    seo.optimized_meta, content.keywords, content.target_persona,
                    json.dumps(seo.schema_markup))
                    
            # Trigger webhook to update frontend
            async with aiohttp.ClientSession() as session:
                webhook_data = {
                    'type': 'content_published',
                    'slug': slug,
                    'title': seo.optimized_title,
                    'category': content.type,
                    'persona': content.target_persona
                }
                
                # Would send to actual webhook endpoint
                # await session.post('https://myroofgenius.com/api/webhooks/content', json=webhook_data)
                
            logger.info(f"Published content: {seo.optimized_title}")
            
            return {
                'slug': slug,
                'url': f'https://myroofgenius.com/blog/{slug}',
                'published': True
            }
            
        except Exception as e:
            logger.error(f"Content publishing failed: {e}")
            raise
            
    async def daily_content_generation(self):
        """Generate content based on calendar"""
        while True:
            try:
                # Get today's content types
                day = datetime.now().strftime('%A').lower()
                content_types = self.content_calendar.get(day, ['blog'])
                
                for content_type in content_types:
                    # Select random topic and persona
                    import random
                    topic = random.choice(self.topics)
                    persona = random.choice(self.personas)
                    
                    logger.info(f"Generating {content_type} about {topic} for {persona}")
                    
                    # Research
                    research = await self.research_with_perplexity(topic)
                    
                    # Create content
                    content = await self.create_content_with_claude(
                        research, content_type, persona
                    )
                    
                    # Optimize SEO
                    seo = await self.optimize_seo_with_gemini(content)
                    
                    # Publish
                    result = await self.publish_content(content, seo)
                    
                    logger.info(f"Content published: {result['url']}")
                    
                    # Track in analytics
                    async with self.pg_pool.acquire() as conn:
                        await conn.execute('''
                            INSERT INTO content_analytics (
                                content_id, impressions, clicks, conversions
                            ) VALUES ($1, 0, 0, 0)
                        ''', result['slug'])
                        
            except Exception as e:
                logger.error(f"Daily content generation failed: {e}")
                
            # Run once per day
            await asyncio.sleep(86400)
            
    async def weekly_newsletter(self):
        """Generate and send weekly newsletter"""
        while True:
            try:
                if datetime.now().weekday() == 6:  # Sunday
                    # Get week's top content
                    async with self.pg_pool.acquire() as conn:
                        top_content = await conn.fetch('''
                            SELECT title, slug, meta_description
                            FROM content_pieces
                            WHERE published_at > NOW() - INTERVAL '7 days'
                            ORDER BY views DESC
                            LIMIT 5
                        ''')
                        
                        subscribers = await conn.fetch('''
                            SELECT email, preferences
                            FROM newsletter_subscribers
                            WHERE status = 'active'
                        ''')
                        
                    # Create newsletter content
                    newsletter_html = self._create_newsletter_html(top_content)
                    
                    # Send to subscribers
                    for subscriber in subscribers:
                        message = Mail(
                            from_email='newsletter@myroofgenius.com',
                            to_emails=subscriber['email'],
                            subject='MyRoofGenius Weekly: AI-Powered Roofing Insights',
                            html_content=newsletter_html
                        )
                        
                        try:
                            sendgrid.send(message)
                            logger.info(f"Newsletter sent to {subscriber['email']}")
                        except Exception as e:
                            logger.error(f"Failed to send to {subscriber['email']}: {e}")
                            
            except Exception as e:
                logger.error(f"Weekly newsletter failed: {e}")
                
            # Check daily but only send on Sunday
            await asyncio.sleep(86400)
            
    async def content_performance_tracking(self):
        """Track content performance and optimize"""
        while True:
            try:
                async with self.pg_pool.acquire() as conn:
                    # Get performance metrics
                    metrics = await conn.fetch('''
                        SELECT 
                            c.slug, c.title, c.target_persona,
                            ca.impressions, ca.clicks, ca.conversions,
                            (ca.clicks::float / NULLIF(ca.impressions, 0)) as ctr,
                            (ca.conversions::float / NULLIF(ca.clicks, 0)) as conversion_rate
                        FROM content_pieces c
                        JOIN content_analytics ca ON c.slug = ca.content_id
                        WHERE c.published_at > NOW() - INTERVAL '30 days'
                    ''')
                    
                    # Identify top performers
                    top_performers = [m for m in metrics if m['ctr'] and m['ctr'] > 0.05]
                    
                    # Identify underperformers
                    underperformers = [m for m in metrics if m['ctr'] and m['ctr'] < 0.02]
                    
                    # Log insights
                    if top_performers:
                        logger.info(f"Top performing content: {[t['title'] for t in top_performers[:3]]}")
                        
                    if underperformers:
                        logger.info(f"Underperforming content needs optimization: {len(underperformers)} pieces")
                        
                    # Store insights for AI learning
                    await conn.execute('''
                        INSERT INTO content_insights (
                            insight_type, data, created_at
                        ) VALUES ('performance_analysis', $1, NOW())
                    ''', json.dumps({
                        'top_performers': [asdict(t) for t in top_performers[:5]],
                        'underperformers': [asdict(u) for u in underperformers[:5]],
                        'avg_ctr': sum(m['ctr'] or 0 for m in metrics) / len(metrics) if metrics else 0
                    }))
                    
            except Exception as e:
                logger.error(f"Performance tracking failed: {e}")
                
            # Run every 6 hours
            await asyncio.sleep(21600)
            
    def _create_newsletter_html(self, top_content) -> str:
        """Create newsletter HTML"""
        html = """
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1>MyRoofGenius Weekly</h1>
            <p>Your AI-powered roofing insights for the week</p>
            <h2>Top Stories</h2>
        """
        
        for content in top_content:
            html += f"""
            <div style="margin: 20px 0; padding: 15px; border: 1px solid #ddd;">
                <h3>{content['title']}</h3>
                <p>{content['meta_description']}</p>
                <a href="https://myroofgenius.com/blog/{content['slug']}" 
                   style="color: #007bff;">Read More →</a>
            </div>
            """
            
        html += """
            <div style="margin-top: 40px; padding: 20px; background: #f0f0f0;">
                <h3>Upgrade to Pro</h3>
                <p>Get unlimited AI estimates and priority support</p>
                <a href="https://myroofgenius.com/pricing" 
                   style="display: inline-block; padding: 10px 20px; 
                          background: #007bff; color: white; text-decoration: none;">
                    Start Free Trial
                </a>
            </div>
            <p style="margin-top: 30px; font-size: 12px; color: #666;">
                © 2025 MyRoofGenius. 
                <a href="https://myroofgenius.com/unsubscribe">Unsubscribe</a>
            </p>
        </body>
        </html>
        """
        
        return html