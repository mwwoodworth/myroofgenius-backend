-- Recruitment Management Tables
-- Task 44: Recruitment and applicant tracking system

-- Job postings table
CREATE TABLE IF NOT EXISTS job_postings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    department VARCHAR(100) NOT NULL,
    location VARCHAR(200) NOT NULL,
    job_type VARCHAR(20) NOT NULL, -- full_time, part_time, contract, temporary, intern, freelance
    experience_level VARCHAR(20) NOT NULL, -- entry, mid, senior, lead, executive
    min_salary DECIMAL(12,2),
    max_salary DECIMAL(12,2),
    description TEXT NOT NULL,
    requirements JSONB, -- Array of requirements
    responsibilities JSONB, -- Array of responsibilities
    benefits JSONB, -- Array of benefits
    skills_required JSONB, -- Array of required skills
    skills_preferred JSONB, -- Array of preferred skills
    remote_allowed BOOLEAN DEFAULT false,
    visa_sponsorship BOOLEAN DEFAULT false,
    hiring_manager_id UUID NOT NULL,
    target_hire_date DATE,
    positions_available INT DEFAULT 1,
    positions_filled INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft', -- draft, open, on_hold, closed, cancelled
    posted_date TIMESTAMPTZ,
    closed_date TIMESTAMPTZ,
    applications_count INT DEFAULT 0,
    views_count INT DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Candidates table
CREATE TABLE IF NOT EXISTS candidates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(30),
    location VARCHAR(200),
    current_title VARCHAR(200),
    current_company VARCHAR(200),
    years_experience INT,
    education_level VARCHAR(50), -- high_school, associate, bachelor, master, doctorate
    linkedin_url TEXT,
    github_url TEXT,
    portfolio_url TEXT,
    website_url TEXT,
    resume_url TEXT,
    resume_text TEXT,
    skills JSONB, -- Array of skills
    languages JSONB, -- Array of languages
    certifications JSONB, -- Array of certifications
    source VARCHAR(30) NOT NULL, -- website, linkedin, indeed, referral, agency, job_board, career_fair, direct, other
    source_details VARCHAR(200),
    rating INT CHECK (rating >= 1 AND rating <= 5),
    tags JSONB, -- Array of tags
    is_active BOOLEAN DEFAULT true,
    blacklisted BOOLEAN DEFAULT false,
    blacklist_reason TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Applications table
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_number VARCHAR(50) UNIQUE NOT NULL,
    job_posting_id UUID NOT NULL REFERENCES job_postings(id),
    candidate_id UUID NOT NULL REFERENCES candidates(id),
    cover_letter TEXT,
    expected_salary DECIMAL(12,2),
    available_start_date DATE,
    willing_to_relocate BOOLEAN DEFAULT false,
    requires_visa BOOLEAN DEFAULT false,
    referral_employee_id UUID,
    referral_notes TEXT,
    status VARCHAR(30) DEFAULT 'new', -- new, screening, phone_screen, interview, assessment, reference_check, offer, rejected, withdrawn, hired
    stage_updated_at TIMESTAMPTZ,
    score INT,
    ranking INT,
    rejection_reason TEXT,
    withdrawal_reason TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(job_posting_id, candidate_id)
);

-- Interviews table
CREATE TABLE IF NOT EXISTS interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id),
    interview_type VARCHAR(20) NOT NULL, -- phone, video, in_person, panel, technical, behavioral
    round_number INT DEFAULT 1,
    scheduled_date TIMESTAMPTZ NOT NULL,
    duration_minutes INT DEFAULT 60,
    location VARCHAR(200),
    room_number VARCHAR(50),
    meeting_link TEXT,
    dial_in_number VARCHAR(50),
    access_code VARCHAR(50),
    interviewers JSONB NOT NULL, -- Array of interviewer IDs
    interview_guide_url TEXT,
    instructions TEXT,
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, completed, cancelled, no_show, rescheduled
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    feedback TEXT,
    technical_score INT CHECK (technical_score >= 1 AND technical_score <= 5),
    cultural_fit_score INT CHECK (cultural_fit_score >= 1 AND cultural_fit_score <= 5),
    communication_score INT CHECK (communication_score >= 1 AND communication_score <= 5),
    overall_rating INT CHECK (overall_rating >= 1 AND overall_rating <= 5),
    strengths TEXT,
    concerns TEXT,
    recommendation VARCHAR(20), -- strong_yes, yes, maybe, no, strong_no
    completed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Interview feedback table
