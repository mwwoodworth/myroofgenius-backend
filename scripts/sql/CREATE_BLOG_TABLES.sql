-- Create REAL blog system tables
-- Persistent storage for blog posts, not in-memory

-- Blog posts table
CREATE TABLE IF NOT EXISTS blog_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Post content
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    excerpt TEXT,
    content TEXT NOT NULL,
    content_html TEXT, -- Rendered HTML
    
    -- Author info
    author_id UUID,
    author_name VARCHAR(255) DEFAULT 'MyRoofGenius Team',
    author_avatar VARCHAR(500),
    
    -- Categorization
    category VARCHAR(100) NOT NULL,
    tags JSONB DEFAULT '[]'::jsonb,
    
    -- Media
    featured_image VARCHAR(500),
    image_alt_text VARCHAR(255),
    images JSONB DEFAULT '[]'::jsonb,
    
    -- SEO
    meta_title VARCHAR(255),
    meta_description TEXT,
    canonical_url VARCHAR(500),
    
    -- Statistics
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    read_time_minutes INTEGER DEFAULT 5,
    
    -- Publishing
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'scheduled', 'archived')),
    published_at TIMESTAMPTZ,
    scheduled_for TIMESTAMPTZ,
    
    -- Flags
    is_featured BOOLEAN DEFAULT false,
    is_pinned BOOLEAN DEFAULT false,
    allow_comments BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Blog categories table
CREATE TABLE IF NOT EXISTS blog_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id UUID REFERENCES blog_categories(id),
    post_count INTEGER DEFAULT 0,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Blog comments table
CREATE TABLE IF NOT EXISTS blog_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES blog_posts(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES blog_comments(id),
    
    -- Commenter info
    user_id UUID,
    author_name VARCHAR(100) NOT NULL,
    author_email VARCHAR(255),
    author_website VARCHAR(500),
    
    -- Comment content
    content TEXT NOT NULL,
    
    -- Moderation
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'spam', 'deleted')),
    is_pinned BOOLEAN DEFAULT false,
    
    -- Statistics
    like_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMPTZ
);

-- Blog subscribers table
CREATE TABLE IF NOT EXISTS blog_subscribers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    
    -- Preferences
    categories JSONB DEFAULT '[]'::jsonb,
    frequency VARCHAR(20) DEFAULT 'weekly' CHECK (frequency IN ('daily', 'weekly', 'monthly')),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    verification_token VARCHAR(255),
    
    -- Statistics
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,
    
    -- Timestamps
    subscribed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMPTZ,
    unsubscribed_at TIMESTAMPTZ
);

-- Blog post likes table (for tracking who liked what)
CREATE TABLE IF NOT EXISTS blog_post_likes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES blog_posts(id) ON DELETE CASCADE,
    user_id UUID,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id, user_id),
    UNIQUE(post_id, ip_address)
);

-- Related posts junction table
CREATE TABLE IF NOT EXISTS blog_related_posts (
    post_id UUID NOT NULL REFERENCES blog_posts(id) ON DELETE CASCADE,
    related_post_id UUID NOT NULL REFERENCES blog_posts(id) ON DELETE CASCADE,
    relevance_score DECIMAL(3,2) DEFAULT 0.5,
    PRIMARY KEY (post_id, related_post_id)
);

-- Create indexes for performance
CREATE INDEX idx_blog_posts_slug ON blog_posts(slug);
CREATE INDEX idx_blog_posts_status ON blog_posts(status);
CREATE INDEX idx_blog_posts_published_at ON blog_posts(published_at DESC);
CREATE INDEX idx_blog_posts_category ON blog_posts(category);
CREATE INDEX idx_blog_posts_author ON blog_posts(author_id);
CREATE INDEX idx_blog_posts_featured ON blog_posts(is_featured) WHERE is_featured = true;

CREATE INDEX idx_blog_comments_post_id ON blog_comments(post_id);
CREATE INDEX idx_blog_comments_status ON blog_comments(status);

CREATE INDEX idx_blog_subscribers_email ON blog_subscribers(email);
CREATE INDEX idx_blog_subscribers_active ON blog_subscribers(is_active) WHERE is_active = true;

-- Full text search indexes
CREATE INDEX idx_blog_posts_search ON blog_posts 
    USING GIN(to_tsvector('english', title || ' ' || COALESCE(content, '') || ' ' || COALESCE(excerpt, '')));

CREATE INDEX idx_blog_posts_tags ON blog_posts USING GIN(tags);

