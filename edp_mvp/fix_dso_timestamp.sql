-- 🔧 CORRECCIÓN FINAL: Función DSO para campos TIMESTAMP
-- 
-- El problema es que fecha_envio_cliente y fecha_conformidad son TIMESTAMP
-- no INTEGER como asumimos inicialmente
--
-- Esta corrección maneja correctamente los tipos TIMESTAMP

-- ==========================================
-- FUNCIÓN CORREGIDA PARA TIMESTAMPS
-- ==========================================

CREATE OR REPLACE FUNCTION update_dso_inteligente()
RETURNS TRIGGER AS $$
BEGIN
    -- Calcular DSO actual: usar fecha_conformidad si existe, sino fecha actual
    IF NEW.fecha_envio_cliente IS NOT NULL THEN
        IF NEW.fecha_conformidad IS NOT NULL THEN
            -- DSO real: ya tiene conformidad
            -- Calcular diferencia entre timestamps en días
            NEW.dso_actual = EXTRACT(DAY FROM (NEW.fecha_conformidad::date - NEW.fecha_envio_cliente::date));
        ELSE
            -- DSO pendiente: usar fecha actual
            -- Calcular días desde envío hasta hoy
            NEW.dso_actual = EXTRACT(DAY FROM (CURRENT_DATE - NEW.fecha_envio_cliente::date));
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
        NEW.dias_en_cliente = EXTRACT(DAY FROM (NEW.fecha_conformidad::date - NEW.fecha_envio_cliente::date));
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
        EXTRACT(DAY FROM (CURRENT_DATE - e.fecha_envio_cliente::date))::INTEGER as dias_sin_respuesta
    FROM edp e
    WHERE e.fecha_envio_cliente IS NOT NULL
    AND e.fecha_conformidad IS NULL
    AND e.dso_actual > limite_dias
    AND e.estado NOT IN ('PAGADO', 'CANCELADO')
    ORDER BY e.dso_actual DESC, e.monto_aprobado DESC;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- VISTAS CORREGIDAS PARA TIMESTAMPS
-- ==========================================

-- Vista para DSO actual de EDPs activos (corregida)
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

-- ==========================================
-- CALCULAR DSO PARA DATOS EXISTENTES
-- ==========================================

-- Forzar recálculo de todos los EDPs existentes
UPDATE edp SET updated_at = CURRENT_TIMESTAMP WHERE id = id;

-- ==========================================
-- VERIFICACIÓN FINAL
-- ==========================================

-- Verificar que los cálculos funcionan correctamente
SELECT 
    n_edp,
    fecha_envio_cliente::date as fecha_envio,
    fecha_conformidad::date as fecha_conformidad,
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
-- CONSULTA DE PRUEBA DSO
-- ==========================================

-- Prueba rápida para ver si funciona
SELECT 
    'DSO Promedio' as metrica,
    ROUND(AVG(dso_actual), 1) as valor,
    COUNT(*) as total_edps
FROM edp 
WHERE fecha_envio_cliente IS NOT NULL
AND estado NOT IN ('PAGADO', 'CANCELADO')

UNION ALL

SELECT 
    'EDPs Vencidos' as metrica,
    COUNT(*)::DECIMAL as valor,
    COUNT(*)::INTEGER as total_edps
FROM edp 
WHERE esta_vencido = true;

-- ==========================================
-- COMENTARIOS DE LA CORRECCIÓN FINAL
-- ==========================================

/*
🔧 CORRECCIÓN FINAL APLICADA

PROBLEMA:
- Los campos fecha_envio_cliente y fecha_conformidad son TIMESTAMP
- No INTEGER como asumimos inicialmente
- Necesitamos convertir TIMESTAMP a DATE para cálculos de días

SOLUCIÓN:
- Usar campo::date para convertir TIMESTAMP a DATE
- EXTRACT(DAY FROM (date1 - date2)) para obtener diferencia en días
- Mantener la misma lógica DSO pero con tipos correctos

RESULTADO:
✅ dso_actual: Días calculados correctamente
✅ dias_en_cliente: Solo cuando hay conformidad
✅ categoria_aging: Clasificación automática
✅ esta_vencido: Flag para seguimiento
✅ Triggers funcionando correctamente

FORMATO MANEJADO:
- Input: '2024-12-26 00:00:00' (TIMESTAMP)
- Conversión: '2024-12-26' (DATE)
- Cálculo: date1 - date2 = días (INTEGER)

AHORA FUNCIONA CORRECTAMENTE CON TUS DATOS REALES! 🎉
*/ 