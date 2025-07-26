# 📧 SISTEMA DE NOTIFICACIONES POR EMAIL - PAGORA

## 🎯 **Descripción General**

El sistema de notificaciones por email de Pagora permite enviar alertas automáticas y manuales sobre el estado de los EDPs y métricas importantes del negocio. Está diseñado para mantener informados a los managers y administradores sobre eventos críticos que requieren atención inmediata.

## ✨ **Características Principales**

### 📧 **Tipos de Notificaciones**

1. **🚨 Alertas Críticas de EDPs**

   - EDPs con más de 60 días sin movimiento
   - Envío automático diario
   - Envío manual bajo demanda

2. **💰 Recordatorios de Pago**

   - EDPs entre 30-60 días pendientes
   - Envío automático diario
   - Envío manual bajo demanda

3. **📊 Resúmenes Semanales**

   - KPIs principales del negocio
   - Métricas de rendimiento
   - Envío automático los lunes

4. **⚠️ Alertas del Sistema**
   - Errores críticos del sistema
   - Mantenimiento programado
   - Envío manual bajo demanda

### 🔧 **Configuración Automática**

- **Tareas Celery** programadas para envío automático
- **Plantillas HTML** profesionales y responsivas
- **Gestión de destinatarios** por rol de usuario
- **Configuración flexible** mediante variables de entorno

## 🛠️ **Instalación y Configuración**

### **Paso 1: Instalar Dependencias**

Las dependencias ya están incluidas en `requirements.txt`:

```bash
Flask-Mail==0.9.1
```

### **Paso 2: Configurar Gmail SMTP**

#### **A. Habilitar Verificación en 2 Pasos**

