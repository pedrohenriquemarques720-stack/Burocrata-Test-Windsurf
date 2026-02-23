-- =====================================================
-- ESQUEMA: burocrata_ecosystem
-- POSTGRESQL 15+ | UUID v4 | BCrypt | LGPD Compliant
-- =====================================================

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- 1. TABELA DE USUÁRIOS (CORE)
-- =====================================================
CREATE TABLE users (
    -- Identificador UUID (não sequencial por segurança)
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Dados básicos
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    document_number VARCHAR(20), -- CPF/CNPJ mascarado/cifrado
    phone VARCHAR(20),
    
    -- Autenticação (BCrypt)
    password_hash VARCHAR(255) NOT NULL,
    last_login TIMESTAMP WITH TIME ZONE,
    
    -- Status da conta
    account_status VARCHAR(20) NOT NULL DEFAULT 'active'
        CONSTRAINT valid_account_status 
        CHECK (account_status IN ('active', 'suspended', 'blocked', 'pending_verification')),
    
    -- Controle de versão e timestamps (LGPD Art. 18)
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete (LGPD)
    
    -- Metadados
    user_metadata JSONB DEFAULT '{}'::jsonb, -- Dados flexíveis
    last_activity TIMESTAMP WITH TIME ZONE,
    
    -- Índices de performance
    CONSTRAINT email_lowercase_check CHECK (email = lower(email))
);

