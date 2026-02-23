-- Triggers de auditoria automática
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (
        user_id, event_type, event_action, resource_type, 
        resource_id, old_data, new_data, ip_address
    ) VALUES (
        current_setting('app.current_user_id')::UUID,
        TG_OP,
        TG_TABLE_NAME,
        TG_TABLE_NAME,
        NEW.user_id,
        row_to_json(OLD),
        row_to_json(NEW),
        inet_client_addr()
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Alertas de anomalias (via pg_cron ou agendador externo)
CREATE OR REPLACE FUNCTION detect_anomalies()
RETURNS TABLE (
    anomaly_type TEXT,
    user_id UUID,
    description TEXT,
    severity TEXT
) AS $$
BEGIN
    -- Múltiplas tentativas de login
    RETURN QUERY
    SELECT 
        'multiple_failed_logins',
        user_id,
        COUNT(*)::TEXT || ' tentativas em 5 minutos',
        'high'
    FROM login_history
    WHERE login_success = false
    AND login_time > NOW() - INTERVAL '5 minutes'
    GROUP BY user_id
    HAVING COUNT(*) > 5;
    
    -- Acessos de locais suspeitos
    RETURN QUERY
    SELECT 
        'suspicious_location',
        lh.user_id,
        'Acesso de ' || lh.geo_location->>'country',
        'medium'
    FROM login_history lh
    WHERE lh.is_suspicious = true
    AND lh.login_time > NOW() - INTERVAL '1 hour';
END;
$$ LANGUAGE plpgsql;