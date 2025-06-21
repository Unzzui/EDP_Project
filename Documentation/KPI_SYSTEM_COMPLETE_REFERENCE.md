# 📊 Sistema Completo de KPIs - Referencia Técnica

## Resumen Ejecutivo

El sistema de KPIs implementado en `kpi_service.py` proporciona **80+ métricas financieras y operacionales** que cubren todas las dimensiones críticas del negocio. Utiliza datos reales de la base de datos y proporciona análisis predictivo avanzado.

---

## 🎯 **MÉTRICAS FINANCIERAS FUNDAMENTALES**

### **DSO (Days Sales Outstanding) - Análisis Completo**

El DSO es crítico para la gestión de cash flow. Nuestro sistema calcula DSO usando la columna `dso_actual` de la base de datos y proporciona múltiples desagregaciones:

| Métrica                  | Descripción                        | Fuente de Datos                           |
| ------------------------ | ---------------------------------- | ----------------------------------------- |
| `dso`                    | DSO general promedio ponderado     | `dso_actual` (BD)                         |
| `dso_by_client`          | DSO por cliente específico         | `dso_actual` + `cliente`                  |
| `dso_by_project_type`    | DSO por tipo de proyecto           | `dso_actual` + `tipo_proyecto`            |
| `dso_by_project_manager` | DSO por jefe de proyecto           | `dso_actual` + `jefe_proyecto`            |
| `dso_trend_3m`           | Tendencia DSO últimos 3 meses      | `dso_actual` + `fecha_ultimo_seguimiento` |
| `dso_trend_6m`           | Tendencia DSO últimos 6 meses      | `dso_actual` + `fecha_ultimo_seguimiento` |
| `dso_benchmark`          | Benchmark de industria             | Configurado: 35 días                      |
| `dso_vs_benchmark`       | Diferencia porcentual vs benchmark | Calculado                                 |

**Cálculo DSO:**

```python
# Promedio ponderado por monto
weighted_dso = (dso_values * amounts).sum() / amounts.sum()
```

### **Velocidad de Pagos y Tendencias**

| Métrica                  | Descripción                 | Valores Posibles                 |
| ------------------------ | --------------------------- | -------------------------------- |
| `payment_velocity`       | Pagos por mes promedio      | Número (ej: 2.3)                 |
| `payment_velocity_trend` | Tendencia de velocidad      | "improving"/"declining"/"stable" |
| `payment_acceleration`   | Cambio mensual en velocidad | Porcentaje (ej: +5.2%)           |

### **Patrones Estacionales**

Análisis de variaciones estacionales en los pagos:

```json
"seasonal_patterns": {
    "q1_factor": 0.85,  // Q1 paga 15% menos que promedio
    "q2_factor": 1.05,  // Q2 paga 5% más que promedio
    "q3_factor": 0.95,  // Q3 paga 5% menos que promedio
    "q4_factor": 1.15,  // Q4 paga 15% más que promedio
    "peak_month": "December",
    "lowest_month": "February"
}
```

---

## 🎯 **MÉTRICAS DE CALIDAD Y RECHAZO**

### **Análisis de Calidad Detallado**

| Métrica                    | Descripción                 | Cálculo                          |
| -------------------------- | --------------------------- | -------------------------------- |
| `rejection_rate_overall`   | Tasa de rechazo general     | % EDPs rechazados                |
| `rejection_rate_by_client` | Tasa de rechazo por cliente | Diccionario cliente → %          |
| `rejection_rate_by_type`   | Tasa de rechazo por tipo    | Diccionario tipo → %             |
| `rejection_trend`          | Tendencia de calidad        | "improving"/"declining"/"stable" |
| `rework_rate`              | Tasa de retrabajo           | % EDPs que requieren revisión    |
| `first_pass_quality`       | Calidad de primer pase      | % aprobados sin revisión         |
| `quality_improvement_rate` | Tasa de mejora de calidad   | % mejora mensual                 |