-- Update triggers
CREATE OR REPLACE FUNCTION update_blog_post_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_TABLE_NAME = 'blog_comments' THEN
        UPDATE blog_posts 
        SET comment_count = (
            SELECT COUNT(*) FROM blog_comments 
            WHERE post_id = NEW.post_id AND status = 'approved'
        )
        WHERE id = NEW.post_id;
    ELSIF TG_TABLE_NAME = 'blog_post_likes' THEN
        UPDATE blog_posts 
        SET like_count = (
            SELECT COUNT(*) FROM blog_post_likes 
            WHERE post_id = NEW.post_id
        )
        WHERE id = NEW.post_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_post_comment_count
    AFTER INSERT OR UPDATE OR DELETE ON blog_comments
    FOR EACH ROW
    EXECUTE FUNCTION update_blog_post_stats();

CREATE TRIGGER update_post_like_count
    AFTER INSERT OR DELETE ON blog_post_likes
    FOR EACH ROW
    EXECUTE FUNCTION update_blog_post_stats();

-- Insert initial categories
INSERT INTO blog_categories (name, slug, description) VALUES
('Roofing Tips', 'roofing-tips', 'Expert advice and tips for roofing projects'),
('Industry News', 'industry-news', 'Latest news and updates from the roofing industry'),
('How-To Guides', 'how-to-guides', 'Step-by-step guides for DIY and professional roofers'),
('Product Reviews', 'product-reviews', 'In-depth reviews of roofing products and tools'),
('Case Studies', 'case-studies', 'Real-world roofing project case studies'),
('Technology', 'technology', 'Roofing technology and innovation');

-- Insert sample blog posts with REAL content
INSERT INTO blog_posts (
    title, slug, excerpt, content, category, tags, 
    featured_image, status, published_at, is_featured
) VALUES
('The Complete Guide to Choosing the Right Roofing Material for Your Climate',
 'complete-guide-choosing-roofing-material-climate',
 'Learn how to select the perfect roofing material based on your local climate conditions. From hot deserts to snowy mountains, we cover it all.',
 E'# Choosing the Right Roofing Material for Your Climate\n\nYour roof is your home''s first line of defense against the elements. Choosing the right roofing material for your specific climate isn''t just about aesthetics—it''s about performance, longevity, and protection.\n\n## Hot and Dry Climates\n\nIn areas like Arizona or Southern California, you need materials that reflect heat and withstand UV radiation:\n\n- **Clay or Concrete Tiles**: Excellent heat reflection, long-lasting\n- **Metal Roofing**: Reflects solar radiant heat, reducing cooling costs by 10-25%\n- **Cool Roof Shingles**: Special granules reflect more sunlight\n\n## Cold and Snowy Climates\n\nFor regions with heavy snow and freezing temperatures:\n\n- **Asphalt Shingles**: Good snow shedding, affordable\n- **Metal Roofing**: Snow slides off easily, prevents ice dams\n- **Slate**: Extremely durable, handles freeze-thaw cycles well\n\n## Wet and Humid Climates\n\nIn areas with high rainfall and humidity:\n\n- **Metal Roofing**: Excellent water shedding, resists mold\n- **Synthetic Slate**: Waterproof, lighter than real slate\n- **Architectural Shingles**: Multiple layers provide better water protection\n\n## High Wind Areas\n\nFor hurricane-prone or windy regions:\n\n- **Metal Roofing**: Can withstand winds up to 140 mph\n- **Impact-Resistant Shingles**: Class 4 rated for hail and debris\n- **Concrete Tiles**: Heavy weight resists uplift\n\n## Making Your Decision\n\nConsider these factors:\n1. Local building codes and HOA requirements\n2. Your budget (initial cost vs. lifetime value)\n3. Energy efficiency goals\n4. Maintenance requirements\n5. Warranty coverage\n\n## Conclusion\n\nThe right roofing material can save you thousands in energy costs and repairs. Consult with local roofing professionals who understand your area''s specific challenges.',
 'How-To Guides',
 '["climate", "materials", "buying guide", "asphalt", "metal", "tile", "slate"]'::jsonb,
 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64',
 'published',
 CURRENT_TIMESTAMP - INTERVAL '2 days',
 true),

