-- Job documents management table
-- Stores document metadata and references for job-related files

-- Create job_documents table
CREATE TABLE IF NOT EXISTS job_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    category VARCHAR(50),
    description TEXT,
    tags JSONB DEFAULT '[]',
    is_public BOOLEAN DEFAULT FALSE,
    uploaded_by UUID,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    download_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP,
    version INTEGER DEFAULT 1,
    previous_version_id UUID,
    metadata JSONB DEFAULT '{}',
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (previous_version_id) REFERENCES job_documents(id) ON DELETE SET NULL
);

-- Create document access log table
CREATE TABLE IF NOT EXISTS document_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    accessed_by UUID,
    access_type VARCHAR(50), -- view, download, edit, delete
    ip_address VARCHAR(45),
    user_agent TEXT,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES job_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (accessed_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create document shares table for external sharing
CREATE TABLE IF NOT EXISTS document_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    share_token VARCHAR(255) UNIQUE NOT NULL,
    shared_by UUID,
    shared_with_email VARCHAR(255),
    expires_at TIMESTAMP,
    max_downloads INTEGER,
    download_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (document_id) REFERENCES job_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (shared_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_job_documents_job_id ON job_documents(job_id);
CREATE INDEX IF NOT EXISTS idx_job_documents_category ON job_documents(category);
CREATE INDEX IF NOT EXISTS idx_job_documents_uploaded_by ON job_documents(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_job_documents_uploaded_at ON job_documents(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_job_documents_is_public ON job_documents(is_public);

CREATE INDEX IF NOT EXISTS idx_document_access_log_document_id ON document_access_log(document_id);
CREATE INDEX IF NOT EXISTS idx_document_access_log_accessed_by ON document_access_log(accessed_by);
CREATE INDEX IF NOT EXISTS idx_document_access_log_accessed_at ON document_access_log(accessed_at DESC);

CREATE INDEX IF NOT EXISTS idx_document_shares_share_token ON document_shares(share_token);
CREATE INDEX IF NOT EXISTS idx_document_shares_document_id ON document_shares(document_id);
CREATE INDEX IF NOT EXISTS idx_document_shares_expires_at ON document_shares(expires_at);

-- Add trigger for download count update
CREATE OR REPLACE FUNCTION update_document_download_count()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.access_type = 'download' THEN
        UPDATE job_documents
        SET download_count = download_count + 1,
            last_accessed = NOW()
        WHERE id = NEW.document_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_download_count
    AFTER INSERT ON document_access_log
    FOR EACH ROW
    EXECUTE FUNCTION update_document_download_count();

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON job_documents TO authenticated;
GRANT SELECT, INSERT ON document_access_log TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON document_shares TO authenticated;