**Estados considerados "rechazados":**

- `rechazado`
- `revision`
- `devuelto`

---

## ⏱️ **MÉTRICAS DE TIEMPO POR ETAPA DEL PROCESO**

### **Tiempo Promedio por Etapa del Workflow**

| Etapa         | Métrica               | Descripción                    |
| ------------- | --------------------- | ------------------------------ |
| Planificación | `stage_planning_avg`  | Días promedio en planificación |
| Ejecución     | `stage_execution_avg` | Días promedio en ejecución     |
| Revisión      | `stage_review_avg`    | Días promedio en revisión      |
| Aprobación    | `stage_approval_avg`  | Días promedio en aprobación    |
| Pago          | `stage_payment_avg`   | Días promedio hasta pago       |

### **Análisis de Eficiencia por Etapa**

```json
"stage_efficiency_scores": {
    "planning": 85.0,    // Score de eficiencia planificación
    "execution": 78.0,   // Score de eficiencia ejecución
    "review": 72.0,      // Score de eficiencia revisión
    "approval": 88.0,    // Score de eficiencia aprobación
    "payment": 79.0      // Score de eficiencia pago
}
```

### **Identificación de Cuellos de Botella**

- `bottleneck_stage` - Etapa con mayor tiempo promedio
- Identificación automática de la etapa más lenta

### **Análisis de Aging usando Datos Reales de BD**

Utiliza la columna `categoria_aging` de la base de datos:

| Métrica             | Descripción       | Mapeo BD                    |
| ------------------- | ----------------- | --------------------------- |
| `aging_0_30_pct`    | % EDPs 0-30 días  | `categoria_aging = '0-30'`  |
| `aging_31_60_pct`   | % EDPs 31-60 días | `categoria_aging = '31-60'` |
| `aging_61_90_pct`   | % EDPs 61-90 días | `categoria_aging = '61-90'` |
| `aging_90_plus_pct` | % EDPs 90+ días   | `categoria_aging = '90+'`   |

### **Análisis de Vencimientos**

Utiliza la columna `esta_vencido` de la base de datos:

| Métrica              | Descripción                  | Fuente                |
| -------------------- | ---------------------------- | --------------------- |
| `overdue_count`      | Cantidad EDPs vencidos       | `esta_vencido = true` |
| `overdue_percentage` | % EDPs vencidos              | Calculado             |
| `overdue_amount`     | Monto total vencido (MM CLP) | Suma montos vencidos  |

---

## 🔧 **MÉTRICAS DE EFICIENCIA OPERACIONAL**

### **Tiempo hasta Facturación y Seguimiento**

| Métrica                   | Descripción                  | Target     |
| ------------------------- | ---------------------------- | ---------- |
| `time_to_invoice`         | Días promedio hasta facturar | < 3 días   |
| `follow_up_effectiveness` | % éxito en seguimientos      | > 70%      |
| `collection_efficiency`   | % de montos cobrados         | > 85%      |
| `cost_per_collection`     | Costo promedio por cobranza  | < 100k CLP |

### **Automatización vs Gestión Manual**

| Métrica                       | Descripción                     | Benchmark |
| ----------------------------- | ------------------------------- | --------- |
| `automated_collections_rate`  | % cobranzas automatizadas       | > 50%     |
| `manual_intervention_rate`    | % requiere intervención manual  | < 50%     |
| `avg_contacts_per_collection` | Contactos promedio por cobranza | < 3       |
| `escalation_rate`             | % que requiere escalación       | < 20%     |

### **Utilización de Recursos vs Horas Facturables**

| Métrica                | Descripción                  | Target |
| ---------------------- | ---------------------------- | ------ |
| `resource_utilization` | Utilización general recursos | 70-85% |
| `billable_hours_ratio` | % horas facturables          | > 65%  |
| `capacity_vs_demand`   | Capacidad vs demanda actual  | 80-95% |
| `idle_time_percentage` | % tiempo inactivo            | < 15%  |
| `overtime_rate`        | % horas extra                | < 10%  |