('5 Signs Your Roof Needs Immediate Attention',
 '5-signs-roof-needs-immediate-attention',
 'Don''t wait for a leak! Learn to spot these critical warning signs that your roof needs professional inspection or repair.',
 E'# 5 Signs Your Roof Needs Immediate Attention\n\nYour roof might be trying to tell you something. Here are five critical signs that require immediate professional attention:\n\n## 1. Missing or Damaged Shingles\n\n**What to look for:**\n- Shingles on the ground after storms\n- Visible gaps in your roof line\n- Cracked, curled, or buckled shingles\n\n**Why it matters:** Missing shingles expose your roof deck to water damage, leading to leaks and structural issues.\n\n## 2. Granules in Gutters\n\n**What to look for:**\n- Sandy, grain-like particles in gutters\n- Bald spots on shingles\n- Excessive granule accumulation\n\n**Why it matters:** Granules protect shingles from UV rays. Loss indicates aging and reduced protection.\n\n## 3. Sagging Roof Deck\n\n**What to look for:**\n- Visible dips or curves in roof line\n- Soft spots when walking on roof\n- Interior ceiling sagging\n\n**Why it matters:** Indicates structural damage, possibly from water infiltration or inadequate support.\n\n## 4. Light in the Attic\n\n**What to look for:**\n- Daylight visible through roof boards\n- Water stains on attic floor\n- Wet insulation\n\n**Why it matters:** If light gets in, so does water. This indicates holes that need immediate repair.\n\n## 5. Sudden Spike in Energy Bills\n\n**What to look for:**\n- Unexplained increase in heating/cooling costs\n- Drafts in upper floors\n- Inconsistent temperatures\n\n**Why it matters:** Poor roof ventilation or damaged insulation affects energy efficiency.\n\n## Take Action Now\n\nIf you notice any of these signs:\n1. Document with photos\n2. Contact a professional roofer immediately\n3. Check if covered by insurance\n4. Don''t attempt DIY repairs on serious issues\n\nRemember: Early detection saves money and prevents catastrophic damage!',
 'Roofing Tips',
 '["maintenance", "inspection", "warning signs", "repairs", "emergency"]'::jsonb,
 'https://images.unsplash.com/photo-1632170426960-9bab5d05ec9e',
 'published',
 CURRENT_TIMESTAMP - INTERVAL '5 days',
 false),

('How AI is Revolutionizing the Roofing Industry in 2024',
 'ai-revolutionizing-roofing-industry-2024',
 'Discover how artificial intelligence is transforming roofing from estimates to installation, making projects faster and more accurate.',
 E'# How AI is Revolutionizing the Roofing Industry in 2024\n\nThe roofing industry is experiencing a technological revolution, with AI leading the charge. Here''s how artificial intelligence is transforming every aspect of roofing:\n\n## AI-Powered Roof Inspections\n\n**Drone + AI Analysis:**\n- Automated damage detection\n- 3D roof modeling\n- Accurate measurements within 98% accuracy\n- Complete inspection in under 30 minutes\n\n## Instant Accurate Estimates\n\n**Machine Learning Benefits:**\n- Historical data analysis for pricing\n- Material quantity calculations\n- Labor hour predictions\n- Weather pattern integration\n\n## Predictive Maintenance\n\n**AI Forecasting:**\n- Predict roof lifespan\n- Schedule preventive maintenance\n- Alert for potential issues\n- Optimize repair timing\n\n## Customer Service Revolution\n\n**AI Chatbots and Assistants:**\n- 24/7 customer support\n- Instant quote generation\n- Appointment scheduling\n- Follow-up automation\n\n## Smart Material Selection\n\n**AI Recommendations Based On:**\n- Local climate data\n- Building specifications\n- Budget constraints\n- Energy efficiency goals\n\n## Real-World Results\n\nCompanies using AI report:\n- 40% reduction in estimate time\n- 25% improvement in accuracy\n- 35% increase in customer satisfaction\n- 20% reduction in material waste\n\n## The Future is Here\n\nAI isn''t replacing roofers—it''s empowering them to work smarter, safer, and more efficiently. Early adopters are already seeing competitive advantages.\n\n## Getting Started with AI\n\n1. Start with AI estimation tools\n2. Implement drone inspections\n3. Use AI-powered CRM systems\n4. Train your team on new technologies\n\nThe roofing industry''s future is bright, and AI is lighting the way!',
 'Technology',
 '["AI", "technology", "innovation", "drones", "automation", "future"]'::jsonb,
 'https://images.unsplash.com/photo-1677442136019-21780ecad995',
 'published',
 CURRENT_TIMESTAMP - INTERVAL '1 week',
 true);

-- Grant permissions
GRANT ALL ON blog_posts TO postgres;
GRANT ALL ON blog_categories TO postgres;
GRANT ALL ON blog_comments TO postgres;
GRANT ALL ON blog_subscribers TO postgres;
GRANT ALL ON blog_post_likes TO postgres;
GRANT ALL ON blog_related_posts TO postgres;

-- Verify blog system
SELECT 
    'Posts' as entity,
    COUNT(*) as count
FROM blog_posts
WHERE status = 'published'
UNION ALL
SELECT 
    'Categories' as entity,
    COUNT(*) as count
FROM blog_categories
UNION ALL
SELECT 
    'Subscribers' as entity,
    COUNT(*) as count
FROM blog_subscribers;