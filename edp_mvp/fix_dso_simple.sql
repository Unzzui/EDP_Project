-- 🔧 CORRECCIÓN SIMPLIFICADA: Función DSO con aritmética directa
-- 
-- Eliminamos EXTRACT y usamos aritmética directa de fechas
-- que es más robusta y compatible con PostgreSQL

-- ==========================================
-- FUNCIÓN DSO SIMPLIFICADA
-- ==========================================

CREATE OR REPLACE FUNCTION update_dso_inteligente()
RETURNS TRIGGER AS $$
BEGIN
    -- Calcular DSO actual: usar fecha_conformidad si existe, sino fecha actual
    IF NEW.fecha_envio_cliente IS NOT NULL THEN
        IF NEW.fecha_conformidad IS NOT NULL THEN
            -- DSO real: ya tiene conformidad
            -- Aritmética directa de fechas (devuelve INTEGER automáticamente)
            NEW.dso_actual = NEW.fecha_conformidad::date - NEW.fecha_envio_cliente::date;
        ELSE
            -- DSO pendiente: usar fecha actual
            -- Aritmética directa con fecha actual
            NEW.dso_actual = CURRENT_DATE - NEW.fecha_envio_cliente::date;
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
    
    -- También calcular dias_en_cliente como antes (solo cuando hay conformidad)
    IF NEW.fecha_conformidad IS NOT NULL AND NEW.fecha_envio_cliente IS NOT NULL THEN
        NEW.dias_en_cliente = NEW.fecha_conformidad::date - NEW.fecha_envio_cliente::date;
    END IF;
    
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- ACTUALIZAR TRIGGER
-- ==========================================

DROP TRIGGER IF EXISTS trigger_update_dso_inteligente ON edp;
CREATE TRIGGER trigger_update_dso_inteligente
    BEFORE UPDATE ON edp
    FOR EACH ROW
    EXECUTE FUNCTION update_dso_inteligente();

-- ==========================================
-- FUNCIÓN SIMPLIFICADA PARA EDPs CRÍTICOS
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
        (CURRENT_DATE - e.fecha_envio_cliente::date) as dias_sin_respuesta
    FROM edp e
    WHERE e.fecha_envio_cliente IS NOT NULL
    AND e.fecha_conformidad IS NULL
    AND e.dso_actual > limite_dias
    AND e.estado NOT IN ('PAGADO', 'CANCELADO')
    ORDER BY e.dso_actual DESC, e.monto_aprobado DESC;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- FORZAR RECÁLCULO DE DATOS EXISTENTES
-- ==========================================

-- Actualizar todos los EDPs para que se recalculen los campos DSO
UPDATE edp SET updated_at = CURRENT_TIMESTAMP WHERE id = id;

-- ==========================================
-- VERIFICACIÓN SIMPLIFICADA
-- ==========================================

-- Probar que los cálculos funcionan
SELECT 
    n_edp,
    fecha_envio_cliente::date as envio,
    fecha_conformidad::date as conformidad,
    dias_en_cliente,
    dso_actual,
    categoria_aging,
    esta_vencido
FROM edp 
WHERE fecha_envio_cliente IS NOT NULL
ORDER BY dso_actual DESC NULLS LAST
LIMIT 5;

-- ==========================================
-- PRUEBA RÁPIDA DSO
-- ==========================================

-- Ver si los campos se calculan correctamente
SELECT 
    COUNT(*) as total_edps_con_envio,
    COUNT(CASE WHEN dso_actual IS NOT NULL THEN 1 END) as edps_con_dso,
    COUNT(CASE WHEN esta_vencido = true THEN 1 END) as edps_vencidos,
    ROUND(AVG(dso_actual), 1) as dso_promedio
FROM edp 
WHERE fecha_envio_cliente IS NOT NULL;

-- ==========================================
-- COMENTARIO FINAL
-- ==========================================

/*
🔧 SOLUCIÓN SIMPLIFICADA

CAMBIOS:
- Eliminamos EXTRACT() completamente
- Usamos aritmética directa: date1 - date2 = INTEGER días
- PostgreSQL maneja automáticamente la conversión
- Más simple y más compatible

ARITMÉTICA DE FECHAS EN POSTGRESQL:
- DATE - DATE = INTEGER (días de diferencia)
- CURRENT_DATE - timestamp::date = INTEGER días
- Más directo y sin problemas de tipos

RESULTADO:
✅ Sin errores de tipos
✅ Cálculo correcto de días
✅ Funciona con TIMESTAMP
✅ Lógica DSO intacta

AHORA DEBERÍA FUNCIONAR SIN ERRORES! 🎯
*/ 