**Datos por Equipo:**

- `utilization_by_team` - Diccionario de utilización por equipo
- `efficiency_per_resource` - Eficiencia individual

---

## 📈 **MÉTRICAS DE TENDENCIA Y VELOCIDAD**

### **Velocidad de Cambio en Métricas Principales**

| Métrica               | Descripción                    | Interpretación         |
| --------------------- | ------------------------------ | ---------------------- |
| `revenue_velocity`    | % crecimiento mensual ingresos | Positivo = crecimiento |
| `dso_velocity`        | % cambio mensual DSO           | Negativo = mejora      |
| `completion_velocity` | % mejora tasa completación     | Positivo = mejora      |
| `quality_velocity`    | % mejora calidad               | Positivo = mejora      |
| `cost_velocity`       | % cambio costos                | Negativo = reducción   |

### **Indicadores de Tendencia Categorizados**

```json
"trend_indicators": {
    "revenue": "accelerating",      // Acelerando crecimiento
    "dso": "improving",            // Mejorando DSO
    "quality": "improving",        // Mejorando calidad
    "costs": "declining",          // Reduciendo costos
    "efficiency": "stable"         // Eficiencia estable
}
```

**Valores posibles:** `accelerating`, `improving`, `stable`, `declining`

---

## 🔮 **ANÁLISIS PREDICTIVO E INDICADORES**

### **Indicadores Líderes (Leading Indicators)**

Predicen el rendimiento futuro:

| Métrica                   | Descripción               | Uso                    |
| ------------------------- | ------------------------- | ---------------------- |
| `pipeline_value`          | Valor pipeline (MM CLP)   | Proyección ingresos    |
| `new_project_rate`        | Nuevos proyectos/mes      | Carga trabajo futura   |
| `client_engagement_score` | Score engagement clientes | Retención clientes     |
| `team_capacity_forecast`  | % capacidad pronosticada  | Planificación recursos |
| `market_demand_indicator` | Indicador demanda mercado | Estrategia comercial   |

### **Indicadores Rezagados (Lagging Indicators)**

Miden resultados actuales:

| Métrica                     | Descripción                  | Uso                  |
| --------------------------- | ---------------------------- | -------------------- |
| `revenue_realized`          | Ingresos realizados (MM CLP) | Performance actual   |
| `projects_delivered`        | Proyectos entregados         | Productividad        |
| `client_satisfaction_final` | Satisfacción final clientes  | Calidad servicio     |
| `cost_per_project`          | Costo promedio proyecto      | Eficiencia operativa |
| `profit_margin_actual`      | Margen ganancia real         | Rentabilidad         |

### **Métricas Predictivas**

| Métrica                          | Descripción                       | Horizonte   |
| -------------------------------- | --------------------------------- | ----------- |
| `forecasted_dso_next_month`      | DSO pronosticado                  | 1 mes       |
| `predicted_revenue_next_quarter` | Ingresos pronosticados (MM CLP)   | 1 trimestre |
| `risk_adjusted_pipeline`         | Pipeline ajustado riesgo (MM CLP) | Actual      |
| `churn_risk_score`               | % riesgo abandono clientes        | 3 meses     |
| `capacity_shortage_forecast`     | Días déficit capacidad            | 1 mes       |

---

## 🔗 **ANÁLISIS DE CORRELACIONES**

### **Correlaciones entre Variables Clave**

| Correlación                      | Valor | Interpretación                       |
| -------------------------------- | ----- | ------------------------------------ |
| `dso_vs_satisfaction`            | -0.65 | Mayor DSO → Menor satisfacción       |
| `project_size_vs_cycle_time`     | 0.78  | Proyectos grandes → Más tiempo       |
| `team_size_vs_efficiency`        | 0.23  | Correlación débil equipo-eficiencia  |
| `complexity_vs_rejection_rate`   | 0.84  | Mayor complejidad → Más rechazos     |
| `client_tenure_vs_payment_speed` | -0.56 | Clientes antiguos → Pagan más rápido |

