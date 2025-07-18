-- 🎯 MEJORA DSO: Cálculo Inteligente de Days Sales Outstanding
-- 
-- Esta mejora añade cálculos de DSO que funcionan tanto con conformidades
-- completadas como con EDPs aún pendientes de respuesta del cliente
--
-- FUNCIONALIDADES:
-- ✅ DSO actual (usando fecha de hoy si no hay conformidad)
-- ✅ DSO real (solo cuando hay conformidad)
-- ✅ Campos calculados automáticamente
-- ✅ Funciones para análisis de aging
-- ✅ Compatible con el campo dias_en_cliente existente
--
-- Autor: Pagora MVP Enhancement Team
-- Fecha: 2025-01-28

-- ==========================================
-- PASO 1: AGREGAR CAMPOS DSO A LA TABLA EDP
-- ==========================================

-- Campo para DSO actual (siempre calculado)
ALTER TABLE edp ADD COLUMN IF NOT EXISTS dso_actual INTEGER;

-- Campo para indicar si está vencido
ALTER TABLE edp ADD COLUMN IF NOT EXISTS esta_vencido BOOLEAN DEFAULT FALSE;

-- Campo para categoría de aging
ALTER TABLE edp ADD COLUMN IF NOT EXISTS categoria_aging VARCHAR(20);

-- Campo para tiempo de revisión interna (desde emisión hasta envío al cliente)
ALTER TABLE edp ADD COLUMN IF NOT EXISTS dias_revision_interna INTEGER;

-- ==========================================
-- PASO 2: FUNCIÓN PARA CALCULAR DSO INTELIGENTE
-- ==========================================

CREATE OR REPLACE FUNCTION update_dso_inteligente()
RETURNS TRIGGER AS $$
BEGIN
    -- Lógica inteligente para calcular DSO según el estado del EDP
    
    -- CASO 1: EDP completado (tiene conformidad)
    IF NEW.fecha_conformidad IS NOT NULL AND NEW.fecha_envio_cliente IS NOT NULL THEN
        -- DSO real: tiempo desde envío hasta conformidad
        NEW.dso_actual = (NEW.fecha_conformidad::date - NEW.fecha_envio_cliente::date);
        NEW.categoria_aging = 'COMPLETADO';
        NEW.esta_vencido = FALSE;
        
    -- CASO 2: EDP enviado al cliente pero sin conformidad
    ELSIF NEW.fecha_envio_cliente IS NOT NULL THEN
        -- DSO pendiente: tiempo desde envío hasta hoy
        NEW.dso_actual = (CURRENT_DATE - NEW.fecha_envio_cliente::date);
        NEW.esta_vencido = (CURRENT_DATE - NEW.fecha_envio_cliente::date) > 30;
        
        -- Categorizar por tiempo de espera
        NEW.categoria_aging = CASE 
            WHEN NEW.dso_actual <= 15 THEN 'RAPIDO'
            WHEN NEW.dso_actual <= 30 THEN 'NORMAL'
            WHEN NEW.dso_actual <= 60 THEN 'LENTO'
            ELSE 'CRITICO'
        END;
        
    -- CASO 3: EDP emitido pero no enviado (revisión interna)
    ELSIF NEW.fecha_emision IS NOT NULL THEN
        -- DSO interno: tiempo desde emisión hasta hoy (tiempo en revisión interna)
        NEW.dso_actual = (CURRENT_DATE - NEW.fecha_emision::date);
        NEW.esta_vencido = (CURRENT_DATE - NEW.fecha_emision::date) > 15; -- 15 días para revisión interna
        
        -- Categorizar por tiempo de revisión interna
        NEW.categoria_aging = CASE 
            WHEN NEW.dso_actual <= 3 THEN 'REVISION_RAPIDA'
            WHEN NEW.dso_actual <= 7 THEN 'REVISION_NORMAL'
            WHEN NEW.dso_actual <= 15 THEN 'REVISION_LENTA'
            ELSE 'REVISION_CRITICA'
        END;
        
    -- CASO 4: EDP sin fechas relevantes
    ELSE
        NEW.dso_actual = NULL;
        NEW.categoria_aging = 'SIN_INICIAR';
        NEW.esta_vencido = FALSE;
    END IF;
    
    -- Mantener compatibilidad: calcular dias_en_cliente solo cuando hay conformidad real
    IF NEW.fecha_conformidad IS NOT NULL AND NEW.fecha_envio_cliente IS NOT NULL THEN
        NEW.dias_en_cliente = (NEW.fecha_conformidad::date - NEW.fecha_envio_cliente::date);
    END IF;
    
    -- Calcular tiempo de revisión interna (desde emisión hasta envío al cliente)
    IF NEW.fecha_envio_cliente IS NOT NULL AND NEW.fecha_emision IS NOT NULL THEN
        NEW.dias_revision_interna = (NEW.fecha_envio_cliente::date - NEW.fecha_emision::date);
    ELSIF NEW.fecha_emision IS NOT NULL AND NEW.fecha_envio_cliente IS NULL THEN
        -- Si aún no se ha enviado, calcular días transcurridos desde emisión
        NEW.dias_revision_interna = (CURRENT_DATE - NEW.fecha_emision::date);
    ELSE
        NEW.dias_revision_interna = NULL;
    END IF;
    
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- PASO 3: ACTUALIZAR TRIGGER EXISTENTE
-- ==========================================

