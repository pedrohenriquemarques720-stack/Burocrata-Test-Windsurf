-- Criptografar dados sensíveis (pgcrypto)
UPDATE users SET 
    document_number = pgp_sym_encrypt(document_number, current_setting('app.encryption_key'));

-- Mascarar dados em logs
CREATE OR REPLACE FUNCTION mask_email(email TEXT) RETURNS TEXT AS $$
BEGIN
    RETURN regexp_replace(email, '(^.)(.*)(.@.*$)', '\1****\3');
END;
$$ LANGUAGE plpgsql;

-- Row Level Security (RLS) - PostgreSQL 9.5+
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_isolation ON users
    USING (user_id = current_setting('app.current_user_id')::UUID 
           OR current_setting('app.user_role') = 'admin');

-- Connection pooling com limites
-- Em produção: PgBouncer com pool_size = 20, max_client_conn = 100