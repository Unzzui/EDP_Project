# 📊 CHULETA SQL - Base de Datos EDP

## 🏗️ ESTRUCTURA DE TABLAS

### Tablas principales:

- **`projects`** - Información de proyectos
- **`edp`** - Entrega de Productos (tabla central)
- **`edp_log`** - Historial de cambios en EDPs
- **`cost_header`** - Encabezados de costos
- **`cost_lines`** - Líneas de detalle de costos
- **`issues`** - Incidencias y problemas

---

## 🔍 CONSULTAS BÁSICAS

### 📋 Consultas de datos generales

```sql
-- Ver todos los EDPs
SELECT * FROM edp ORDER BY n_edp DESC;

-- Contar total de EDPs por estado
SELECT estado, COUNT(*) as total
FROM edp
GROUP BY estado
ORDER BY total DESC;

-- Ver EDPs recientes (últimos 30 días)
SELECT n_edp, proyecto, cliente, estado, fecha_emision
FROM edp
WHERE fecha_emision >= NOW() - INTERVAL '30 days'
ORDER BY fecha_emision DESC;

-- Ver todos los proyectos activos
SELECT project_id, proyecto, cliente, gestor, jefe_proyecto
FROM projects
WHERE fecha_fin_prevista > NOW() OR fecha_fin_prevista IS NULL;
```

### 💰 Consultas financieras

```sql
-- Total propuesto vs aprobado por proyecto
SELECT
    proyecto,
    COUNT(*) as total_edps,
    SUM(monto_propuesto) as total_propuesto,
    SUM(monto_aprobado) as total_aprobado,
    ROUND((SUM(monto_aprobado)::NUMERIC / SUM(monto_propuesto)::NUMERIC) * 100, 2) as porcentaje_aprobacion
FROM edp
WHERE monto_propuesto > 0
GROUP BY proyecto
ORDER BY total_aprobado DESC;

-- EDPs pendientes de pago
SELECT n_edp, proyecto, cliente, monto_aprobado, fecha_estimada_pago
FROM edp
WHERE estado = 'Aprobado'
AND fecha_estimada_pago < NOW()
AND monto_aprobado > 0
ORDER BY fecha_estimada_pago;

-- Resumen financiero por cliente
SELECT
    cliente,
    COUNT(*) as total_edps,
    SUM(monto_propuesto) as total_propuesto,
    SUM(monto_aprobado) as total_aprobado
FROM edp
GROUP BY cliente
ORDER BY total_aprobado DESC;
```

### 📊 Consultas de performance

```sql
-- Performance por gestor
SELECT
    gestor,
    COUNT(*) as total_edps,
    COUNT(CASE WHEN estado = 'Aprobado' THEN 1 END) as aprobados,
    ROUND(
        (COUNT(CASE WHEN estado = 'Aprobado' THEN 1 END)::NUMERIC / COUNT(*)::NUMERIC) * 100, 2
    ) as tasa_aprobacion
FROM edp
WHERE gestor IS NOT NULL
GROUP BY gestor
ORDER BY tasa_aprobacion DESC;

-- EDPs por mes de emisión
SELECT
    DATE_TRUNC('month', fecha_emision) as mes,
    COUNT(*) as total_edps,
    SUM(monto_propuesto) as total_propuesto
FROM edp
WHERE fecha_emision IS NOT NULL
GROUP BY DATE_TRUNC('month', fecha_emision)
ORDER BY mes DESC;
```

---

## 🔗 CONSULTAS CON JOINS

### 🔄 EDP con Log de cambios

```sql
-- Ver historial de cambios de un EDP específico
SELECT
    e.n_edp,
    e.proyecto,
    e.estado,
    l.fecha_hora,
    l.campo,
    l.antes,
    l.despues,
    l.usuario
FROM edp e
JOIN edp_log l ON e.id = l.edp_id
WHERE e.n_edp = 123  -- Cambiar por el número de EDP
ORDER BY l.fecha_hora DESC;

-- EDPs más modificados (con más logs)
SELECT
    e.n_edp,
    e.proyecto,
    e.estado,
    COUNT(l.id) as total_cambios
FROM edp e
LEFT JOIN edp_log l ON e.id = l.edp_id
GROUP BY e.id, e.n_edp, e.proyecto, e.estado
ORDER BY total_cambios DESC
LIMIT 10;
```

