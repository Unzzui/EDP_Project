# 🤔 ¿Qué Pasa Cuando NO Existe fecha_envio_cliente?

## 🎯 Comportamiento Actual del Sistema DSO

### Cuando `fecha_envio_cliente` es NULL:

| Campo             | Valor            | Explicación                                 |
| ----------------- | ---------------- | ------------------------------------------- |
| `dso_actual`      | **NULL**         | No se puede calcular DSO sin fecha de envío |
| `dias_en_cliente` | **NULL**         | No se puede calcular tiempo en cliente      |
| `categoria_aging` | **'SIN_ENVIAR'** | Categoría especial para EDPs no enviados    |
| `esta_vencido`    | **FALSE**        | No puede estar vencido si no se envió       |

## 📊 Casos Reales en Tu Operación

### **Caso 1: EDP Creado pero No Enviado**

```sql
-- EDP recién creado, aún no enviado al cliente
INSERT INTO edp (n_edp, cliente, proyecto, monto_aprobado, estado)
VALUES (1250, 'Cliente A', 'Proyecto X', 50000, 'APROBADO');

-- Resultado automático:
-- dso_actual = NULL
-- categoria_aging = 'SIN_ENVIAR'
-- esta_vencido = FALSE
```

### **Caso 2: EDP en Preparación**

```sql
-- EDP que está siendo preparado para envío
SELECT
    n_edp,
    cliente,
    estado,
    dso_actual,           -- NULL
    categoria_aging,      -- 'SIN_ENVIAR'
    esta_vencido         -- FALSE
FROM edp
WHERE fecha_envio_cliente IS NULL
AND estado IN ('APROBADO', 'EN_PREPARACION');
```

## 🔍 Consultas Útiles para EDPs Sin Envío

### **1. Ver EDPs Pendientes de Envío**

```sql
SELECT
    n_edp,
    cliente,
    proyecto,
    monto_aprobado,
    estado,
    created_at,
    -- Días desde creación (no desde envío)
    CURRENT_DATE - created_at::date as dias_desde_creacion
FROM edp
WHERE fecha_envio_cliente IS NULL
AND estado NOT IN ('CANCELADO', 'RECHAZADO')
ORDER BY created_at;
```

### **2. EDPs Que Deberían Haberse Enviado**

```sql
-- EDPs creados hace más de X días pero no enviados
SELECT
    n_edp,
    cliente,
    proyecto,
    estado,
    created_at,
    CURRENT_DATE - created_at::date as dias_sin_enviar,
    CASE
        WHEN CURRENT_DATE - created_at::date > 7 THEN 'URGENTE'
        WHEN CURRENT_DATE - created_at::date > 3 THEN 'REVISAR'
        ELSE 'OK'
    END as prioridad_envio
FROM edp
WHERE fecha_envio_cliente IS NULL
AND estado = 'APROBADO'
AND CURRENT_DATE - created_at::date > 2
ORDER BY dias_sin_enviar DESC;
```

### **3. Resumen de EDPs por Estado de Envío**

```sql
SELECT
    CASE
        WHEN fecha_envio_cliente IS NULL THEN 'NO_ENVIADO'
        WHEN fecha_conformidad IS NULL THEN 'ENVIADO_PENDIENTE'
        ELSE 'COMPLETADO'
    END as status_envio,
    COUNT(*) as cantidad,
    SUM(monto_aprobado) as monto_total,
    AVG(CASE
        WHEN fecha_envio_cliente IS NULL THEN CURRENT_DATE - created_at::date
        ELSE dso_actual
    END) as dias_promedio
FROM edp
WHERE estado NOT IN ('CANCELADO', 'PAGADO')
GROUP BY
    CASE
        WHEN fecha_envio_cliente IS NULL THEN 'NO_ENVIADO'
        WHEN fecha_conformidad IS NULL THEN 'ENVIADO_PENDIENTE'
        ELSE 'COMPLETADO'
    END
ORDER BY cantidad DESC;
```

## 🚨 Vista Completa: Dashboard con Todos los Estados

