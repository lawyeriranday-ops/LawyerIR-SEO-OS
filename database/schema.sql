-- LawyerIR SEO OS — Database Schema (Phase 2)
-- PostgreSQL 15+

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users (future authentication)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Sites being monitored
CREATE TABLE IF NOT EXISTS sites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    url VARCHAR(512) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Page-level URLs for SEO analysis
CREATE TABLE IF NOT EXISTS urls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    path VARCHAR(512) NOT NULL,
    full_url VARCHAR(1024) NOT NULL UNIQUE,
    title VARCHAR(512),
    meta_description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    last_crawled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (site_id, path),
    CHECK (status IN ('active', 'inactive', 'redirect'))
);

-- SEO audit runs (page-level)
CREATE TABLE IF NOT EXISTS audits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url_id UUID NOT NULL REFERENCES urls(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    score INTEGER,
    summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    CHECK (score IS NULL OR (score >= 0 AND score <= 100))
);

-- Keywords tracked per site
CREATE TABLE IF NOT EXISTS keywords (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    target_url_id UUID REFERENCES urls(id) ON DELETE SET NULL,
    keyword VARCHAR(255) NOT NULL,
    search_volume INTEGER,
    position NUMERIC(5, 2),
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    ctr NUMERIC(5, 4),
    intent VARCHAR(20),
    priority VARCHAR(10) NOT NULL DEFAULT 'medium',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (site_id, keyword),
    CHECK (intent IS NULL OR intent IN ('informational', 'navigational', 'transactional', 'commercial')),
    CHECK (priority IN ('low', 'medium', 'high')),
    CHECK (ctr IS NULL OR (ctr >= 0 AND ctr <= 1))
);

-- Generated reports
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    audit_id UUID REFERENCES audits(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sites_owner_id ON sites(owner_id);
CREATE INDEX IF NOT EXISTS idx_urls_site_id ON urls(site_id);
CREATE INDEX IF NOT EXISTS idx_audits_url_id ON audits(url_id);
CREATE INDEX IF NOT EXISTS idx_keywords_site_id ON keywords(site_id);
CREATE INDEX IF NOT EXISTS idx_keywords_target_url_id ON keywords(target_url_id);
CREATE INDEX IF NOT EXISTS idx_keywords_priority ON keywords(priority);
CREATE INDEX IF NOT EXISTS idx_reports_site_id ON reports(site_id);
CREATE INDEX IF NOT EXISTS idx_reports_audit_id ON reports(audit_id);

-- Auto-update sites.updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sites_updated_at
    BEFORE UPDATE ON sites
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_urls_updated_at
    BEFORE UPDATE ON urls
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_keywords_updated_at
    BEFORE UPDATE ON keywords
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Seed default site and homepage URL
INSERT INTO sites (url, name)
VALUES ('https://lawyerir.com', 'LawyerIR')
ON CONFLICT (url) DO NOTHING;

INSERT INTO urls (site_id, path, full_url, title, status)
SELECT id, '/', 'https://lawyerir.com/', 'LawyerIR', 'active'
FROM sites WHERE url = 'https://lawyerir.com'
ON CONFLICT (full_url) DO NOTHING;