### 💼 Proyectos con Costos

```sql
-- Resumen de costos por proyecto
SELECT
    p.proyecto,
    p.cliente,
    COUNT(ch.id) as total_facturas,
    SUM(ch.importe_neto) as total_costos
FROM projects p
LEFT JOIN cost_header ch ON p.project_id = ch.project_id
GROUP BY p.id, p.proyecto, p.cliente
ORDER BY total_costos DESC;

-- Detalle de costos con líneas
SELECT
    ch.project_id,
    ch.proveedor,
    ch.factura,
    ch.fecha_factura,
    cl.descripcion_item,
    cl.cantidad,
    cl.precio_unitario,
    cl.subtotal
FROM cost_header ch
JOIN cost_lines cl ON ch.cost_id = cl.cost_id
WHERE ch.project_id = 'PROJ-001'  -- Cambiar por ID de proyecto
ORDER BY ch.fecha_factura DESC;
```

---

## 🚨 CONSULTAS DE MONITOREO

### ⚠️ Issues y problemas

```sql
-- Issues abiertas por severidad
SELECT
    severidad,
    COUNT(*) as total,
    COUNT(CASE WHEN estado = 'Abierto' THEN 1 END) as abiertas
FROM issues
GROUP BY severidad
ORDER BY
    CASE severidad
        WHEN 'Crítica' THEN 1
        WHEN 'Alta' THEN 2
        WHEN 'Media' THEN 3
        WHEN 'Baja' THEN 4
    END;

-- Issues sin resolver más antiguas
SELECT
    tipo,
    descripcion,
    proyecto_relacionado,
    usuario_asignado,
    timestamp as fecha_creacion,
    EXTRACT(DAYS FROM NOW() - timestamp) as dias_abierta
FROM issues
WHERE estado IN ('Abierto', 'En Proceso')
ORDER BY timestamp
LIMIT 10;
```

### 🔔 Alertas y notificaciones

```sql
-- EDPs vencidos sin respuesta
SELECT
    n_edp,
    proyecto,
    cliente,
    fecha_envio_cliente,
    EXTRACT(DAYS FROM NOW() - fecha_envio_cliente) as dias_sin_respuesta
FROM edp
WHERE estado = 'Enviado al Cliente'
AND fecha_envio_cliente < NOW() - INTERVAL '15 days'
ORDER BY fecha_envio_cliente;

-- Facturas próximas a vencer
SELECT
    factura,
    proveedor,
    project_id,
    fecha_vencimiento,
    importe_neto,
    EXTRACT(DAYS FROM fecha_vencimiento - NOW()) as dias_para_vencer
FROM cost_header
WHERE fecha_vencimiento BETWEEN NOW() AND NOW() + INTERVAL '7 days'
AND estado_costo != 'Pagado'
ORDER BY fecha_vencimiento;
```

---

## 📈 CONSULTAS AVANZADAS

### 📊 Análisis temporal

```sql
-- Tiempo promedio de aprobación
SELECT
    proyecto,
    AVG(EXTRACT(DAYS FROM fecha_conformidad - fecha_emision)) as dias_promedio_aprobacion,
    COUNT(*) as total_aprobados
FROM edp
WHERE estado = 'Aprobado'
AND fecha_emision IS NOT NULL
AND fecha_conformidad IS NOT NULL
GROUP BY proyecto
HAVING COUNT(*) >= 3  -- Solo proyectos con al menos 3 EDPs aprobados
ORDER BY dias_promedio_aprobacion;

-- Tendencia mensual de EDPs
SELECT
    DATE_TRUNC('month', fecha_emision) as mes,
    COUNT(*) as total_edps,
    COUNT(CASE WHEN estado = 'Aprobado' THEN 1 END) as aprobados,
    ROUND(AVG(monto_propuesto), 2) as monto_promedio
FROM edp
WHERE fecha_emision >= NOW() - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', fecha_emision)
ORDER BY mes;
```

### 🎯 KPIs principales

