-- 🔧 CORRECCIÓN: Función DSO para tipos de datos correctos
-- 
-- El problema es que fecha_envio_cliente y fecha_conformidad son INTEGER
-- representando fechas en formato YYYYMMDD, no tipos DATE reales
--
-- Esta corrección maneja la conversión correcta de INTEGER a DATE

-- ==========================================
-- FUNCIÓN CORREGIDA PARA DSO INTELIGENTE
-- ==========================================

CREATE OR REPLACE FUNCTION update_dso_inteligente()
RETURNS TRIGGER AS $$
BEGIN
    -- Calcular DSO actual: usar fecha_conformidad si existe, sino fecha actual
    IF NEW.fecha_envio_cliente IS NOT NULL THEN
        IF NEW.fecha_conformidad IS NOT NULL THEN
            -- DSO real: ya tiene conformidad
            -- Convertir INTEGER (YYYYMMDD) a DATE y calcular diferencia
            NEW.dso_actual = (
                TO_DATE(NEW.fecha_conformidad::text, 'YYYYMMDD') - 
                TO_DATE(NEW.fecha_envio_cliente::text, 'YYYYMMDD')
            );
        ELSE
            -- DSO pendiente: usar fecha actual
            -- Convertir INTEGER (YYYYMMDD) a DATE y restar de fecha actual
            NEW.dso_actual = (
                CURRENT_DATE - TO_DATE(NEW.fecha_envio_cliente::text, 'YYYYMMDD')
            );
        END IF;
    ELSE
        NEW.dso_actual = NULL;
    END IF;
    
    -- Determinar si está vencido (más de 30 días sin respuesta)
    IF NEW.fecha_envio_cliente IS NOT NULL AND NEW.fecha_conformidad IS NULL THEN
        NEW.esta_vencido = (
            CURRENT_DATE - TO_DATE(NEW.fecha_envio_cliente::text, 'YYYYMMDD')
        ) > 30;
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
    
    -- También calcular dias_en_cliente como antes (solo cuando hay conformidad)
    IF NEW.fecha_conformidad IS NOT NULL AND NEW.fecha_envio_cliente IS NOT NULL THEN
        NEW.dias_en_cliente = (
            TO_DATE(NEW.fecha_conformidad::text, 'YYYYMMDD') - 
            TO_DATE(NEW.fecha_envio_cliente::text, 'YYYYMMDD')
        );
    END IF;
    
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- ACTUALIZAR TRIGGER
-- ==========================================

-- Reemplazar el trigger con la función corregida
DROP TRIGGER IF EXISTS trigger_update_dso_inteligente ON edp;
CREATE TRIGGER trigger_update_dso_inteligente
    BEFORE UPDATE ON edp
    FOR EACH ROW
    EXECUTE FUNCTION update_dso_inteligente();

-- ==========================================
-- FUNCIÓN CORREGIDA PARA EDPs CRÍTICOS
-- ==========================================

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
        (CURRENT_DATE - TO_DATE(e.fecha_envio_cliente::text, 'YYYYMMDD'))::INTEGER as dias_sin_respuesta
    FROM edp e
    WHERE e.fecha_envio_cliente IS NOT NULL
    AND e.fecha_conformidad IS NULL
    AND e.dso_actual > limite_dias
    AND e.estado NOT IN ('PAGADO', 'CANCELADO')
    ORDER BY e.dso_actual DESC, e.monto_aprobado DESC;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- CALCULAR DSO PARA DATOS EXISTENTES
-- ==========================================

-- Forzar recálculo de todos los EDPs existentes
UPDATE edp SET updated_at = CURRENT_TIMESTAMP WHERE id = id;

-- ==========================================
-- VERIFICACIÓN DE LA CORRECCIÓN
-- ==========================================

-- Verificar que los cálculos funcionan correctamente
SELECT 
    n_edp,
    fecha_envio_cliente,
    fecha_conformidad,
    dias_en_cliente,
    dso_actual,
    categoria_aging,
    esta_vencido,
    CASE 
        WHEN fecha_conformidad IS NOT NULL THEN 'COMPLETADO'
        WHEN fecha_envio_cliente IS NOT NULL THEN 'PENDIENTE'
        ELSE 'NO_ENVIADO'
    END as status_verificacion
FROM edp 
WHERE fecha_envio_cliente IS NOT NULL
ORDER BY dso_actual DESC NULLS LAST
LIMIT 10;

-- ==========================================
-- COMENTARIOS DE LA CORRECCIÓN
-- ==========================================

/*
🔧 CORRECCIÓN APLICADA

PROBLEMA ORIGINAL:
- fecha_envio_cliente y fecha_conformidad son INTEGER (formato YYYYMMDD)
- La función intentaba usar EXTRACT() con tipos incorrectos
- PostgreSQL no podía hacer la conversión automáticamente

SOLUCIÓN:
- Usar TO_DATE(campo::text, 'YYYYMMDD') para convertir INTEGER a DATE
- Hacer operaciones aritméticas directas entre fechas (DATE - DATE = INTEGER días)
- Mantener la misma lógica pero con tipos correctos

RESULTADO:
- dso_actual: Días entre fechas (INTEGER)
- dias_en_cliente: Días reales cuando hay conformidad (INTEGER)
- categoria_aging: Clasificación automática basada en días
- esta_vencido: Boolean basado en límite de 30 días

FORMATO DE FECHAS:
- Input: 20250128 (INTEGER)
- Conversión: TO_DATE('20250128', 'YYYYMMDD') = 2025-01-28 (DATE)
- Cálculo: 2025-01-28 - 2025-01-15 = 13 (INTEGER días)
*/ 