-- 🎯 MIGRACIÓN OPTIMIZADA PARA POSTGRESQL
-- Conversión de Pagora MVP a Herramienta de Inteligencia Operacional
-- 
-- Esta versión está específicamente diseñada para PostgreSQL/Supabase
--
-- CAMBIOS CRÍTICOS:
-- ✅ Corrección de tipos monetarios (BIGINT → DECIMAL) - CRÍTICO
-- ✅ Tabla de historial de estados automático - CRÍTICO  
-- ✅ Perfiles de clientes para análisis predictivo - CRÍTICO
-- ✅ Tracking temporal básico - SIMPLIFICADO
-- ✅ KPI snapshots para análisis de tendencias - CRÍTICO
-- ✅ Triggers automáticos PostgreSQL - OPTIMIZADOS
-- ✅ Índices de performance realmente necesarios - OPTIMIZADOS
--
-- Autor: Pagora MVP Enhancement Team
-- Fecha: 2025-01-28

-- ==========================================
-- PASO 1: BACKUP DE SEGURIDAD
-- ==========================================
CREATE TABLE IF NOT EXISTS backup_edp AS SELECT * FROM edp;
CREATE TABLE IF NOT EXISTS backup_projects AS SELECT * FROM projects;
CREATE TABLE IF NOT EXISTS backup_cost_header AS SELECT * FROM cost_header;
CREATE TABLE IF NOT EXISTS backup_cost_lines AS SELECT * FROM cost_lines;

-- ==========================================
-- PASO 2: CORRECCIÓN CRÍTICA DE TIPOS MONETARIOS (POSTGRESQL)
-- ==========================================

-- En PostgreSQL podemos usar ALTER TABLE directamente
ALTER TABLE edp ALTER COLUMN monto_propuesto TYPE DECIMAL(15,2);
ALTER TABLE edp ALTER COLUMN monto_aprobado TYPE DECIMAL(15,2);
ALTER TABLE projects ALTER COLUMN monto_contrato TYPE DECIMAL(15,2);
ALTER TABLE cost_header ALTER COLUMN importe_bruto TYPE DECIMAL(15,2);
ALTER TABLE cost_header ALTER COLUMN importe_neto TYPE DECIMAL(15,2);

-- También corregir cost_lines si existe
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cost_lines') THEN
        ALTER TABLE cost_lines ALTER COLUMN precio_unitario TYPE DECIMAL(15,2);
        ALTER TABLE cost_lines ALTER COLUMN subtotal TYPE DECIMAL(15,2);
    END IF;
END $$;

-- ==========================================
-- PASO 3: CAMPOS DE TRACKING TEMPORAL ESENCIALES
-- ==========================================

-- Solo los campos realmente críticos
ALTER TABLE edp ADD COLUMN IF NOT EXISTS dias_en_cliente INTEGER;
ALTER TABLE edp ADD COLUMN IF NOT EXISTS prioridad VARCHAR(20);
ALTER TABLE edp ADD COLUMN IF NOT EXISTS fecha_ultimo_seguimiento TIMESTAMP;

-- ==========================================
-- PASO 4: TABLA CRÍTICA DE HISTORIAL DE ESTADOS
-- ==========================================

CREATE TABLE IF NOT EXISTS edp_status_history (
    id SERIAL PRIMARY KEY,
    edp_id INTEGER NOT NULL,
    estado_anterior TEXT,
    estado_nuevo TEXT,
    fecha_cambio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usuario VARCHAR(100),
    comentario TEXT,
    trigger_cambio VARCHAR(20) DEFAULT 'MANUAL',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (edp_id) REFERENCES edp(id)
);

-- ==========================================
-- PASO 5: TABLA PREDICTIVA DE PERFILES DE CLIENTES
-- ==========================================