```sql
-- Dashboard de KPIs principales
SELECT
    'Total EDPs' as metrica,
    COUNT(*)::TEXT as valor
FROM edp
UNION ALL
SELECT
    'EDPs Aprobados',
    COUNT(*)::TEXT
FROM edp WHERE estado = 'Aprobado'
UNION ALL
SELECT
    'Monto Total Aprobado',
    TO_CHAR(SUM(monto_aprobado), 'FM999,999,999')
FROM edp WHERE estado = 'Aprobado'
UNION ALL
SELECT
    'Tasa de Aprobación %',
    ROUND(
        (COUNT(CASE WHEN estado = 'Aprobado' THEN 1 END)::NUMERIC / COUNT(*)::NUMERIC) * 100, 1
    )::TEXT
FROM edp
UNION ALL
SELECT
    'Issues Abiertas',
    COUNT(*)::TEXT
FROM issues WHERE estado IN ('Abierto', 'En Proceso');
```

---

## 🛠️ CONSULTAS DE MANTENIMIENTO

### 🔍 Verificación de datos

```sql
-- EDPs sin logs (posibles datos huérfanos)
SELECT e.n_edp, e.proyecto, e.estado
FROM edp e
LEFT JOIN edp_log l ON e.id = l.edp_id
WHERE l.edp_id IS NULL;

-- Verificar integridad referencial
SELECT
    'cost_header sin project' as problema,
    COUNT(*) as cantidad
FROM cost_header ch
LEFT JOIN projects p ON ch.project_id = p.project_id
WHERE p.project_id IS NULL

UNION ALL

SELECT
    'cost_lines sin header',
    COUNT(*)
FROM cost_lines cl
LEFT JOIN cost_header ch ON cl.cost_id = ch.cost_id
WHERE ch.cost_id IS NULL;
```

### 📋 Limpieza de datos

```sql
-- Duplicados potenciales en EDPs
SELECT n_edp, proyecto, COUNT(*) as duplicados
FROM edp
GROUP BY n_edp, proyecto
HAVING COUNT(*) > 1;

-- Registros con datos inconsistentes
SELECT n_edp, proyecto, estado, monto_propuesto, monto_aprobado
FROM edp
WHERE (estado = 'Aprobado' AND monto_aprobado IS NULL)
   OR (monto_aprobado > monto_propuesto AND monto_propuesto > 0);
```

---

## 🔧 FUNCIONES ÚTILES

### 📅 Formateo de fechas

```sql
-- Formato DD/MM/YYYY
TO_CHAR(fecha_emision, 'DD/MM/YYYY')

-- Formato con hora
TO_CHAR(fecha_hora, 'DD/MM/YYYY HH24:MI')

-- Solo mes y año
TO_CHAR(fecha_emision, 'MM/YYYY')
```

### 💰 Formateo de montos

```sql
-- Formato con separadores de miles
TO_CHAR(monto_aprobado, 'FM999,999,999')

-- Formato moneda
'$' || TO_CHAR(monto_aprobado, 'FM999,999,999.00')
```

### 🔢 Cálculos útiles

```sql
-- Días entre fechas
EXTRACT(DAYS FROM fecha_fin - fecha_inicio)

-- Porcentaje
ROUND((valor_1::NUMERIC / valor_2::NUMERIC) * 100, 2)

-- Promedio sin nulos
AVG(NULLIF(monto_aprobado, 0))
```

---

## 💡 TIPS PARA SUPABASE

### 🚀 Performance

- Usa `LIMIT` en consultas exploratorias
- Aprovecha los índices existentes (proyecto, cliente, estado, fechas)
- Para consultas grandes, considera usar `EXPLAIN ANALYZE`

### 🔐 Seguridad

- Siempre valida los parámetros de entrada
- Usa parámetros preparados en aplicaciones
- Considera Row Level Security (RLS) para multi-tenant

### 📊 API REST

```sql
-- Via URL en Supabase
GET /rest/v1/edp?select=n_edp,proyecto,estado&estado=eq.Aprobado

-- Con filtros múltiples
GET /rest/v1/edp?proyecto=ilike.*PROYECTO*&estado=eq.Aprobado&order=fecha_emision.desc
```
