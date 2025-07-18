# Especificaciones Funcionales - Dashboard Operations Visual Intelligence

## 🎯 Objetivo

Definir exactamente qué información debe contener cada elemento del dashboard y sus interacciones para maximizar la utilidad operacional.

---

## 📱 Reordenamiento de Secciones

### Prioridad Visual (de arriba hacia abajo):

1. **Alertas Operacionales** (mover al inicio)
2. **KPIs Principales**
3. **Estados de Pago (EDPs)**
4. **DSO por Jefe Proyecto**
5. **Forecast Ingresos 7 Días**
6. **Tendencia DSO**
7. **Resumen Ejecutivo**

---

## 🚨 Sección: Alertas Operacionales (REUBICADA AL INICIO)

### Contenido Actual Mejorado:

#### Alerta 1: EDPs Vencidos Críticos

**Información visible:**

- Número de EDPs: 29
- Monto total: $2,454,907,139 CLP
- Descripción: "EDPs con más de 90 días pendientes"

**Al hacer clic - Modal debe contener:**

- Lista completa de los 29 EDPs
- Columnas: Cliente, Proyecto ID, Monto, Días vencido, Jefe de Proyecto, Último contacto
- Ordenado por monto descendente
- Botones de acción: "Contactar Cliente", "Marcar como Disputado", "Asignar Seguimiento"
- Filtros: Por Jefe de Proyecto, Por rango de días

#### Alerta 2: DSO Elevado

**Información visible:**

- Valor actual: 148 días
- Referencia: "superior al target (60 días)"
- Diferencia: +88 días sobre target

**Al hacer clic - Modal debe contener:**

- Evolución DSO últimos 6 meses (gráfico simple)
- Desglose DSO por Jefe de Proyecto
- Top 5 proyectos que más impactan el DSO
- Acciones sugeridas para reducir DSO

#### Alerta 3: Bajo Flujo Proyectado

**Información visible:**

- Porcentaje: 0.0% del backlog cobrable en 30 días
- Estado: Crítico

**Al hacer clic - Modal debe contener:**

- Proyección de ingresos próximos 30 días
- Lista de EDPs próximos a vencer (siguientes 30 días)
- Comparación con mismo período año anterior
- Plan de acción para mejorar flujo

---

## 📊 Sección: KPIs Principales

### DSO Actual (149.0)

**Información visible mejorada:**

- Valor: 149 días
- Target: 60 días
- Variación: +89 días (+148% sobre target)
- Indicador visual de criticidad

**Tooltip on hover debe mostrar:**

- Definición: "Días Promedio de Cobranza"
- Fórmula: "Promedio días entre facturación y cobro"
- Último período: "Mes anterior: 145 días"

### CLP/Día Impacto (-3990k)

**Información visible:**

- Valor: -3,990k CLP/día
- Descripción: "Pérdida diaria por retrasos en cobro"

**Al hacer clic - Modal debe contener:**

- Desglose de la pérdida diaria por concepto
- Top 10 EDPs que más contribuyen a la pérdida
- Proyección de pérdida mensual/anual a ritmo actual
- Comparación con meses anteriores

### Forecast 7D (2502.2M)

**Información visible:**

- Valor: 2,502.2M CLP
- Período: "Próximos 7 días"

**Al hacer clic - Modal debe contener:**

- Desglose día por día de ingresos proyectados
- Lista de EDPs que componen cada día
- Nivel de confianza por día
- EDPs en riesgo de no cumplirse

### Meta Mensual (47%)

**Información visible mejorada:**

- Valor: 47%
- Descripción específica: "Meta de Cobro Mensual"
- Días restantes: 13 días
- Monto faltante para cumplir meta

**Al hacer clic - Modal debe contener:**

- Progreso diario hacia la meta
- Monto total de la meta mensual
- Monto ya cobrado vs pendiente
- Proyección de cumplimiento basada en tendencia actual
- EDPs críticos para cumplir la meta

---

## 🎯 Sección: Estados de Pago (EDPs)

### EDPs Críticos (48)

**Información visible actual:**

