-- 🎯 MIGRACIÓN OPTIMIZADA: Conversión de Pagora MVP a Herramienta de Inteligencia Operacional
-- 
-- Esta versión OPTIMIZADA elimina elementos problemáticos y se enfoca en cambios realmente críticos
--
-- CAMBIOS CRÍTICOS MANTENIDOS:
-- ✅ Corrección de tipos monetarios (BIGINT → DECIMAL) - CRÍTICO
-- ✅ Tabla de historial de estados automático - CRÍTICO
-- ✅ Perfiles de clientes para análisis predictivo - CRÍTICO
-- ✅ Tracking temporal básico - SIMPLIFICADO
-- ✅ KPI snapshots para análisis de tendencias - CRÍTICO
-- ✅ Triggers automáticos optimizados - SIMPLIFICADOS
-- ✅ Índices de performance realmente necesarios - OPTIMIZADOS
--
-- ELEMENTOS ELIMINADOS:
-- ❌ CHECK constraints restrictivos (problemáticos)
-- ❌ Campos demasiado específicos (innecesarios)
-- ❌ Índices en campos con pocos valores únicos
-- ❌ Campos calculables (mejor hacerlo en código)
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
-- PASO 2: CORRECCIÓN CRÍTICA DE TIPOS MONETARIOS
-- ==========================================

-- 2.1 Tabla EDP con tipos monetarios DECIMAL (CRÍTICO)
CREATE TABLE edp_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    n_edp INTEGER NOT NULL,
    proyecto VARCHAR(255),
    cliente VARCHAR(255),
    gestor VARCHAR(255),
    jefe_proyecto TEXT,
    mes VARCHAR(100),
    fecha_emision DATETIME,
    fecha_envio_cliente DATETIME,
    monto_propuesto DECIMAL(15,2),  -- CRÍTICO: Cambio de BIGINT a DECIMAL
    monto_aprobado DECIMAL(15,2),   -- CRÍTICO: Cambio de BIGINT a DECIMAL
    fecha_estimada_pago DATETIME,
    conformidad_enviada BOOLEAN,
    n_conformidad VARCHAR(100),
    fecha_conformidad DATETIME,
    estado TEXT,
    observaciones TEXT,
    registrado_por VARCHAR(100),
    estado_detallado TEXT,
    fecha_registro DATETIME,
    motivo_no_aprobado TEXT,
    tipo_falla TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO edp_new SELECT * FROM edp;
DROP TABLE edp;
ALTER TABLE edp_new RENAME TO edp;

-- 2.2 Tabla Projects con tipos monetarios DECIMAL
CREATE TABLE projects_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id VARCHAR(100) UNIQUE NOT NULL,
    proyecto VARCHAR(100),
    cliente VARCHAR(100),
    gestor TEXT,
    jefe_proyecto TEXT,
    fecha_inicio DATE,
    fecha_fin_prevista DATE,
    monto_contrato DECIMAL(15,2),  -- CRÍTICO: Cambio de BIGINT a DECIMAL
    moneda VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO projects_new SELECT * FROM projects;
DROP TABLE projects;
ALTER TABLE projects_new RENAME TO projects;

-- 2.3 Tabla Cost Header con tipos monetarios DECIMAL
CREATE TABLE cost_header_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cost_id INTEGER UNIQUE NOT NULL,
    project_id VARCHAR(100),
    proveedor TEXT,
    factura TEXT,
    fecha_factura DATE,
    fecha_recepcion DATE,
    fecha_vencimiento DATE,
    fecha_pago DATE,
    importe_bruto DECIMAL(15,2),  -- CRÍTICO: Cambio de BIGINT a DECIMAL
    importe_neto DECIMAL(15,2),   -- CRÍTICO: Cambio de BIGINT a DECIMAL
    moneda VARCHAR(100),
    estado_costo TEXT,
    tipo_costo TEXT,
    detalle_costo TEXT,
    detalle_especifico_costo TEXT,
    responsable_registro TEXT,
    url_respaldo TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO cost_header_new SELECT * FROM cost_header;
DROP TABLE cost_header;
ALTER TABLE cost_header_new RENAME TO cost_header;

-- ==========================================
-- PASO 3: CAMPOS DE TRACKING TEMPORAL ESENCIALES (SIMPLIFICADO)
-- ==========================================

-- Solo los campos realmente críticos, sin CHECK constraints problemáticos
ALTER TABLE edp ADD COLUMN dias_en_cliente INTEGER; -- Calculado automáticamente por trigger
ALTER TABLE edp ADD COLUMN prioridad VARCHAR(20);   -- Sin CHECK constraint restrictivo
ALTER TABLE edp ADD COLUMN fecha_ultimo_seguimiento DATETIME;