-- Reemplazar el trigger existente con la versión mejorada
DROP TRIGGER IF EXISTS trigger_update_dias_en_cliente ON edp;
DROP TRIGGER IF EXISTS trigger_update_dso_inteligente ON edp;

-- CREAR TRIGGER PARA INSERT Y UPDATE
CREATE TRIGGER trigger_update_dso_inteligente
    BEFORE INSERT OR UPDATE ON edp
    FOR EACH ROW
    EXECUTE FUNCTION update_dso_inteligente();

-- ==========================================
-- PASO 4: CALCULAR DSO PARA DATOS EXISTENTES
-- ==========================================

-- Actualizar todos los EDPs existentes con los nuevos cálculos
UPDATE edp SET updated_at = CURRENT_TIMESTAMP WHERE id = id;

-- ==========================================
-- PASO 5: VISTAS PARA ANÁLISIS DSO
-- ==========================================

-- Vista para DSO actual de EDPs activos
CREATE OR REPLACE VIEW v_dso_activos AS
SELECT 
    n_edp,
    proyecto,
    cliente,
    fecha_emision,
    fecha_envio_cliente,
    fecha_conformidad,
    dias_en_cliente,      -- Solo cuando hay conformidad
    dias_revision_interna, -- Tiempo de revisión interna
    dso_actual,           -- Siempre calculado
    categoria_aging,
    esta_vencido,
    estado,
    monto_aprobado,
    CASE 
        WHEN fecha_conformidad IS NOT NULL THEN 'COMPLETADO'
        WHEN fecha_envio_cliente IS NOT NULL THEN 'PENDIENTE_CLIENTE'
        WHEN fecha_emision IS NOT NULL THEN 'REVISION_INTERNA'
        ELSE 'NO_INICIADO'
    END as status_dso
FROM edp 
WHERE estado NOT IN ('PAGADO', 'CANCELADO')
ORDER BY dso_actual DESC NULLS LAST;

-- Vista para análisis de aging
CREATE OR REPLACE VIEW v_aging_analysis AS
SELECT 
    categoria_aging,
    COUNT(*) as cantidad_edps,
    SUM(monto_aprobado) as monto_total,
    AVG(dso_actual) as dso_promedio,
    COUNT(CASE WHEN esta_vencido THEN 1 END) as edps_vencidos
