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

-- ==========================================
-- PASO 2: FUNCIÓN PARA CALCULAR DSO INTELIGENTE
-- ==========================================

CREATE OR REPLACE FUNCTION update_dso_inteligente()
RETURNS TRIGGER AS $$
BEGIN
    -- Calcular DSO actual: usar fecha_conformidad si existe, sino fecha actual
    IF NEW.fecha_envio_cliente IS NOT NULL THEN
        IF NEW.fecha_conformidad IS NOT NULL THEN
            -- DSO real: ya tiene conformidad
            NEW.dso_actual = EXTRACT(DAY FROM NEW.fecha_conformidad - NEW.fecha_envio_cliente);
        ELSE
            -- DSO pendiente: usar fecha actual
            NEW.dso_actual = EXTRACT(DAY FROM CURRENT_DATE - NEW.fecha_envio_cliente::date);
        END IF;
    ELSE
        NEW.dso_actual = NULL;
    END IF;
    
    -- Determinar si está vencido (más de 30 días sin respuesta)
    IF NEW.fecha_envio_cliente IS NOT NULL AND NEW.fecha_conformidad IS NULL THEN
        NEW.esta_vencido = (CURRENT_DATE - NEW.fecha_envio_cliente::date) > 30;
    ELSE
        NEW.esta_vencido = FALSE;
    END IF;
    
    -- Categorizar aging
    IF NEW.dso_actual IS NOT NULL THEN
        NEW.categoria_aging = CASE 
            WHEN NEW.dso_actual <= 15 THEN 'RAPIDO'
            WHEN NEW.dso_actual <= 30 THEN 'NORMAL'
            WHEN NEW.dso_actual <= 60 THEN 'LENTO'
            ELSE 'CRITICO'
        END;
    ELSE
        NEW.categoria_aging = 'SIN_ENVIAR';
    END IF;
    
    -- También calcular dias_en_cliente como antes
    IF NEW.fecha_conformidad IS NOT NULL AND NEW.fecha_envio_cliente IS NOT NULL THEN
        NEW.dias_en_cliente = EXTRACT(DAY FROM NEW.fecha_conformidad - NEW.fecha_envio_cliente);
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
CREATE TRIGGER trigger_update_dso_inteligente
    BEFORE UPDATE ON edp
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
    fecha_envio_cliente,
    fecha_conformidad,
    dias_en_cliente,      -- Solo cuando hay conformidad
    dso_actual,           -- Siempre calculado
    categoria_aging,
    esta_vencido,
    estado,
    monto_aprobado,
    CASE 
        WHEN fecha_conformidad IS NOT NULL THEN 'COMPLETADO'
        WHEN fecha_envio_cliente IS NOT NULL THEN 'PENDIENTE'
        ELSE 'NO_ENVIADO'
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
        WHEN 'RAPIDO' THEN 1
        WHEN 'NORMAL' THEN 2
        WHEN 'LENTO' THEN 3
        WHEN 'CRITICO' THEN 4
        ELSE 5
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
        EXTRACT(DAY FROM CURRENT_DATE - e.fecha_envio_cliente::date)::INTEGER as dias_sin_respuesta
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

-- EJEMPLO 5: Comparar dias_en_cliente vs dso_actual
SELECT 
    n_edp,
    cliente,
    dias_en_cliente,      -- Solo cuando hay conformidad (NULL si pendiente)
    dso_actual,           -- Siempre calculado
    CASE 
        WHEN dias_en_cliente IS NOT NULL THEN 'Conformidad recibida'
        WHEN dso_actual IS NOT NULL THEN 'Pendiente de conformidad'
        ELSE 'No enviado al cliente'
    END as situacion
FROM edp 
WHERE fecha_envio_cliente IS NOT NULL
ORDER BY dso_actual DESC
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