-- Índices estratégicos
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(account_status);
CREATE INDEX idx_users_created ON users(created_at);
CREATE INDEX idx_users_deleted ON users(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_document ON users(document_number) WHERE document_number IS NOT NULL;

-- Trigger para atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_users_timestamp
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 2. PERFIS E PERMISSÕES (RBAC)
-- =====================================================
CREATE TABLE roles (
    role_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_name VARCHAR(50) NOT NULL UNIQUE,
    role_level INTEGER NOT NULL DEFAULT 0, -- Hierarquia
    description TEXT,
    is_system_role BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE permissions (
    permission_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    permission_code VARCHAR(100) NOT NULL UNIQUE,
    resource VARCHAR(100) NOT NULL, -- Ex: 'contracts', 'payments', 'users'
    action VARCHAR(50) NOT NULL, -- Ex: 'create', 'read', 'update', 'delete', 'approve'
    description TEXT,
    CONSTRAINT valid_action CHECK (action IN ('create', 'read', 'update', 'delete', 'approve', 'manage', 'audit'))
);

CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(role_id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(permission_id) ON DELETE CASCADE,
    granted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    granted_by UUID REFERENCES users(user_id),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_roles (
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(role_id) ON DELETE CASCADE,
    granted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    granted_by UUID REFERENCES users(user_id),
    expires_at TIMESTAMP WITH TIME ZONE, -- Para permissões temporárias
    PRIMARY KEY (user_id, role_id)
);

-- Índices RBAC
CREATE INDEX idx_user_roles_user ON user_roles(user_id);
CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);

-- População inicial de roles
INSERT INTO roles (role_name, role_level, description, is_system_role) VALUES
    ('super_admin', 100, 'Acesso total ao sistema', true),
    ('admin', 80, 'Administração geral', true),
    ('compliance_officer', 70, 'Auditoria e conformidade', true),
    ('enterprise_manager', 50, 'Gestão de contas corporativas', true),
    ('premium_user', 20, 'Usuário premium', true),
    ('free_user', 10, 'Usuário gratuito', true),
    ('viewer', 5, 'Apenas visualização', true);

-- =====================================================
-- 3. CONSENTIMENTOS LGPD
-- =====================================================
CREATE TABLE consent_terms (
    term_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    term_type VARCHAR(50) NOT NULL, -- 'privacy_policy', 'terms_of_use', 'marketing'
    version VARCHAR(20) NOT NULL,
    content TEXT NOT NULL, -- Pode ser URL ou texto
    effective_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(term_type, version)
);

CREATE TABLE user_consents (
    consent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    term_id UUID NOT NULL REFERENCES consent_terms(term_id),
    ip_address INET,
    user_agent TEXT,
    consented_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE, -- Para revogação de consentimento
    consent_method VARCHAR(50) DEFAULT 'web_form', -- 'web_form', 'api', 'admin'
    UNIQUE(user_id, term_id, revoked_at)
);

CREATE INDEX idx_user_consents_user ON user_consents(user_id);
CREATE INDEX idx_user_consents_active ON user_consents(user_id) WHERE revoked_at IS NULL;

-- =====================================================
-- 4. LOGS DE AUDITORIA (AUDIT TRAIL)
-- =====================================================
CREATE TABLE audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    event_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Quem
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    session_id UUID,
    ip_address INET,
    user_agent TEXT,
    
    -- O que
    event_type VARCHAR(50) NOT NULL, -- 'login', 'logout', 'data_change', 'permission_change', 'payment'
    event_action VARCHAR(100) NOT NULL,
    
    -- Onde
    resource_type VARCHAR(50), -- 'contract', 'profile', 'subscription'
    resource_id UUID,
    
    -- Detalhes
    old_data JSONB,
    new_data JSONB,
    changes JSONB,
    http_method VARCHAR(10),
    endpoint VARCHAR(255),
    status_code INTEGER,
    
    -- Metadados
    severity VARCHAR(20) DEFAULT 'info' 
        CHECK (severity IN ('info', 'warning', 'critical')),
    audit_metadata JSONB DEFAULT '{}'::jsonb
);

-- Índices de auditoria (performance crítica)
CREATE INDEX idx_audit_user_time ON audit_logs(user_id, event_time DESC);
CREATE INDEX idx_audit_event_time ON audit_logs(event_time DESC);
CREATE INDEX idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_ip ON audit_logs(ip_address);
CREATE INDEX idx_audit_severity ON audit_logs(severity);

-- Tabela para logins específicos
CREATE TABLE login_history (
    login_id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    login_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    logout_time TIMESTAMP WITH TIME ZONE,
    ip_address INET NOT NULL,
    user_agent TEXT,
    device_fingerprint VARCHAR(255),
    geo_location JSONB, -- Dados de geolocalização (cidade/país)
    login_success BOOLEAN NOT NULL DEFAULT true,
    failure_reason VARCHAR(100),
    session_duration INTERVAL GENERATED ALWAYS AS (logout_time - login_time) STORED,
    
    -- Detecção de anomalias
    is_suspicious BOOLEAN DEFAULT false,
    suspicion_score INTEGER DEFAULT 0,
    suspicion_reason TEXT
);

CREATE INDEX idx_login_user_time ON login_history(user_id, login_time DESC);
CREATE INDEX idx_login_ip ON login_history(ip_address);
CREATE INDEX idx_login_suspicious ON login_history(is_suspicious) WHERE is_suspicious;

-- =====================================================
-- 5. ASSINATURAS (SUBSCRIPTIONS)
-- =====================================================
CREATE TABLE plans (
    plan_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_code VARCHAR(50) NOT NULL UNIQUE, -- 'free', 'premium', 'enterprise'
    plan_name VARCHAR(100) NOT NULL,
    plan_type VARCHAR(20) NOT NULL 
        CHECK (plan_type IN ('free', 'paid', 'trial', 'custom')),
    price_cent DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'BRL',
    billing_cycle VARCHAR(20) -- 'monthly', 'yearly', 'one_time'
        CHECK (billing_cycle IN ('monthly', 'yearly', 'quarterly', 'one_time', 'none')),
    
    -- Features (JSON flexível)
    features JSONB NOT NULL DEFAULT '{}'::jsonb,
    max_users INTEGER DEFAULT 1,
    max_contracts INTEGER,
    max_storage_mb INTEGER,
    
    -- Controle
    is_public BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    plan_id UUID NOT NULL REFERENCES plans(plan_id),
    
    -- Período
    start_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    end_date TIMESTAMP WITH TIME ZONE,
    trial_end_date TIMESTAMP WITH TIME ZONE,
    
    -- Status
    status VARCHAR(30) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'canceled', 'expired', 'past_due', 'trialing', 'incomplete')),
    
    -- Pagamento
    payment_provider VARCHAR(50), -- 'stripe', 'mercadopago', 'abacatepay'
    payment_id VARCHAR(255),
    payment_method VARCHAR(50),
    auto_renew BOOLEAN DEFAULT true,
    cancellation_reason TEXT,
    canceled_at TIMESTAMP WITH TIME ZONE,
    
    -- Controle
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_end_date ON subscriptions(end_date) WHERE end_date IS NOT NULL;
CREATE INDEX idx_subscriptions_active ON subscriptions(user_id) WHERE status = 'active';