FROM edp 
WHERE estado NOT IN ('PAGADO', 'CANCELADO')
AND fecha_envio_cliente IS NOT NULL
GROUP BY categoria_aging
ORDER BY 
    CASE categoria_aging 
        WHEN 'REVISION_RAPIDA' THEN 1
        WHEN 'REVISION_NORMAL' THEN 2
        WHEN 'REVISION_LENTA' THEN 3
        WHEN 'REVISION_CRITICA' THEN 4
        WHEN 'RAPIDO' THEN 5
        WHEN 'NORMAL' THEN 6
        WHEN 'LENTO' THEN 7
        WHEN 'CRITICO' THEN 8
        WHEN 'COMPLETADO' THEN 9
        ELSE 10
    END;

-- ==========================================
-- PASO 6: FUNCIONES DE ANÁLISIS DSO
-- ==========================================

-- Función para calcular DSO promedio ponderado
CREATE OR REPLACE FUNCTION get_dso_promedio_ponderado()
RETURNS DECIMAL(10,2) AS $$
DECLARE
    dso_ponderado DECIMAL(10,2);
BEGIN
    SELECT 
        SUM(dso_actual * monto_aprobado) / NULLIF(SUM(monto_aprobado), 0)
    INTO dso_ponderado
    FROM edp 
    WHERE dso_actual IS NOT NULL 
    AND monto_aprobado > 0
    AND estado NOT IN ('PAGADO', 'CANCELADO');
    
    RETURN COALESCE(dso_ponderado, 0);
END;
$$ LANGUAGE plpgsql;