- Cantidad: 48 EDPs >60 días
- Monto: 4,481.0M CLP en riesgo

**Información adicional requerida:**

- Preview hover: "Pedro: 8 EDPs, Carolina: 12 EDPs, Ana: 15 EDPs, +13 más"

**Al hacer clic - Modal debe contener:**

- Lista completa de 48 EDPs críticos
- Columnas: Cliente, Proyecto, Monto, Días vencido, Jefe Proyecto, Estado actual
- Agrupación por Jefe de Proyecto
- Acciones por EDP: Llamar, Email, Marcar disputa, Registrar pago parcial
- Botones masivos: Email a todos, Generar reporte, Asignar recordatorios
- Filtros: Por jefe, por rango de monto, por días vencido

### Aging 31-60 (3 EDPs)

**Información visible actual:**

- Cantidad: 3 EDPs en zona warning
- Monto: 71.6M CLP

**Información adicional requerida:**

- Preview hover: "Cliente A: 45M (45d), Cliente B: 18M (38d), Cliente C: 8.6M (35d)"

**Al hacer clic - Modal debe contener:**

- Detalle de los 3 EDPs específicos
- Información de contacto del cliente
- Historial de comunicaciones previas
- Acciones preventivas sugeridas
- Programación de seguimiento

### Cobro Rápido (2 EDPs)

**Información visible actual:**

- Cantidad: 2 EDPs <30 días
- Monto: 158.9M CLP saludable

**Al hacer clic - Modal debe contener:**

- Detalle de los 2 EDPs próximos a cobrar
- Fecha estimada de cobro
- Acciones para asegurar el cobro
- Uso para proyección de flujo de caja

### Meta Gap

**Información visible actual:**

- Estado: "Sin datos de meta"

**Información requerida:**

- Una vez con datos: Diferencia entre meta y realidad
- Porcentaje de cumplimiento
- Acciones para cerrar la brecha

---

## 👥 Sección: DSO por Jefe Proyecto

### Pedro Rojas (154d)

**Información visible actual:**

- DSO: 154 días
- Monto: 804.1M CLP
- Proyectos: 9

**Información adicional requerida:**

- Indicador de urgencia: "8 EDPs críticos"
- Tendencia: Flecha ↗️ (empeorando), ↘️ (mejorando), ➡️ (estable)

**Tooltip hover debe mostrar:**

- Email: pedro.rojas@company.com
- Teléfono: +56 9 xxxx xxxx
- Última actualización: fecha

**Al hacer clic - Modal debe contener:**

- Resumen completo de performance de Pedro
- Lista de sus 9 proyectos con estado individual
- Desglose de los 8 EDPs críticos bajo su responsabilidad
- Historial de DSO últimos 6 meses
- Comparación con otros jefes de proyecto
- Acciones sugeridas para mejorar su DSO
- Botones: Llamar, Email, Programar reunión, Asignar apoyo

### Aplicar mismo formato para:

- Carolina López (147d, 1870.0M CLP, 17 proyectos)
- Ana Pérez (144d, 1089.3M CLP, 13 proyectos)
- Diego Bravo (135d, 948.0M CLP, 14 proyectos)

---

## 📈 Sección: Forecast Ingresos - Próximos 7 Días

### Información visible mejorada:

**Por cada día mostrar:**

- Monto proyectado (ej: 658.4M)
- Día de la semana (Lun, Mar, etc.)
- Porcentaje de confianza (85%, 72%, etc.)
- Clarificación: "% = Probabilidad de cobro"

**Al hacer clic en un día específico - Modal debe contener:**

- Lista de EDPs programados para ese día
- Cliente, proyecto, monto esperado por cada EDP
- Nivel de confianza individual por EDP
- Acciones para asegurar el cobro
- EDPs en riesgo de no cumplirse
- Contacto responsable por cada EDP

**Al hacer clic en el título de la sección - Modal debe contener:**

- Vista consolidada de los 7 días
- Total esperado vs meta semanal
- EDPs más críticos de la semana
- Plan de seguimiento semanal

---

## 📉 Sección: Tendencia DSO