CREATE TABLE subscription_history (
    history_id BIGSERIAL PRIMARY KEY,
    subscription_id UUID NOT NULL REFERENCES subscriptions(subscription_id) ON DELETE CASCADE,
    previous_status VARCHAR(30),
    new_status VARCHAR(30) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    changed_by UUID REFERENCES users(user_id),
    reason TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Trigger de subscriptions updated_at
CREATE TRIGGER trigger_update_subscriptions_timestamp
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- População inicial de planos
INSERT INTO plans (plan_code, plan_name, plan_type, price_cent, billing_cycle, features, max_users, max_contracts) VALUES
    ('free', 'Burocrata Free', 'free', 0, 'none', '{"analises": 3, "historico": 30, "suporte": "email"}', 1, 10),
    ('premium', 'Burocrata Premium', 'paid', 29.90, 'monthly', '{"analises": 100, "historico": 365, "suporte": "prioritario", "api": true}', 1, 100),
    ('enterprise', 'Burocrata Enterprise', 'paid', 199.90, 'monthly', '{"analises": "ilimitado", "historico": "ilimitado", "suporte": "vip", "api": true, "multi_user": true, "auditoria": true}', 10, 1000);

-- =====================================================
-- 6. FUNÇÕES DE SEGURANÇA E MANUTENÇÃO
-- =====================================================

-- Função para limpeza de dados (LGPD - direito ao esquecimento)
CREATE OR REPLACE FUNCTION anonimize_user(user_uuid UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE users SET
        email = 'deleted_' || user_id || '@anon.burocrata',
        full_name = '[DELETED]',
        document_number = NULL,
        phone = NULL,
        password_hash = crypt('DELETED_' || gen_random_uuid()::text, gen_salt('bf')),
        account_status = 'blocked',
        deleted_at = NOW(),
        user_metadata = '{"deleted": true, "deleted_at": "' || NOW()::text || '"}'::jsonb
    WHERE user_id = user_uuid;
    
    -- Anonimizar logs de auditoria
    UPDATE audit_logs SET
        user_id = NULL,
        ip_address = NULL,
        user_agent = NULL
    WHERE user_id = user_uuid;
    
    -- Manter apenas metadados anonimizados
    UPDATE login_history SET
        user_id = NULL,
        ip_address = NULL,
        user_agent = NULL,
        device_fingerprint = NULL
    WHERE user_id = user_uuid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Função para detectar logins suspeitos
CREATE OR REPLACE FUNCTION check_suspicious_login()
RETURNS TRIGGER AS $$
BEGIN
    -- Verificar múltiplas tentativas de diferentes IPs
    IF EXISTS (
        SELECT 1 FROM login_history 
        WHERE user_id = NEW.user_id 
        AND login_time > NOW() - INTERVAL '1 hour'
        AND ip_address != NEW.ip_address
        GROUP BY user_id HAVING COUNT(DISTINCT ip_address) > 3
    ) THEN
        NEW.is_suspicious := true;
        NEW.suspicion_score := 70;
        NEW.suspicion_reason := 'Múltiplos IPs em curto período';
    END IF;
    
    -- Verificar geolocalização impossível
    IF EXISTS (
        SELECT 1 FROM login_history 
        WHERE user_id = NEW.user_id 
        AND login_time > NOW() - INTERVAL '2 hours'
        AND geo_location->>'country' != NEW.geo_location->>'country'
    ) THEN
        NEW.is_suspicious := true;
        NEW.suspicion_score := 90;
        NEW.suspicion_reason := 'Viagem impossível entre países';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_suspicious_login
    BEFORE INSERT ON login_history
    FOR EACH ROW
    EXECUTE FUNCTION check_suspicious_login();

-- =====================================================
-- 7. VIEWS PARA RELATÓRIOS
-- =====================================================

CREATE VIEW user_security_summary AS
SELECT 
    u.user_id,
    u.email,
    u.account_status,
    COUNT(DISTINCT lh.login_id) as total_logins,
    MAX(lh.login_time) as last_login,
    COUNT(DISTINCT CASE WHEN lh.is_suspicious THEN lh.login_id END) as suspicious_logins,
    ARRAY_AGG(DISTINCT r.role_name) as roles,
    uc.consent_active
FROM users u
LEFT JOIN login_history lh ON u.user_id = lh.user_id
LEFT JOIN user_roles ur ON u.user_id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.role_id
LEFT JOIN LATERAL (
    SELECT bool_and(revoked_at IS NULL) as consent_active
    FROM user_consents 
    WHERE user_id = u.user_id
) uc ON true
GROUP BY u.user_id, u.email, u.account_status, uc.consent_active;

-- =====================================================
-- PERMISSÕES E SEGURANÇA ADICIONAL
-- =====================================================

-- Revogar permissões públicas
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;

-- Criar roles de aplicação
CREATE ROLE app_user;
CREATE ROLE app_admin;
CREATE ROLE audit_viewer;

-- Conceder permissões específicas
GRANT SELECT, INSERT, UPDATE ON users TO app_user;
GRANT SELECT, INSERT ON audit_logs TO app_user;
GRANT SELECT, INSERT ON login_history TO app_user;
GRANT SELECT, INSERT ON user_consents TO app_user;
GRANT SELECT ON plans TO app_user;
GRANT SELECT, INSERT, UPDATE ON subscriptions TO app_user;

-- Admin tem acesso total
GRANT ALL ON ALL TABLES IN SCHEMA public TO app_admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO app_admin;

-- Auditoria (somente leitura)
GRANT SELECT ON audit_logs, login_history TO audit_viewer;