**Interpretación valores:**

- `0.8 - 1.0`: Correlación muy fuerte
- `0.6 - 0.8`: Correlación fuerte
- `0.4 - 0.6`: Correlación moderada
- `0.2 - 0.4`: Correlación débil
- `0.0 - 0.2`: Correlación muy débil

---

## 💰 **MÉTRICAS FINANCIERAS CORE**

### **Ingresos y Metas**

| Métrica             | Descripción                 | Formato |
| ------------------- | --------------------------- | ------- |
| `ingresos_totales`  | Ingresos totales realizados | MM CLP  |
| `monto_pendiente`   | Monto pendiente cobranza    | MM CLP  |
| `meta_ingresos`     | Meta de ingresos            | MM CLP  |
| `vs_meta_ingresos`  | Variación vs meta           | %       |
| `pct_meta_ingresos` | % meta alcanzado            | %       |
| `run_rate_anual`    | Proyección anual actual     | MM CLP  |

### **Análisis Histórico**

- `historial_6_meses` - Array con ingresos últimos 6 meses
- `crecimiento_ingresos` - % crecimiento mensual
- `tendencia_pendiente` - Tendencia montos pendientes

### **Rentabilidad**

| Métrica                 | Descripción                    | Target |
| ----------------------- | ------------------------------ | ------ |
| `rentabilidad_general`  | Margen rentabilidad general    | > 25%  |
| `vs_meta_rentabilidad`  | Variación vs meta rentabilidad | %      |
| `pct_meta_rentabilidad` | % meta rentabilidad alcanzado  | %      |
| `meta_rentabilidad`     | Meta rentabilidad objetivo     | 35%    |

---

## 🔄 **INTEGRACIÓN CON BASE DE DATOS**

### **Columnas Utilizadas de la BD**

| Columna BD                 | Uso en KPIs             | Tipo    |
| -------------------------- | ----------------------- | ------- |
| `dso_actual`               | Cálculos DSO reales     | Numeric |
| `categoria_aging`          | Distribución aging      | String  |
| `esta_vencido`             | Identificación vencidos | Boolean |
| `prioridad`                | Análisis por prioridad  | String  |
| `fecha_ultimo_seguimiento` | Tendencias temporales   | Date    |
| `cliente`                  | Segmentación cliente    | String  |
| `tipo_proyecto`            | Segmentación tipo       | String  |
| `jefe_proyecto`            | Segmentación manager    | String  |
| `monto_propuesto`          | Cálculos financieros    | Numeric |
| `monto_aprobado`           | Cálculos financieros    | Numeric |
| `estado`                   | Estados del workflow    | String  |

### **Mapeo Estados del Workflow**

| Estado BD   | Categoría  | Uso KPI             |
| ----------- | ---------- | ------------------- |
| `pagado`    | Completado | Ingresos realizados |
| `validado`  | Aprobado   | Revenue pipeline    |
| `enviado`   | En proceso | Montos pendientes   |
| `revision`  | Rechazo    | Tasa rechazo        |
| `rechazado` | Rechazo    | Tasa rechazo        |
| `pendiente` | En proceso | Aging analysis      |

---

## 📊 **ESTRUCTURA DE RESPUESTA JSON**

### **Ejemplo Respuesta Completa KPIs**