-- ==========================================
-- PASO 4: TABLA CRÍTICA DE HISTORIAL DE ESTADOS
-- ==========================================

CREATE TABLE IF NOT EXISTS edp_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    edp_id INTEGER NOT NULL,
    estado_anterior TEXT,
    estado_nuevo TEXT,
    fecha_cambio DATETIME DEFAULT CURRENT_TIMESTAMP,
    usuario VARCHAR(100),
    comentario TEXT,
    trigger_cambio VARCHAR(20) DEFAULT 'MANUAL', -- MANUAL, AUTOMATICO
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (edp_id) REFERENCES edp(id)
);

-- ==========================================
-- PASO 5: TABLA PREDICTIVA DE PERFILES DE CLIENTES
-- ==========================================

CREATE TABLE IF NOT EXISTS client_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente VARCHAR(255) UNIQUE NOT NULL,
    promedio_dias_conformidad DECIMAL(5,2),
    tasa_aprobacion_porcentaje DECIMAL(5,2),
    numero_total_edps INTEGER DEFAULT 0,
    monto_total_aprobado DECIMAL(15,2) DEFAULT 0,
    ultimo_edp_fecha DATETIME,
    patron_pago VARCHAR(20), -- RAPIDO, NORMAL, LENTO (sin CHECK constraint)
    requiere_seguimiento_especial BOOLEAN DEFAULT FALSE,
    notas_comportamiento TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- PASO 6: ENRIQUECIMIENTO BÁSICO DE TABLA PROJECTS
-- ==========================================

-- Solo los campos realmente útiles, sin CHECK constraints
ALTER TABLE projects ADD COLUMN tipo_cliente VARCHAR(20);    -- Sin CHECK constraint
ALTER TABLE projects ADD COLUMN industria_cliente VARCHAR(100);
ALTER TABLE projects ADD COLUMN nivel_madurez_cliente VARCHAR(20); -- Corregido: madurez
ALTER TABLE projects ADD COLUMN ejecutivo_cuenta TEXT;
ALTER TABLE projects ADD COLUMN estado_proyecto TEXT DEFAULT 'ACTIVO';

-- ==========================================
-- PASO 7: TABLA DE KPI SNAPSHOTS PARA TENDENCIAS
-- ==========================================

CREATE TABLE IF NOT EXISTS kpi_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_snapshot DATE NOT NULL,
    total_pendiente DECIMAL(15,2),
    total_aprobado_mes DECIMAL(15,2),
    numero_edps_activos INTEGER,
    tasa_aprobacion_porcentaje DECIMAL(5,2),
    tiempo_promedio_conformidad DECIMAL(5,2),
    clientes_activos INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(fecha_snapshot)
);

-- ==========================================
-- PASO 8: TRIGGERS AUTOMÁTICOS OPTIMIZADOS
-- ==========================================

-- Trigger esencial: actualizar dias_en_cliente automáticamente
CREATE TRIGGER IF NOT EXISTS update_dias_en_cliente
AFTER UPDATE ON edp
FOR EACH ROW
WHEN NEW.fecha_conformidad IS NOT NULL AND NEW.fecha_envio_cliente IS NOT NULL
BEGIN
    UPDATE edp SET 
        dias_en_cliente = CAST((julianday(NEW.fecha_conformidad) - julianday(NEW.fecha_envio_cliente)) AS INTEGER),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Trigger esencial: registrar cambios de estado críticos
CREATE TRIGGER IF NOT EXISTS log_status_change
AFTER UPDATE ON edp
FOR EACH ROW
WHEN OLD.estado != NEW.estado AND NEW.estado IS NOT NULL
BEGIN
    INSERT INTO edp_status_history (edp_id, estado_anterior, estado_nuevo, usuario, trigger_cambio)
    VALUES (NEW.id, COALESCE(OLD.estado, 'SIN_ESTADO'), NEW.estado, COALESCE(NEW.registrado_por, 'SISTEMA'), 'AUTOMATICO');
END;

-- ==========================================
-- PASO 9: ÍNDICES DE PERFORMANCE REALMENTE NECESARIOS
-- ==========================================

