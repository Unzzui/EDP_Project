-- Crear tabla para sistema de alertas progresivas EDP
-- Compatible con PostgreSQL/Supabase

CREATE TABLE IF NOT EXISTS edp_alerts (
    id SERIAL PRIMARY KEY,
    edp_id VARCHAR(50) NOT NULL,
    alert_type VARCHAR(20) NOT NULL CHECK (alert_type IN ('early_warning', 'warning', 'urgent', 'critical', 'overdue')),
    days_since_last_movement INTEGER NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    recipient_email VARCHAR(255) NOT NULL,
    email_subject VARCHAR(500),
    email_sent_successfully BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_edp_alerts_edp_id ON edp_alerts(edp_id);
CREATE INDEX IF NOT EXISTS idx_edp_alerts_sent_at ON edp_alerts(sent_at);
CREATE INDEX IF NOT EXISTS idx_edp_alerts_alert_type ON edp_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_edp_alerts_days_movement ON edp_alerts(days_since_last_movement);

-- Comentarios para documentación
COMMENT ON TABLE edp_alerts IS 'Sistema de alertas progresivas para EDPs que se acercan al estado crítico';
COMMENT ON COLUMN edp_alerts.edp_id IS 'Identificador del EDP (número de EDP)';
COMMENT ON COLUMN edp_alerts.alert_type IS 'Tipo de alerta: early_warning (7 días), warning (14 días), urgent (21 días), critical (28 días), overdue (30+ días)';
COMMENT ON COLUMN edp_alerts.days_since_last_movement IS 'Días transcurridos desde el último movimiento del EDP';
COMMENT ON COLUMN edp_alerts.sent_at IS 'Fecha y hora cuando se envió la alerta';
COMMENT ON COLUMN edp_alerts.recipient_email IS 'Email del destinatario de la alerta';
COMMENT ON COLUMN edp_alerts.email_subject IS 'Asunto del email enviado';
COMMENT ON COLUMN edp_alerts.email_sent_successfully IS 'Indicador si el email se envió correctamente';

-- Agregar constraint para evitar duplicados de alertas del mismo tipo en el mismo día
CREATE UNIQUE INDEX IF NOT EXISTS idx_edp_alerts_unique_daily 
ON edp_alerts(edp_id, alert_type, DATE(sent_at));

-- Vista para consultas frecuentes
CREATE OR REPLACE VIEW v_edp_alerts_summary AS
SELECT 
    edp_id,
    alert_type,
    COUNT(*) as total_alerts,
    MAX(sent_at) as last_alert_sent,
    MAX(days_since_last_movement) as max_days_without_movement,
    COUNT(CASE WHEN email_sent_successfully THEN 1 END) as successful_emails,
    COUNT(CASE WHEN NOT email_sent_successfully THEN 1 END) as failed_emails
FROM edp_alerts 
GROUP BY edp_id, alert_type
ORDER BY edp_id, alert_type;

COMMENT ON VIEW v_edp_alerts_summary IS 'Resumen de alertas por EDP y tipo de alerta';

-- Función para limpiar alertas antiguas (opcional)
CREATE OR REPLACE FUNCTION cleanup_old_alerts(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM edp_alerts 
    WHERE sent_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_alerts IS 'Función para limpiar alertas antiguas, por defecto mantiene 90 días';

-- Insertar datos de prueba (opcional - comentado)
/*
INSERT INTO edp_alerts (edp_id, alert_type, days_since_last_movement, recipient_email, email_subject, email_sent_successfully) VALUES
('EDP001', 'early_warning', 7, 'test@example.com', 'Alerta Temprana: EDP001 - 7 días sin movimiento', true),
('EDP002', 'warning', 14, 'test@example.com', 'Advertencia: EDP002 - 14 días sin movimiento', true),
('EDP003', 'urgent', 21, 'test@example.com', 'Urgente: EDP003 - 21 días sin movimiento', false),
('EDP004', 'critical', 28, 'test@example.com', 'Crítico: EDP004 - 28 días sin movimiento', true),
('EDP005', 'overdue', 35, 'test@example.com', 'Vencido: EDP005 - 35 días sin movimiento', true);
*/