### Información del gráfico mejorada:

**Debe mostrar claramente:**

- Línea de DSO actual vs Target DSO
- Últimos 6 meses de evolución
- Puntos de datos específicos al hover

**Al hacer clic - Modal debe contener:**

- Gráfico expandido con más detalle
- Eventos significativos que afectaron el DSO
- Comparación con año anterior
- Proyección de tendencia futura
- Factores que influyen en el DSO
- Plan de acción para mejora

---

## 📋 Sección: Resumen Ejecutivo

### Información AI mejorada:

**Texto actual:**
"El portfolio presenta ingresos registrados por $1,066.3M CLP. La eficiencia operacional es del 21.8%. Se detectaron 48 proyectos críticos que requieren atención."

**Información adicional requerida:**

- Elementos clickeables en el texto:
  - "$1,066.3M CLP" → Modal con desglose de ingresos
  - "21.8% eficiencia" → Modal con cálculo y comparación
  - "48 proyectos críticos" → Mismo modal que EDPs críticos

### KPIs Secundarios:

#### ROI Promedio (79.2%)

**Al hacer clic - Modal debe contener:**

- Desglose de ROI por proyecto
- Comparación con benchmarks de industria
- Proyectos con mejor y peor ROI
- Factores que afectan el ROI

#### Proyectos Completados (11)

**Al hacer clic - Modal debe contener:**

- Lista de los 11 proyectos completados
- Tiempo de ejecución por proyecto
- ROI final de cada proyecto completado
- Lecciones aprendidas

#### Satisfacción Cliente (22%)

**Al hacer clic - Modal debe contener:**

- Desglose de satisfacción por cliente
- Comentarios y feedback específico
- Clientes más y menos satisfechos
- Plan de acción para mejorar satisfacción
- Correlación entre satisfacción y tiempo de pago

---

## 🔄 Funcionalidades Transversales

### Filtros Globales (aplicables a todo el dashboard):

- **Rango de fechas**: Últimos 30 días, 90 días, 6 meses, año, personalizado
- **Jefe de Proyecto**: Filtro múltiple
- **Cliente**: Filtro múltiple
- **Estado de EDP**: Todos, Críticos, Warning, Saludables

### Acciones Globales:

- **Exportar datos**: PDF, Excel de la vista actual
- **Programar reporte**: Email automático diario/semanal
- **Actualizar datos**: Refresh manual
- **Configurar alertas**: Umbrales personalizables

### Tooltips Informativos (no complejos):

- **Definiciones**: Para términos técnicos (DSO, EDP, etc.)
- **Contexto**: Comparación con período anterior
- **Cálculos**: Fórmulas de métricas importantes

---

## 📊 Especificaciones de Modales

### Tamaño y Estructura:

- **Pequeño**: Previews simples, máximo 5 filas de datos
- **Mediano**: Listas completas, máximo 20 filas visibles (scroll para más)
- **Acciones**: Máximo 3 botones primarios por modal
- **Navegación**: Breadcrumb si el modal tiene sub-secciones

### Contenido Estándar de Modales:

- **Header**: Título claro + métrica principal
- **Body**: Tabla o lista ordenada por relevancia
- **Footer**: Acciones principales + botón cerrar
- **Filtros**: Solo si hay >10 elementos para mostrar

### Performance:

- **Carga**: Datos pre-cargados, apertura instantánea
- **Actualización**: Refresh automático cada 15 minutos
- **Offline**: Indicador si datos no están actualizados

---

## 🎯 Criterios de Éxito

### Métricas de Utilidad:

- **Tiempo hasta encontrar información crítica**: <10 segundos
- **Clics necesarios para acción**: Máximo 2 clics
- **Información visible sin scroll**: 80% de datos críticos
- **Resolución de problemas**: Información suficiente para decidir acción

### Validación de Contenido:

- **Cada modal debe responder**: "¿Qué hago con esta información?"
- **Cada métrica debe tener**: Contexto, tendencia y próxima acción
- **Cada alerta debe incluir**: Gravedad, impacto y solución sugerida