1. Ve a [Mi Cuenta de Google](https://myaccount.google.com/)
2. Ve a "Seguridad"
3. Habilita "Verificación en 2 pasos"

#### **B. Generar Contraseña de Aplicación**

1. Ve a "Contraseñas de aplicación"
2. Selecciona "Otra" y nombra la app (ej: "Pagora EDP System")
3. Copia la contraseña de 16 caracteres generada

#### **C. Configurar Variables de Entorno**

Crea o edita tu archivo `.env` con las siguientes variables:

```bash
# Configuración SMTP Gmail
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=tu-email@gmail.com
MAIL_PASSWORD=tu-app-password-de-16-caracteres
MAIL_DEFAULT_SENDER=tu-email@gmail.com
MAIL_MAX_EMAILS=100

# Configuración de Notificaciones
ENABLE_CRITICAL_ALERTS=True
ENABLE_PAYMENT_REMINDERS=True
ENABLE_WEEKLY_SUMMARY=True
ENABLE_SYSTEM_ALERTS=True

# Umbrales de Alertas
CRITICAL_EDP_DAYS=60
PAYMENT_REMINDER_DAYS=30
WEEKLY_SUMMARY_DAY=monday
```

### **Paso 3: Verificar Configuración**

Una vez configurado, puedes verificar el estado del sistema:

```bash
# Verificar estado del email
curl -X GET "http://localhost:5000/api/email/status" \
  -H "Authorization: Bearer tu-token"

# Enviar email de prueba
curl -X POST "http://localhost:5000/api/email/test" \
  -H "Authorization: Bearer tu-token"
```

## 📋 **API Endpoints**

### **Estado del Sistema**

#### **GET /api/email/status**

Obtiene el estado actual del sistema de email.

**Respuesta:**

```json
{
  "success": true,
  "data": {
    "enabled": true,
    "configured": true,
    "server": "smtp.gmail.com",
    "port": 587,
    "use_tls": true,
    "default_sender": "miempresa@gmail.com",
    "features": {
      "critical_alerts": true,
      "payment_reminders": true,
      "weekly_summary": true,
      "system_alerts": true
    },
    "thresholds": {
      "critical_edp_days": 60,
      "payment_reminder_days": 30,
      "weekly_summary_day": "monday"
    }
  }
}
```

### **Pruebas del Sistema**

#### **POST /api/email/test**

Envía un email de prueba para verificar la configuración.

**Respuesta:**

```json
{
  "success": true,
  "message": "Test email queued successfully",
  "task_id": "task-uuid-here"
}
```

#### **GET /api/email/test/status/{task_id}**

Verifica el estado de un email de prueba.

**Respuesta:**

```json
{
  "state": "SUCCESS",
  "status": "Test email sent successfully!",
  "result": {
    "success": true,
    "recipients_count": 2,
    "message": "Test email sent successfully"
  }
}
```

### **Envío Manual de Notificaciones**

#### **POST /api/email/send-critical-alerts**

Envía manualmente alertas de EDPs críticos.

#### **POST /api/email/send-payment-reminders**

Envía manualmente recordatorios de pago.

#### **POST /api/email/send-weekly-summary**

Envía manualmente el resumen semanal.

#### **POST /api/email/send-system-alert**

Envía una alerta del sistema personalizada.

**Body:**

```json
{
  "title": "Mantenimiento Programado",
  "description": "El sistema estará en mantenimiento el próximo domingo de 2:00 AM a 4:00 AM.",
  "severity": "medium"
}
```

### **Gestión de Destinatarios**

#### **GET /api/email/recipients**

Obtiene la lista de destinatarios por rol.

**Respuesta:**

```json
{
  "success": true,
  "data": {
    "manager": [
      {
        "email": "manager@empresa.com",
        "username": "manager",
        "nombre_completo": "Juan Manager"
      }
    ],
    "admin": [
      {
        "email": "admin@empresa.com",
        "username": "admin",
        "nombre_completo": "Ana Admin"
      }
    ]
  }
}
```

### **Estado de Tareas**

#### **GET /api/email/task-status/{task_id}**

Verifica el estado de cualquier tarea de email.

## 🔄 **Tareas Automáticas (Celery)**

### **Programación de Tareas**

Las siguientes tareas se ejecutan automáticamente:

| Tarea                      | Frecuencia            | Descripción                    |
| -------------------------- | --------------------- | ------------------------------ |
| `send_critical_edp_alerts` | Diaria (00:00)        | Envía alertas de EDPs críticos |
| `send_payment_reminders`   | Diaria (00:00)        | Envía recordatorios de pago    |
| `send_weekly_summary`      | Semanal (Lunes 09:00) | Envía resumen semanal          |

### **Configuración de Celery**

Las tareas están configuradas en `edp_mvp/app/__init__.py`:

```python
celery.conf.beat_schedule = {
    "send-critical-alerts": {
        "task": "edp_mvp.app.tasks.email_tasks.send_critical_edp_alerts",
        "schedule": 86400,  # Daily at midnight
    },
    "send-payment-reminders": {
        "task": "edp_mvp.app.tasks.email_tasks.send_payment_reminders",
        "schedule": 86400,  # Daily at midnight
    },
    "send-weekly-summary": {
        "task": "edp_mvp.app.tasks.email_tasks.send_weekly_summary",
        "schedule": 604800,  # Weekly (Monday at 9:00 AM)
    },
}
```

## 📧 **Plantillas de Email**

### **Alertas Críticas de EDPs**

**Asunto:** `🚨 ALERTA CRÍTICA: EDP {n_edp} requiere atención inmediata`

**Contenido:**

- Detalles del EDP crítico
- Información del cliente y proyecto
- Monto y días sin movimiento
- Acciones recomendadas
- Enlace directo al EDP en el sistema

### **Recordatorios de Pago**

**Asunto:** `💰 Recordatorio de Pago: EDP {n_edp}`

**Contenido:**

- Detalles del EDP pendiente
- Información del cliente y proyecto
- Monto y días pendientes
- Enlace directo al EDP en el sistema

### **Resúmenes Semanales**

**Asunto:** `📊 Resumen Semanal - {fecha}`

**Contenido:**

- KPIs principales (Total EDPs, Monto Total, DSO Promedio)
- EDPs críticos
- Actividad de la semana (EDPs aprobados, pagados, monto cobrado)
- Enlace al dashboard completo

### **Alertas del Sistema**

**Asunto:** `⚠️ Alerta del Sistema: {título}`

**Contenido:**

- Título y descripción de la alerta
- Severidad (baja, media, alta, crítica)
- Timestamp de la alerta

## 🔧 **Personalización**

### **Modificar Umbrales**

Puedes modificar los umbrales de alertas en las variables de entorno:

```bash
# EDPs críticos después de 45 días (en lugar de 60)
CRITICAL_EDP_DAYS=45

# Recordatorios después de 20 días (en lugar de 30)
PAYMENT_REMINDER_DAYS=20

# Resumen semanal los viernes (en lugar de lunes)
WEEKLY_SUMMARY_DAY=friday
```

### **Habilitar/Deshabilitar Funciones**

```bash
# Deshabilitar recordatorios de pago
ENABLE_PAYMENT_REMINDERS=False

# Deshabilitar resúmenes semanales
ENABLE_WEEKLY_SUMMARY=False
```

### **Personalizar Plantillas**

Las plantillas HTML se encuentran en `edp_mvp/app/services/email_service.py` en los métodos `_render_*_template()`.

## 🚨 **Solución de Problemas**

### **Error: "Email service not configured"**

**Causa:** Las variables de entorno de email no están configuradas.

**Solución:**

1. Verificar que todas las variables MAIL\_\* estén configuradas
2. Verificar que MAIL_USERNAME y MAIL_PASSWORD no estén vacíos
3. Verificar que MAIL_DEFAULT_SENDER esté configurado

### **Error: "Authentication failed"**

**Causa:** Credenciales de Gmail incorrectas.

**Solución:**

1. Verificar que la verificación en 2 pasos esté habilitada
2. Generar una nueva contraseña de aplicación
3. Verificar que MAIL_PASSWORD use la contraseña de aplicación (no la normal)

### **Error: "Connection refused"**

**Causa:** Problemas de conectividad con Gmail.

**Solución:**

1. Verificar conexión a internet
2. Verificar que el firewall no bloquee el puerto 587
3. Verificar que MAIL_SERVER sea "smtp.gmail.com"

### **Emails no se envían automáticamente**

**Causa:** Celery no está ejecutándose o las tareas no están programadas.

**Solución:**

1. Verificar que Celery worker esté ejecutándose
2. Verificar que Celery beat esté ejecutándose
3. Verificar la configuración de beat_schedule

## 📊 **Monitoreo y Logs**

### **Logs del Sistema**

El sistema registra todas las actividades en los logs:

```
📧 Starting critical EDP alerts task
📧 Email service not configured, skipping critical alerts
📧 Critical alerts sent successfully to 3 recipients for 5 EDPs
❌ Error sending email: Authentication failed
```

### **Monitoreo de Tareas**

Puedes monitorear las tareas de Celery usando Flower:

```bash
# Acceder a Flower (si está configurado)
http://localhost:5555
```

### **Verificación de Estado**

```bash
# Verificar estado del sistema de email
curl -X GET "http://localhost:5000/api/email/status"

# Verificar destinatarios
curl -X GET "http://localhost:5000/api/email/recipients"
```

## 🔒 **Seguridad**

### **Buenas Prácticas**

1. **Nunca uses tu contraseña normal de Gmail**
2. **Usa siempre contraseñas de aplicación**
3. **Configura límites de envío (MAIL_MAX_EMAILS)**
4. **Revisa regularmente los logs de envío**
5. **Configura solo los destinatarios necesarios**

### **Configuración de Producción**

Para producción, considera:

1. **Usar un servicio de email dedicado** (SendGrid, Mailgun)
2. **Configurar SPF, DKIM y DMARC**
3. **Implementar rate limiting**
4. **Monitorear métricas de entrega**

## 📈 **Métricas y Analytics**

### **Métricas Disponibles**

- Emails enviados por tipo
- Tasa de entrega exitosa
- Destinatarios por rol
- Frecuencia de alertas críticas
- Tiempo de respuesta a alertas

### **Dashboard de Email**

Puedes crear un dashboard específico para monitorear el sistema de email usando los endpoints de la API.

## 🎯 **Próximas Mejoras**

### **Funcionalidades Planificadas**

1. **Plantillas personalizables** por empresa
2. **Suscripciones individuales** a tipos de alertas
3. **Frecuencias personalizables** por usuario
4. **Integración con Slack/Teams**
5. **Analytics avanzados** de envío
6. **Sistema de confirmación** de lectura

### **Optimizaciones Técnicas**

1. **Rate limiting** inteligente
2. **Retry automático** con backoff exponencial
3. **Compresión** de plantillas HTML
4. **Cache** de destinatarios
5. **Bulk sending** optimizado

---

## 📞 **Soporte**

Para soporte técnico o preguntas sobre el sistema de email:

1. Revisa los logs del sistema
2. Verifica la configuración de variables de entorno
3. Prueba el envío manual de emails
4. Consulta la documentación de Flask-Mail
5. Revisa la configuración de Gmail SMTP