CREATE TABLE IF NOT EXISTS interview_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID NOT NULL REFERENCES interviews(id),
    interviewer_id UUID NOT NULL,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    technical_assessment TEXT,
    behavioral_assessment TEXT,
    strengths TEXT,
    weaknesses TEXT,
    recommendation VARCHAR(20), -- strong_yes, yes, maybe, no, strong_no
    would_work_with BOOLEAN,
    notes TEXT,
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Offers table
CREATE TABLE IF NOT EXISTS offers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    offer_number VARCHAR(50) UNIQUE NOT NULL,
    application_id UUID NOT NULL REFERENCES applications(id),
    position_title VARCHAR(200) NOT NULL,
    department VARCHAR(100) NOT NULL,
    employment_type VARCHAR(20) NOT NULL,
    salary DECIMAL(12,2) NOT NULL,
    bonus DECIMAL(12,2),
    signing_bonus DECIMAL(12,2),
    equity VARCHAR(100),
    commission_structure TEXT,
    start_date DATE NOT NULL,
    work_location VARCHAR(200),
    remote_work_allowed BOOLEAN DEFAULT false,
    benefits JSONB NOT NULL, -- Array of benefits
    vacation_days INT,
    sick_days INT,
    conditions JSONB, -- Array of conditions (background check, drug test, etc.)
    expiry_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'draft', -- draft, pending_approval, approved, sent, negotiating, accepted, declined, withdrawn
    approval_chain JSONB, -- Array of approvers
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    sent_date TIMESTAMPTZ,
    sent_via VARCHAR(50), -- email, mail, in_person
    response_date TIMESTAMPTZ,
    negotiation_history JSONB, -- Array of negotiation rounds
    negotiation_notes TEXT,
    decline_reason TEXT,
    counter_offer JSONB,
    final_salary DECIMAL(12,2),
    final_bonus DECIMAL(12,2),
    final_equity VARCHAR(100),
    offer_letter_url TEXT,
    signed_offer_url TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Assessments table
CREATE TABLE IF NOT EXISTS assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id),
    assessment_type VARCHAR(50) NOT NULL, -- technical, personality, cognitive, skills, culture_fit
    assessment_name VARCHAR(200) NOT NULL,
    provider VARCHAR(100),
    platform_url TEXT,
    access_code VARCHAR(100),
    sent_date TIMESTAMPTZ NOT NULL,
    due_date TIMESTAMPTZ,
    reminder_sent BOOLEAN DEFAULT false,
    started_date TIMESTAMPTZ,
    completed_date TIMESTAMPTZ,
    time_spent_minutes INT,
    score DECIMAL(5,2),
    percentile INT,
    result JSONB, -- Detailed results
    passed BOOLEAN,
    report_url TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Reference checks table
CREATE TABLE IF NOT EXISTS reference_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id),
    reference_name VARCHAR(200) NOT NULL,
    reference_title VARCHAR(200),
    reference_company VARCHAR(200),
    reference_email VARCHAR(255),
    reference_phone VARCHAR(30),
    relationship VARCHAR(50), -- supervisor, peer, subordinate, client
    years_known INT,
    request_sent_date TIMESTAMPTZ,
    completed_date TIMESTAMPTZ,
    method VARCHAR(20), -- phone, email, letter
    verified_employment BOOLEAN,
    verified_title BOOLEAN,
    verified_dates BOOLEAN,
    would_rehire BOOLEAN,
    performance_rating INT CHECK (performance_rating >= 1 AND performance_rating <= 5),
    strengths TEXT,
    weaknesses TEXT,
    additional_comments TEXT,
    red_flags TEXT,
    conducted_by UUID,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Background checks table
CREATE TABLE IF NOT EXISTS background_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id),
    vendor VARCHAR(100),
    check_type VARCHAR(50), -- criminal, education, employment, credit, drug
    initiated_date DATE NOT NULL,
    completed_date DATE,
    status VARCHAR(20) DEFAULT 'pending', -- pending, in_progress, completed, failed
    result VARCHAR(20), -- clear, conditional, fail
    criminal_check BOOLEAN,
    criminal_result TEXT,
    education_verified BOOLEAN,
    education_notes TEXT,
    employment_verified BOOLEAN,
    employment_notes TEXT,
    credit_check BOOLEAN,
    credit_score INT,
    drug_test BOOLEAN,
    drug_test_result VARCHAR(20), -- negative, positive, inconclusive
    report_url TEXT,
    expires_date DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recruitment tasks table