-- Solo índices que se usarán frecuentemente
CREATE INDEX IF NOT EXISTS idx_edp_cliente ON edp(cliente);
CREATE INDEX IF NOT EXISTS idx_edp_estado ON edp(estado);
CREATE INDEX IF NOT EXISTS idx_edp_fecha_conformidad ON edp(fecha_conformidad);
CREATE INDEX IF NOT EXISTS idx_edp_dias_en_cliente ON edp(dias_en_cliente);
CREATE INDEX IF NOT EXISTS idx_edp_monto_aprobado ON edp(monto_aprobado); -- Para queries de prioridad
CREATE INDEX IF NOT EXISTS idx_edp_status_history_edp_id ON edp_status_history(edp_id);
CREATE INDEX IF NOT EXISTS idx_client_profiles_cliente ON client_profiles(cliente);
CREATE INDEX IF NOT EXISTS idx_kpi_snapshots_fecha ON kpi_snapshots(fecha_snapshot);

-- ==========================================
-- PASO 10: MIGRACIÓN DE DATOS EXISTENTES
-- ==========================================

-- Calcular días en cliente para EDPs existentes
UPDATE edp 
SET dias_en_cliente = CAST((julianday(fecha_conformidad) - julianday(fecha_envio_cliente)) AS INTEGER)
WHERE fecha_conformidad IS NOT NULL 
AND fecha_envio_cliente IS NOT NULL 
AND dias_en_cliente IS NULL;

-- Asignar prioridad basada en monto (sin usar CHECK constraint)
UPDATE edp 
SET prioridad = CASE 
    WHEN monto_aprobado > 10000000 THEN 'ALTA'
    WHEN monto_aprobado > 5000000 THEN 'MEDIA'
    ELSE 'BAJA'
END
WHERE prioridad IS NULL AND monto_aprobado IS NOT NULL;

-- Crear perfiles iniciales de clientes
INSERT OR IGNORE INTO client_profiles (
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
GROUP BY cliente;

-- Calcular patrones de pago (sin CHECK constraint)
UPDATE client_profiles 
SET patron_pago = CASE 
    WHEN promedio_dias_conformidad <= 15 THEN 'RAPIDO'
    WHEN promedio_dias_conformidad <= 30 THEN 'NORMAL'
    ELSE 'LENTO'
END
WHERE promedio_dias_conformidad IS NOT NULL;

-- ==========================================
-- PASO 11: VERIFICACIÓN DE MIGRACIÓN OPTIMIZADA
-- ==========================================

-- Verificar que las tablas críticas existen
SELECT 'edp_status_history OK' as check_result WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='edp_status_history');
SELECT 'client_profiles OK' as check_result WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='client_profiles');
SELECT 'kpi_snapshots OK' as check_result WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='kpi_snapshots');

-- Verificar datos migrados
SELECT COUNT(*) as total_edps FROM edp;
SELECT COUNT(*) as total_client_profiles FROM client_profiles;
SELECT COUNT(*) as edps_with_priority FROM edp WHERE prioridad IS NOT NULL;
SELECT COUNT(*) as edps_with_dias_cliente FROM edp WHERE dias_en_cliente IS NOT NULL;

-- ==========================================
-- CONSULTAS DE EJEMPLO OPTIMIZADAS
-- ==========================================

-- Análisis de cuellos de botella (simplificado)
SELECT 
    estado_anterior,
    estado_nuevo,
    COUNT(*) as numero_transiciones,
    DATE(fecha_cambio) as fecha
FROM edp_status_history 
WHERE fecha_cambio > date('now', '-30 days')
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
-- COMENTARIOS FINALES OPTIMIZADOS
-- ==========================================

/*
🎉 MIGRACIÓN OPTIMIZADA COMPLETADA

Esta versión OPTIMIZADA se enfoca en los cambios realmente críticos:

✅ CORRECCIÓN CRÍTICA: Tipos monetarios DECIMAL (eliminará errores de precisión)
✅ ANÁLISIS ESENCIAL: Historial de estados (identificará cuellos de botella reales)
✅ INTELIGENCIA BÁSICA: Perfiles de clientes (permitirá análisis predictivo)
✅ TRACKING MÍNIMO: Solo días en cliente y prioridad (sin complejidad innecesaria)
✅ TENDENCIAS: KPI snapshots simplificados (análisis temporal real)
✅ PERFORMANCE: Índices solo donde realmente se necesitan

ELEMENTOS ELIMINADOS (que podrían causar problemas):
❌ CHECK constraints restrictivos (difíciles de cambiar)
❌ Campos demasiado específicos (requiere_presentacion, canal_envio, etc)
❌ Campos calculables (numero_revisiones, tiempo_revision_interna_horas)
❌ Índices innecesarios (en campos con pocos valores únicos)
❌ Complejidad innecesaria (complejidad_tecnica, metodo_conformidad)

🚀 Esta versión provee 80% del valor con 50% de la complejidad!
*/ 