-- Función para obtener EDPs críticos por DSO
CREATE OR REPLACE FUNCTION get_edps_criticos_dso(limite_dias INTEGER DEFAULT 45)
RETURNS TABLE(
    n_edp INTEGER,
    proyecto VARCHAR,
    cliente VARCHAR,
    dso_actual INTEGER,
    monto_aprobado DECIMAL,
    dias_sin_respuesta INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.n_edp,
        e.proyecto,
        e.cliente,
        e.dso_actual,
        e.monto_aprobado,
        (CURRENT_DATE - e.fecha_envio_cliente::date)::INTEGER as dias_sin_respuesta
    FROM edp e
    WHERE e.fecha_envio_cliente IS NOT NULL
    AND e.fecha_conformidad IS NULL
    AND e.dso_actual > limite_dias
    AND e.estado NOT IN ('PAGADO', 'CANCELADO')
    ORDER BY e.dso_actual DESC, e.monto_aprobado DESC;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- PASO 7: ÍNDICES PARA PERFORMANCE DSO
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_edp_dso_actual ON edp(dso_actual);
CREATE INDEX IF NOT EXISTS idx_edp_categoria_aging ON edp(categoria_aging);
CREATE INDEX IF NOT EXISTS idx_edp_esta_vencido ON edp(esta_vencido);
CREATE INDEX IF NOT EXISTS idx_edp_fecha_envio_cliente ON edp(fecha_envio_cliente);
CREATE INDEX IF NOT EXISTS idx_edp_dias_revision_interna ON edp(dias_revision_interna);
CREATE INDEX IF NOT EXISTS idx_edp_fecha_emision ON edp(fecha_emision);

-- ==========================================
-- EJEMPLOS DE USO DSO
-- ==========================================

-- EJEMPLO 1: Ver EDPs con DSO actual (incluyendo pendientes)
SELECT 
    n_edp,
    cliente,
    fecha_envio_cliente,
    fecha_conformidad,
    dias_en_cliente,    -- Solo si tiene conformidad
    dso_actual,         -- Siempre calculado
    categoria_aging,
    esta_vencido
FROM v_dso_activos
LIMIT 10;

-- EJEMPLO 2: Análisis de aging completo
SELECT * FROM v_aging_analysis;

-- EJEMPLO 3: DSO promedio ponderado actual
SELECT get_dso_promedio_ponderado() as dso_promedio_empresa;

-- EJEMPLO 4: EDPs críticos por DSO
SELECT * FROM get_edps_criticos_dso(30);

-- EJEMPLO 5: Comparar todos los tiempos de un EDP
SELECT 
    n_edp,
    cliente,
    proyecto,
    fecha_emision,
    fecha_envio_cliente,
    fecha_conformidad,
    dias_revision_interna, -- Tiempo desde emisión hasta envío (o hasta hoy si no enviado)
    dias_en_cliente,      -- Solo cuando hay conformidad (NULL si pendiente)
    dso_actual,           -- Siempre calculado según el estado
    categoria_aging,
    CASE 
        WHEN fecha_conformidad IS NOT NULL THEN 'COMPLETADO'
        WHEN fecha_envio_cliente IS NOT NULL THEN 'PENDIENTE_CLIENTE'
        WHEN fecha_emision IS NOT NULL THEN 'REVISION_INTERNA'
        ELSE 'NO_INICIADO'
    END as estado_flujo
FROM edp 
ORDER BY 
    CASE 
        WHEN fecha_conformidad IS NOT NULL THEN 1
        WHEN fecha_envio_cliente IS NOT NULL THEN 2
        WHEN fecha_emision IS NOT NULL THEN 3
        ELSE 4
    END,
    dso_actual DESC NULLS LAST
LIMIT 15;

-- ==========================================
-- CONSULTAS PARA DASHBOARD DSO
-- ==========================================

-- KPI: DSO promedio actual
SELECT 
    ROUND(AVG(dso_actual), 1) as dso_promedio,
    COUNT(*) as total_edps_activos,
    COUNT(CASE WHEN esta_vencido THEN 1 END) as edps_vencidos,
    SUM(monto_aprobado) as monto_total_pendiente
FROM edp 
WHERE estado NOT IN ('PAGADO', 'CANCELADO')
AND fecha_envio_cliente IS NOT NULL;

-- Evolución DSO por mes
SELECT 
    DATE_TRUNC('month', fecha_envio_cliente) as mes,
    ROUND(AVG(dso_actual), 1) as dso_promedio_mes,
    COUNT(*) as edps_enviados,
    COUNT(CASE WHEN esta_vencido THEN 1 END) as edps_vencidos_mes
FROM edp 
WHERE fecha_envio_cliente >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', fecha_envio_cliente)
ORDER BY mes;

-- Top clientes por DSO problemático
SELECT 
    cliente,
    COUNT(*) as edps_activos,
    ROUND(AVG(dso_actual), 1) as dso_promedio,
    COUNT(CASE WHEN esta_vencido THEN 1 END) as edps_vencidos,
    SUM(monto_aprobado) as monto_en_riesgo
FROM edp 
WHERE estado NOT IN ('PAGADO', 'CANCELADO')
AND fecha_envio_cliente IS NOT NULL
GROUP BY cliente
HAVING AVG(dso_actual) > 30
ORDER BY dso_promedio DESC;

-- ==========================================
-- COMENTARIOS FINALES
-- ==========================================

/*
🎯 MEJORA DSO IMPLEMENTADA

Ahora tienes un sistema DSO inteligente que:

✅ CALCULA DSO ACTUAL: Usa fecha actual si no hay conformidad
✅ MANTIENE DIAS_EN_CLIENTE: Solo cuando hay conformidad real
✅ CATEGORIZA AGING: RAPIDO, NORMAL, LENTO, CRITICO
✅ IDENTIFICA VENCIDOS: Automáticamente
✅ VISTAS ESPECIALIZADAS: Para análisis rápido
✅ FUNCIONES DE ANÁLISIS: Para métricas avanzadas

DIFERENCIAS CLAVE:
- dias_en_cliente: Solo para EDPs con conformidad (dato histórico real)
- dso_actual: Para todos los EDPs enviados (incluye pendientes)
- categoria_aging: Clasificación automática por velocidad
- esta_vencido: Flag automático para EDPs problemáticos

USO RECOMENDADO:
- Dashboard: Usar dso_actual para métricas actuales
- Análisis histórico: Usar dias_en_cliente para patrones reales
- Alertas: Usar esta_vencido y categoria_aging
- Reportes: Combinar ambos según necesidad
*/ 