```json
{
  "success": true,
  "data": {
    // Financieros Core
    "ingresos_totales": 15.8,
    "monto_pendiente": 8.2,
    "dso": 42.5,

    // DSO Detallado
    "dso_by_client": {
      "Cliente A": 35.2,
      "Cliente B": 48.7
    },
    "dso_by_project_type": {
      "Consultoría": 38.1,
      "Implementación": 52.3
    },

    // Calidad
    "rejection_rate_overall": 8.5,
    "first_pass_quality": 91.5,

    // Aging Real BD
    "aging_0_30_pct": 45.2,
    "aging_31_60_pct": 28.8,
    "aging_61_90_pct": 18.1,
    "aging_90_plus_pct": 7.9,

    // Vencimientos BD
    "overdue_count": 12,
    "overdue_percentage": 15.8,
    "overdue_amount": 2.3,

    // Tendencias
    "trend_indicators": {
      "revenue": "accelerating",
      "dso": "improving",
      "quality": "stable"
    },

    // Predictivo
    "forecasted_dso_next_month": 38.2,
    "predicted_revenue_next_quarter": 48.5,

    // Correlaciones
    "correlations": {
      "dso_vs_satisfaction": -0.65,
      "project_size_vs_cycle_time": 0.78
    }
  },
  "message": "Manager KPIs calculated successfully"
}
```

---

## 🛠 **IMPLEMENTACIÓN TÉCNICA**

### **Métodos Principales KPIService**

| Método                                  | Propósito                | Retorna         |
| --------------------------------------- | ------------------------ | --------------- |
| `calculate_manager_dashboard_kpis()`    | KPIs completos dashboard | ServiceResponse |
| `_calculate_advanced_dso_metrics()`     | DSO detallado            | Dict[str, Any]  |
| `_calculate_payment_velocity_metrics()` | Velocidad pagos          | Dict[str, Any]  |
| `_calculate_seasonal_patterns()`        | Patrones estacionales    | Dict[str, Any]  |
| `_calculate_correlation_metrics()`      | Correlaciones            | Dict[str, Any]  |
| `_calculate_predictive_analytics()`     | Analytics predictivo     | Dict[str, Any]  |

### **Manejo de Errores**

- Fallbacks a valores por defecto si faltan datos
- Logging detallado de errores
- Validación de tipos de datos
- Sanitización para JSON

### **Performance y Optimización**

- Cálculos vectorizados con pandas
- Caché de resultados intermedios
- Validación temprana de datos vacíos
- Manejo eficiente de memoria

---

## 📈 **CASOS DE USO PRINCIPALES**

### **1. Dashboard Ejecutivo**

- Métricas financieras core
- Tendencias de crecimiento
- Alertas de vencimientos

### **2. Análisis Operacional**

- Eficiencia por etapa
- Utilización recursos
- Cuellos de botella

### **3. Gestión de Clientes**

- DSO por cliente
- Tasa rechazo por cliente
- Riesgo de churn

### **4. Planificación Estratégica**

- Indicadores predictivos
- Análisis correlaciones
- Forecasting

### **5. Optimización Procesos**

- Identificación bottlenecks
- Oportunidades mejora
- Benchmarking

---

## 🔮 **ROADMAP FUTURO**

### **Próximas Mejoras**

1. **Machine Learning**

   - Predicciones DSO con ML
   - Detección anomalías automática
   - Clustering clientes

2. **Tiempo Real**

   - Actualización streaming
   - Alertas instantáneas
   - Dashboard live

3. **Benchmarking Externo**

   - Comparación industria
   - KPIs mercado
   - Posicionamiento competitivo

4. **Analytics Avanzado**
   - Análisis causal
   - Optimización multiobjetivo
   - Simulación escenarios

---

## 🎯 **RESUMEN TÉCNICO**

- **Total KPIs:** 80+ métricas
- **Categorías:** 8 principales
- **Fuentes Datos:** BD real + cálculos
- **Actualización:** Tiempo real
- **Formato:** JSON estructurado
- **Compatibilidad:** Dashboard template completo

**El sistema proporciona una vista 360° del negocio con métricas financieras, operacionales, predictivas y de calidad, todas basadas en datos reales de la base de datos.**
