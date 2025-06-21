# 🎯 DSO: Ejemplos Prácticos de Uso

## Diferencias Entre Campos DSO

| Campo             | Cuándo Se Calcula    | Qué Mide               | Uso Principal      |
| ----------------- | -------------------- | ---------------------- | ------------------ |
| `dias_en_cliente` | Solo con conformidad | Tiempo real en cliente | Análisis histórico |
| `dso_actual`      | Siempre (con envío)  | DSO actual/pendiente   | Seguimiento activo |

## 📊 Ejemplo 1: Dashboard DSO Actual

```sql
-- Ver tu DSO actual completo (como lo haces ahora)
SELECT
    n_edp,
    cliente,
    proyecto,
    fecha_envio_cliente,
    fecha_conformidad,
    dso_actual,           -- Siempre calculado
    categoria_aging,
    esta_vencido,
    CASE
        WHEN fecha_conformidad IS NOT NULL THEN 'COMPLETADO'
        ELSE 'PENDIENTE'
    END as status
FROM edp
WHERE fecha_envio_cliente IS NOT NULL
ORDER BY dso_actual DESC;
```

**Resultado:**

```
n_edp | cliente    | dso_actual | categoria_aging | esta_vencido | status
------|------------|------------|----------------|--------------|----------
1234  | Cliente A  | 45         | LENTO          | true         | PENDIENTE
1235  | Cliente B  | 12         | RAPIDO         | false        | COMPLETADO
1236  | Cliente C  | 38         | LENTO          | true         | PENDIENTE
```

## 📈 Ejemplo 2: KPIs Ejecutivos

```sql
-- DSO promedio ponderado (tu métrica clave)
SELECT
    ROUND(AVG(dso_actual), 1) as dso_promedio_dias,
    SUM(monto_aprobado) as monto_total_pendiente,
    COUNT(CASE WHEN esta_vencido THEN 1 END) as edps_vencidos,
    COUNT(*) as total_edps_activos
FROM edp
WHERE estado NOT IN ('PAGADO', 'CANCELADO')
AND fecha_envio_cliente IS NOT NULL;
```

**Resultado:**

```
dso_promedio_dias | monto_total_pendiente | edps_vencidos | total_activos
------------------|----------------------|---------------|---------------
32.5             | $1,250,000           | 8             | 25
```

## 🚨 Ejemplo 3: Alertas Críticas

```sql
-- EDPs que necesitan seguimiento urgente
SELECT * FROM get_edps_criticos_dso(30);
```

**Resultado:**

```
n_edp | cliente    | dso_actual | monto_aprobado | dias_sin_respuesta
------|------------|------------|----------------|--------------------
1234  | Cliente A  | 45         | $75,000        | 45
1238  | Cliente D  | 38         | $120,000       | 38
```

## 📊 Ejemplo 4: Análisis Comparativo

```sql
-- Comparar comportamiento histórico vs actual
SELECT
    cliente,
    -- Histórico (solo conformidades completadas)
    AVG(dias_en_cliente) as dias_promedio_historico,
    COUNT(CASE WHEN dias_en_cliente IS NOT NULL THEN 1 END) as edps_completados,

    -- Actual (incluyendo pendientes)
    AVG(dso_actual) as dso_promedio_actual,
    COUNT(CASE WHEN dso_actual IS NOT NULL THEN 1 END) as edps_total_enviados,

    -- Diferencia (indica si están siendo más lentos)
    AVG(dso_actual) - AVG(dias_en_cliente) as diferencia_velocidad
FROM edp
WHERE fecha_envio_cliente IS NOT NULL
GROUP BY cliente
ORDER BY diferencia_velocidad DESC;
```

**Resultado:**

```
cliente    | dias_historico | dso_actual | diferencia | interpretación
-----------|----------------|------------|------------|----------------
Cliente A  | 15.2          | 32.5       | +17.3      | MÁS LENTO ahora
Cliente B  | 22.1          | 18.4       | -3.7       | MÁS RÁPIDO ahora
Cliente C  | 28.5          | 28.1       | -0.4       | IGUAL velocidad
```

## 🎯 Ejemplo 5: Seguimiento Semanal

```sql
-- Tu reporte semanal de DSO
SELECT
    categoria_aging,
    COUNT(*) as cantidad,
    ROUND(AVG(dso_actual), 1) as dso_promedio,
    SUM(monto_aprobado) as monto_categoria,
    STRING_AGG(n_edp::text, ', ') as edps_incluidos
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
    END;
```

## 📱 Ejemplo 6: Consultas para Tu App/Dashboard

### A. Vista Rápida DSO

```sql
-- Para tu dashboard principal
SELECT * FROM v_dso_activos LIMIT 20;
```

### B. Análisis de Aging

```sql
-- Para gráfico de torta/barras
SELECT * FROM v_aging_analysis;
```

### C. DSO Ponderado

```sql
-- Para tu KPI principal
SELECT get_dso_promedio_ponderado() as dso_empresa;
```

### D. Top Clientes Problemáticos

```sql
-- Para acciones correctivas
SELECT * FROM get_edps_criticos_dso(45);
```

## 🔄 Ejemplo 7: Workflow Operacional

### Lunes (Revisión Semanal):

```sql
-- ¿Cómo está mi DSO esta semana?
SELECT
    COUNT(*) as edps_activos,
    AVG(dso_actual) as dso_promedio,
    COUNT(CASE WHEN esta_vencido THEN 1 END) as necesitan_seguimiento
FROM v_dso_activos;
```

### Miércoles (Seguimiento):

```sql
-- ¿Qué EDPs necesito contactar?
SELECT n_edp, cliente, dso_actual, monto_aprobado
FROM v_dso_activos
WHERE esta_vencido = true
ORDER BY monto_aprobado DESC;
```

### Viernes (Reporte):

```sql
-- ¿Cómo evolucionó mi DSO?
SELECT categoria_aging, COUNT(*) as cantidad, SUM(monto_aprobado) as monto
FROM v_dso_activos
GROUP BY categoria_aging;
```

## 💡 Ventajas del Sistema Dual

### ✅ `dias_en_cliente` - Para Análisis

- "El Cliente A históricamente tarda 15 días"
- "Nuestro tiempo promedio real es 22 días"
- "El Q3 fue mejor que Q2 en velocidad"

### ✅ `dso_actual` - Para Operaciones

- "Tengo $500K pendientes a más de 30 días"
- "El EDP 1234 lleva 45 días sin respuesta"
- "Mi DSO actual es 32.5 días"

## 🚀 Para Implementar

1. **Ejecuta el script DSO:**

```bash
psql -d tu_base_datos -f enhancement_dso_calculation.sql
```

2. **Verifica que funciona:**

```sql
SELECT n_edp, dias_en_cliente, dso_actual, categoria_aging
FROM edp LIMIT 5;
```

3. **Usa en tu dashboard:**

```sql
SELECT * FROM v_dso_activos;
```

¡Ahora tienes DSO completo que se actualiza automáticamente! 🎉