CREATE TABLE IF NOT EXISTS recruitment_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id),
    task_type VARCHAR(50) NOT NULL, -- schedule_interview, send_assessment, check_references, prepare_offer, etc.
    title VARCHAR(200) NOT NULL,
    description TEXT,
    assigned_to UUID,
    due_date DATE,
    priority VARCHAR(10) DEFAULT 'normal', -- low, normal, high, urgent
    status VARCHAR(20) DEFAULT 'pending', -- pending, in_progress, completed, cancelled
    completed_date TIMESTAMPTZ,
    completed_by UUID,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recruitment notes table
CREATE TABLE IF NOT EXISTS recruitment_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(30) NOT NULL, -- application, candidate, interview
    entity_id UUID NOT NULL,
    note_type VARCHAR(30), -- general, screening, interview, reference, decision
    content TEXT NOT NULL,
    is_private BOOLEAN DEFAULT false,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recruitment email templates
CREATE TABLE IF NOT EXISTS recruitment_email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(100) UNIQUE NOT NULL,
    template_type VARCHAR(50) NOT NULL, -- application_received, interview_invite, rejection, offer, etc.
    subject VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    variables JSONB, -- List of variable placeholders
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recruitment pipelines table
CREATE TABLE IF NOT EXISTS recruitment_pipelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    stages JSONB NOT NULL, -- Array of stage definitions
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_job_postings_status ON job_postings(status);
CREATE INDEX IF NOT EXISTS idx_job_postings_department ON job_postings(department);
CREATE INDEX IF NOT EXISTS idx_job_postings_location ON job_postings(location);
CREATE INDEX IF NOT EXISTS idx_job_postings_posted_date ON job_postings(posted_date);
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_source ON candidates(source);
CREATE INDEX IF NOT EXISTS idx_candidates_created_at ON candidates(created_at);
CREATE INDEX IF NOT EXISTS idx_applications_job_posting ON applications(job_posting_id);
CREATE INDEX IF NOT EXISTS idx_applications_candidate ON applications(candidate_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_created_at ON applications(created_at);
CREATE INDEX IF NOT EXISTS idx_interviews_application ON interviews(application_id);
CREATE INDEX IF NOT EXISTS idx_interviews_scheduled_date ON interviews(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_interviews_status ON interviews(status);
CREATE INDEX IF NOT EXISTS idx_offers_application ON offers(application_id);
CREATE INDEX IF NOT EXISTS idx_offers_status ON offers(status);
CREATE INDEX IF NOT EXISTS idx_assessments_application ON assessments(application_id);
CREATE INDEX IF NOT EXISTS idx_reference_checks_application ON reference_checks(application_id);
CREATE INDEX IF NOT EXISTS idx_background_checks_application ON background_checks(application_id);
CREATE INDEX IF NOT EXISTS idx_recruitment_tasks_application ON recruitment_tasks(application_id);
CREATE INDEX IF NOT EXISTS idx_recruitment_tasks_assigned_to ON recruitment_tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_recruitment_tasks_status ON recruitment_tasks(status);
CREATE INDEX IF NOT EXISTS idx_recruitment_notes_entity ON recruitment_notes(entity_type, entity_id);

-- Functions
CREATE OR REPLACE FUNCTION calculate_time_to_hire(application_id UUID)
RETURNS INT AS $$
DECLARE
    start_date DATE;
    end_date DATE;
BEGIN
    SELECT created_at::DATE, updated_at::DATE
    INTO start_date, end_date
    FROM applications
    WHERE id = application_id AND status = 'hired';

    IF end_date IS NOT NULL THEN
        RETURN end_date - start_date;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_application_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE job_postings
        SET applications_count = applications_count + 1
        WHERE id = NEW.job_posting_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE job_postings
        SET applications_count = applications_count - 1
        WHERE id = OLD.job_posting_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_job_applications_count
AFTER INSERT OR DELETE ON applications
FOR EACH ROW
EXECUTE FUNCTION update_application_count();

-- Triggers
CREATE TRIGGER set_job_postings_updated_at
BEFORE UPDATE ON job_postings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_candidates_updated_at
BEFORE UPDATE ON candidates
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_applications_updated_at
BEFORE UPDATE ON applications
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_interviews_updated_at
BEFORE UPDATE ON interviews
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_offers_updated_at
BEFORE UPDATE ON offers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_assessments_updated_at
BEFORE UPDATE ON assessments
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_reference_checks_updated_at
BEFORE UPDATE ON reference_checks
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_background_checks_updated_at
BEFORE UPDATE ON background_checks
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_recruitment_tasks_updated_at
BEFORE UPDATE ON recruitment_tasks
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_recruitment_email_templates_updated_at
BEFORE UPDATE ON recruitment_email_templates
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER set_recruitment_pipelines_updated_at
BEFORE UPDATE ON recruitment_pipelines
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();