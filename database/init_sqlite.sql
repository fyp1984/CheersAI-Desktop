-- CheersAI SQLite Database Schema
-- SQLite version adapted from PostgreSQL schema

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- ============================================================================
-- 8.1.1 用户表 (users)
-- ============================================================================
CREATE TABLE users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    email TEXT UNIQUE NOT NULL,
    phone TEXT UNIQUE,
    username TEXT NOT NULL,
    nickname TEXT,
    avatar_url TEXT,
    password_hash TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deleted')),
    email_verified INTEGER DEFAULT 0,
    phone_verified INTEGER DEFAULT 0,
    last_login_at TEXT,
    last_login_ip TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_created_at ON users(created_at);

-- ============================================================================
-- 8.1.2 产品表 (products)
-- ============================================================================
CREATE TABLE products (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    name TEXT NOT NULL,
    code TEXT UNIQUE NOT NULL,
    description TEXT,
    icon_url TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'deprecated')),
    current_version TEXT,
    download_urls TEXT, -- JSON string
    settings TEXT DEFAULT '{}', -- JSON string
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_products_code ON products(code);
CREATE INDEX idx_products_status ON products(status);

-- ============================================================================
-- 8.1.3 会员计划表 (membership_plans)
-- ============================================================================
CREATE TABLE membership_plans (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    price_monthly REAL,
    price_yearly REAL,
    currency TEXT DEFAULT 'CNY',
    features TEXT NOT NULL, -- JSON string
    limits TEXT NOT NULL, -- JSON string
    sort_order INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_membership_plans_code ON membership_plans(code);
CREATE INDEX idx_membership_plans_status ON membership_plans(status);

-- 初始化会员等级
INSERT INTO membership_plans (code, name, price_monthly, price_yearly, features, limits) VALUES
('free', 'Free', 0, 0, '{"basic_features": true}', '{"agents": 3, "knowledge_bases": 1, "api_calls_daily": 100}'),
('pro', 'Pro', 29, 299, '{"basic_features": true, "advanced_features": true}', '{"agents": 20, "knowledge_bases": 10, "api_calls_daily": 1000}'),
('team', 'Team', 99, 999, '{"basic_features": true, "advanced_features": true, "team_features": true}', '{"agents": 100, "knowledge_bases": 50, "api_calls_daily": 5000}'),
('enterprise', 'Enterprise', NULL, NULL, '{"all_features": true}', '{"agents": -1, "knowledge_bases": -1, "api_calls_daily": -1}');

-- ============================================================================
-- 8.1.4 用户订阅表 (subscriptions)
-- ============================================================================
CREATE TABLE subscriptions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_code TEXT NOT NULL REFERENCES membership_plans(code),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled')),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    auto_renew INTEGER DEFAULT 0,
    payment_method TEXT,
    last_payment_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_end_date ON subscriptions(end_date);
CREATE INDEX idx_subscriptions_plan_code ON subscriptions(plan_code);

-- ============================================================================
-- 8.1.5 审计日志表 (audit_logs)
-- ============================================================================
CREATE TABLE audit_logs (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    log_type TEXT NOT NULL,
    action TEXT NOT NULL,
    operator_id TEXT REFERENCES users(id),
    operator_name TEXT,
    target_type TEXT,
    target_id TEXT,
    before_data TEXT, -- JSON string
    after_data TEXT, -- JSON string
    ip_address TEXT,
    user_agent TEXT,
    result TEXT DEFAULT 'success',
    error_message TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_audit_logs_type ON audit_logs(log_type);
CREATE INDEX idx_audit_logs_operator ON audit_logs(operator_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_target ON audit_logs(target_type, target_id);
CREATE INDEX idx_audit_logs_result ON audit_logs(result);

-- ============================================================================
-- 8.1.6 用户反馈表 (feedbacks)
-- ============================================================================
CREATE TABLE feedbacks (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id TEXT REFERENCES products(id),
    type TEXT NOT NULL CHECK (type IN ('bug', 'feature', 'question', 'other')),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    attachments TEXT DEFAULT '[]', -- JSON string
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'resolved', 'closed')),
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    assignee_id TEXT REFERENCES users(id),
    resolved_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_feedbacks_user_id ON feedbacks(user_id);
CREATE INDEX idx_feedbacks_status ON feedbacks(status);
CREATE INDEX idx_feedbacks_created_at ON feedbacks(created_at);
CREATE INDEX idx_feedbacks_type ON feedbacks(type);
CREATE INDEX idx_feedbacks_priority ON feedbacks(priority);

-- ============================================================================
-- 8.1.7 公告表 (announcements)
-- ============================================================================
CREATE TABLE announcements (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    target_products TEXT DEFAULT '[]', -- JSON array string
    target_users TEXT DEFAULT 'all',
    channels TEXT DEFAULT '["app"]', -- JSON array string
    priority TEXT DEFAULT 'normal',
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    publish_at TEXT,
    expire_at TEXT,
    created_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_announcements_status ON announcements(status);
CREATE INDEX idx_announcements_publish_at ON announcements(publish_at);
CREATE INDEX idx_announcements_type ON announcements(type);
CREATE INDEX idx_announcements_priority ON announcements(priority);

-- ============================================================================
-- 8.1.8 内测申请表 (beta_applications)
-- ============================================================================
CREATE TABLE beta_applications (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    email TEXT NOT NULL,
    name TEXT,
    company TEXT,
    use_case TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_beta_applications_email ON beta_applications(email);
CREATE INDEX idx_beta_applications_status ON beta_applications(status);
CREATE INDEX idx_beta_applications_created_at ON beta_applications(created_at);

-- ============================================================================
-- Triggers for updated_at timestamps
-- ============================================================================

-- Users table trigger
CREATE TRIGGER update_users_timestamp 
AFTER UPDATE ON users
BEGIN
    UPDATE users SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Products table trigger
CREATE TRIGGER update_products_timestamp 
AFTER UPDATE ON products
BEGIN
    UPDATE products SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Membership plans table trigger
CREATE TRIGGER update_membership_plans_timestamp 
AFTER UPDATE ON membership_plans
BEGIN
    UPDATE membership_plans SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Subscriptions table trigger
CREATE TRIGGER update_subscriptions_timestamp 
AFTER UPDATE ON subscriptions
BEGIN
    UPDATE subscriptions SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Feedbacks table trigger
CREATE TRIGGER update_feedbacks_timestamp 
AFTER UPDATE ON feedbacks
BEGIN
    UPDATE feedbacks SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Announcements table trigger
CREATE TRIGGER update_announcements_timestamp 
AFTER UPDATE ON announcements
BEGIN
    UPDATE announcements SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Beta applications table trigger
CREATE TRIGGER update_beta_applications_timestamp 
AFTER UPDATE ON beta_applications
BEGIN
    UPDATE beta_applications SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- ============================================================================
-- Views for common queries
-- ============================================================================

-- Active subscriptions view
CREATE VIEW v_active_subscriptions AS
SELECT 
    s.*,
    u.email,
    u.username,
    mp.name as plan_name,
    mp.features,
    mp.limits
FROM subscriptions s
JOIN users u ON s.user_id = u.id
JOIN membership_plans mp ON s.plan_code = mp.code
WHERE s.status = 'active' 
AND date(s.end_date) >= date('now');

-- User feedback summary view
CREATE VIEW v_feedback_summary AS
SELECT 
    f.*,
    u.username as user_name,
    u.email as user_email,
    p.name as product_name,
    a.username as assignee_name
FROM feedbacks f
JOIN users u ON f.user_id = u.id
LEFT JOIN products p ON f.product_id = p.id
LEFT JOIN users a ON f.assignee_id = a.id;

-- Published announcements view
CREATE VIEW v_published_announcements AS
SELECT 
    a.*,
    u.username as creator_name
FROM announcements a
JOIN users u ON a.created_by = u.id
WHERE a.status = 'published'
AND (a.publish_at IS NULL OR datetime(a.publish_at) <= datetime('now'))
AND (a.expire_at IS NULL OR datetime(a.expire_at) > datetime('now'))
ORDER BY a.publish_at DESC;