CREATE TABLE IF NOT EXISTS client_profiles (
    id SERIAL PRIMARY KEY,
    cliente VARCHAR(255) UNIQUE NOT NULL,
    promedio_dias_conformidad DECIMAL(5,2),
    tasa_aprobacion_porcentaje DECIMAL(5,2),
    numero_total_edps INTEGER DEFAULT 0,
    monto_total_aprobado DECIMAL(15,2) DEFAULT 0,
    ultimo_edp_fecha TIMESTAMP,
    patron_pago VARCHAR(20),
    requiere_seguimiento_especial BOOLEAN DEFAULT FALSE,
    notas_comportamiento TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- PASO 6: ENRIQUECIMIENTO BÁSICO DE TABLA PROJECTS
-- ==========================================

-- Solo los campos realmente útiles
ALTER TABLE projects ADD COLUMN IF NOT EXISTS tipo_cliente VARCHAR(20);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS industria_cliente VARCHAR(100);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS nivel_madurez_cliente VARCHAR(20);
ALTER TABLE projects ADD COLUMN IF NOT EXISTS ejecutivo_cuenta TEXT;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS estado_proyecto TEXT DEFAULT 'ACTIVO';

-- ==========================================
-- PASO 7: TABLA DE KPI SNAPSHOTS PARA TENDENCIAS
-- ==========================================

CREATE TABLE IF NOT EXISTS kpi_snapshots (
    id SERIAL PRIMARY KEY,
    fecha_snapshot DATE NOT NULL,
    total_pendiente DECIMAL(15,2),
    total_aprobado_mes DECIMAL(15,2),
    numero_edps_activos INTEGER,
    tasa_aprobacion_porcentaje DECIMAL(5,2),
    tiempo_promedio_conformidad DECIMAL(5,2),
    clientes_activos INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fecha_snapshot)
);

-- ==========================================
-- PASO 8: TRIGGERS AUTOMÁTICOS POSTGRESQL
-- ==========================================

-- Función para actualizar dias_en_cliente automáticamente
CREATE OR REPLACE FUNCTION update_dias_en_cliente()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.fecha_conformidad IS NOT NULL AND NEW.fecha_envio_cliente IS NOT NULL THEN
        NEW.dias_en_cliente = EXTRACT(DAY FROM NEW.fecha_conformidad - NEW.fecha_envio_cliente);
    END IF;
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear trigger si no existe
DROP TRIGGER IF EXISTS trigger_update_dias_en_cliente ON edp;
CREATE TRIGGER trigger_update_dias_en_cliente
    BEFORE UPDATE ON edp
    FOR EACH ROW
    EXECUTE FUNCTION update_dias_en_cliente();

-- Función para registrar cambios de estado automáticamente
CREATE OR REPLACE FUNCTION log_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.estado IS DISTINCT FROM NEW.estado AND NEW.estado IS NOT NULL THEN
        INSERT INTO edp_status_history (edp_id, estado_anterior, estado_nuevo, usuario, trigger_cambio)
        VALUES (NEW.id, COALESCE(OLD.estado, 'SIN_ESTADO'), NEW.estado, COALESCE(NEW.registrado_por, 'SISTEMA'), 'AUTOMATICO');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear trigger si no existe
DROP TRIGGER IF EXISTS trigger_log_status_change ON edp;
CREATE TRIGGER trigger_log_status_change
    AFTER UPDATE ON edp
    FOR EACH ROW
    EXECUTE FUNCTION log_status_change();

-- ==========================================
-- PASO 9: ÍNDICES DE PERFORMANCE REALMENTE NECESARIOS
-- ==========================================

-- Solo índices que se usarán frecuentemente
CREATE INDEX IF NOT EXISTS idx_edp_cliente ON edp(cliente);
CREATE INDEX IF NOT EXISTS idx_edp_estado ON edp(estado);
CREATE INDEX IF NOT EXISTS idx_edp_fecha_conformidad ON edp(fecha_conformidad);
CREATE INDEX IF NOT EXISTS idx_edp_dias_en_cliente ON edp(dias_en_cliente);
CREATE INDEX IF NOT EXISTS idx_edp_monto_aprobado ON edp(monto_aprobado);
CREATE INDEX IF NOT EXISTS idx_edp_status_history_edp_id ON edp_status_history(edp_id);
CREATE INDEX IF NOT EXISTS idx_client_profiles_cliente ON client_profiles(cliente);
CREATE INDEX IF NOT EXISTS idx_kpi_snapshots_fecha ON kpi_snapshots(fecha_snapshot);

-- ==========================================
-- PASO 10: MIGRACIÓN DE DATOS EXISTENTES
-- ==========================================

-- Calcular días en cliente para EDPs existentes
UPDATE edp 
SET dias_en_cliente = EXTRACT(DAY FROM fecha_conformidad - fecha_envio_cliente)
WHERE fecha_conformidad IS NOT NULL 
AND fecha_envio_cliente IS NOT NULL 
AND dias_en_cliente IS NULL;