```sql
CREATE OR REPLACE VIEW v_dashboard_completo AS
SELECT
    n_edp,
    cliente,
    proyecto,
    monto_aprobado,
    estado,
    fecha_envio_cliente,
    fecha_conformidad,

    -- Campos DSO (pueden ser NULL)
    dso_actual,
    dias_en_cliente,
    categoria_aging,
    esta_vencido,

    -- Estado consolidado
    CASE
        WHEN fecha_envio_cliente IS NULL THEN 'NO_ENVIADO'
        WHEN fecha_conformidad IS NULL THEN 'PENDIENTE_CONFORMIDAD'
        ELSE 'CONFORMIDAD_RECIBIDA'
    END as status_proceso,

    -- Días relevantes según el estado
    CASE
        WHEN fecha_envio_cliente IS NULL THEN CURRENT_DATE - created_at::date
        WHEN fecha_conformidad IS NULL THEN CURRENT_DATE - fecha_envio_cliente::date
        ELSE fecha_conformidad::date - fecha_envio_cliente::date
    END as dias_relevantes,

    -- Prioridad de acción
    CASE
        WHEN fecha_envio_cliente IS NULL AND CURRENT_DATE - created_at::date > 5 THEN 'ENVIAR_URGENTE'
        WHEN fecha_envio_cliente IS NOT NULL AND esta_vencido THEN 'SEGUIMIENTO_URGENTE'
        WHEN fecha_envio_cliente IS NOT NULL AND dso_actual > 45 THEN 'SEGUIMIENTO_NORMAL'
        WHEN fecha_envio_cliente IS NULL THEN 'PREPARAR_ENVIO'
        ELSE 'OK'
    END as accion_requerida

FROM edp
WHERE estado NOT IN ('CANCELADO', 'PAGADO')
ORDER BY
    CASE
        WHEN fecha_envio_cliente IS NULL AND CURRENT_DATE - created_at::date > 5 THEN 1
        WHEN esta_vencido THEN 2
        WHEN dso_actual > 45 THEN 3
        ELSE 4
    END,
    monto_aprobado DESC;
```

## 📈 KPIs que Incluyen EDPs Sin Envío

### **1. Tiempo Total del Proceso**

```sql
-- Desde creación hasta conformidad (proceso completo)
SELECT
    AVG(
        CASE
            WHEN fecha_conformidad IS NOT NULL THEN
                fecha_conformidad::date - created_at::date
            ELSE
                CURRENT_DATE - created_at::date
        END
    ) as dias_proceso_completo_promedio
FROM edp
WHERE estado NOT IN ('CANCELADO', 'PAGADO');
```

### **2. Eficiencia de Envío**

```sql
-- ¿Qué tan rápido enviamos después de aprobar?
SELECT
    AVG(fecha_envio_cliente::date - created_at::date) as dias_promedio_hasta_envio,
    COUNT(CASE WHEN fecha_envio_cliente IS NULL THEN 1 END) as edps_sin_enviar,
    COUNT(*) as total_edps_aprobados
FROM edp
WHERE estado = 'APROBADO';
```

### **3. Embudo de Proceso**

```sql
-- Ver el flujo completo
SELECT
    'EDPs Creados' as etapa,
    COUNT(*) as cantidad,
    SUM(monto_aprobado) as monto
FROM edp WHERE estado NOT IN ('CANCELADO', 'PAGADO')

UNION ALL

SELECT
    'EDPs Enviados' as etapa,
    COUNT(*) as cantidad,
    SUM(monto_aprobado) as monto
FROM edp WHERE fecha_envio_cliente IS NOT NULL AND estado NOT IN ('CANCELADO', 'PAGADO')

UNION ALL

SELECT
    'EDPs con Conformidad' as etapa,
    COUNT(*) as cantidad,
    SUM(monto_aprobado) as monto
FROM edp WHERE fecha_conformidad IS NOT NULL AND estado NOT IN ('CANCELADO', 'PAGADO')

ORDER BY cantidad DESC;
```

## 🎯 Recomendaciones Operacionales

### **Para EDPs Sin Envío:**

1. **Monitorear tiempo desde creación** - No DSO, pero sí tiempo interno
2. **Alertas por días sin enviar** - Ej: más de 5 días sin envío
3. **Priorizar por monto** - EDPs grandes sin enviar son críticos
4. **Revisar bloqueos** - ¿Por qué no se han enviado?

### **Consulta de Alertas Diarias:**

```sql
-- Tu consulta diaria de pendientes
SELECT
    'EDPs sin enviar (>5 días)' as alerta,
    COUNT(*) as cantidad,
    SUM(monto_aprobado) as monto_en_riesgo
FROM edp
WHERE fecha_envio_cliente IS NULL
AND CURRENT_DATE - created_at::date > 5
AND estado = 'APROBADO'

UNION ALL

SELECT
    'EDPs enviados vencidos' as alerta,
    COUNT(*) as cantidad,
    SUM(monto_aprobado) as monto_en_riesgo
FROM edp
WHERE esta_vencido = true;
```

## 💡 Resumen

**Cuando NO hay `fecha_envio_cliente`:**

- ✅ **Sistema no falla** - Maneja NULL correctamente
- ✅ **Categoría especial** - 'SIN_ENVIAR'
- ✅ **DSO = NULL** - No se puede calcular sin envío
- ✅ **Métricas alternativas** - Días desde creación
- ✅ **Alertas específicas** - Para EDPs no enviados

**Tu flujo queda así:**

1. **EDP Creado** → `categoria_aging = 'SIN_ENVIAR'`
2. **EDP Enviado** → `dso_actual` se calcula automáticamente
3. **EDP con Conformidad** → `dias_en_cliente` se calcula también

¡El sistema es robusto y maneja todos los estados! 🎉