-- Asignar prioridad basada en monto
UPDATE edp 
SET prioridad = CASE 
    WHEN monto_aprobado > 10000000 THEN 'ALTA'
    WHEN monto_aprobado > 5000000 THEN 'MEDIA'
    ELSE 'BAJA'
END
WHERE prioridad IS NULL AND monto_aprobado IS NOT NULL;

-- Crear perfiles iniciales de clientes
INSERT INTO client_profiles (
    cliente, 
    numero_total_edps, 
    monto_total_aprobado, 
    ultimo_edp_fecha,
    promedio_dias_conformidad
)
SELECT 
    cliente,
    COUNT(*) as numero_total_edps,
    SUM(COALESCE(monto_aprobado, 0)) as monto_total_aprobado,
    MAX(fecha_conformidad) as ultimo_edp_fecha,
    AVG(dias_en_cliente) as promedio_dias_conformidad
FROM edp 
WHERE cliente IS NOT NULL 
GROUP BY cliente
ON CONFLICT (cliente) DO NOTHING;

-- Calcular patrones de pago
UPDATE client_profiles 
SET patron_pago = CASE 
    WHEN promedio_dias_conformidad <= 15 THEN 'RAPIDO'
    WHEN promedio_dias_conformidad <= 30 THEN 'NORMAL'
    ELSE 'LENTO'
END
WHERE promedio_dias_conformidad IS NOT NULL;

-- ==========================================
-- PASO 11: VERIFICACIÓN DE MIGRACIÓN
-- ==========================================

-- Verificar que las tablas críticas existen
SELECT 'edp_status_history OK' as check_result 
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'edp_status_history');

SELECT 'client_profiles OK' as check_result 
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'client_profiles');

SELECT 'kpi_snapshots OK' as check_result 
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'kpi_snapshots');

-- Verificar datos migrados
SELECT COUNT(*) as total_edps FROM edp;
SELECT COUNT(*) as total_client_profiles FROM client_profiles;
SELECT COUNT(*) as edps_with_priority FROM edp WHERE prioridad IS NOT NULL;
SELECT COUNT(*) as edps_with_dias_cliente FROM edp WHERE dias_en_cliente IS NOT NULL;

-- ==========================================
-- CONSULTAS DE EJEMPLO OPTIMIZADAS POSTGRESQL
-- ==========================================

-- Análisis de cuellos de botella (últimos 30 días)
SELECT 
    estado_anterior,
    estado_nuevo,
    COUNT(*) as numero_transiciones,
    DATE(fecha_cambio) as fecha
FROM edp_status_history 
WHERE fecha_cambio > CURRENT_DATE - INTERVAL '30 days'
GROUP BY estado_anterior, estado_nuevo, DATE(fecha_cambio)
ORDER BY numero_transiciones DESC;

-- Clientes por patrón de pago
SELECT 
    patron_pago,
    COUNT(*) as numero_clientes,
    AVG(promedio_dias_conformidad) as promedio_dias,
    SUM(monto_total_aprobado) as monto_total
FROM client_profiles 
GROUP BY patron_pago
ORDER BY monto_total DESC;

-- EDPs críticos optimizado
SELECT 
    n_edp,
    proyecto,
    cliente,
    prioridad,
    dias_en_cliente,
    estado,
    monto_aprobado
FROM edp 
WHERE prioridad = 'ALTA' 
AND dias_en_cliente > 30
ORDER BY monto_aprobado DESC
LIMIT 20;

-- ==========================================
-- COMENTARIOS FINALES
-- ==========================================

/*
🎉 MIGRACIÓN POSTGRESQL OPTIMIZADA COMPLETADA

Esta versión para PostgreSQL incluye los cambios críticos:

✅ CORRECCIÓN CRÍTICA: Tipos monetarios DECIMAL (sin recrear tablas)
✅ ANÁLISIS ESENCIAL: Historial de estados con triggers PostgreSQL
✅ INTELIGENCIA BÁSICA: Perfiles de clientes para análisis predictivo
✅ TRACKING MÍNIMO: Solo campos esenciales
✅ TENDENCIAS: KPI snapshots simplificados
✅ PERFORMANCE: Índices optimizados para PostgreSQL

🚀 Base de datos transformada para inteligencia operacional en PostgreSQL!
*/ 