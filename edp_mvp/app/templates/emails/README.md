# Sistema de Templates de Email - Pagora EDP

## Estructura de Archivos

```
emails/
├── base_styles.css          # Estilos CSS base compartidos
├── base.html               # Template base para todos los emails
├── weekly_summary.html     # Template para resumen semanal
├── critical_alert.html     # Template para alertas críticas
├── payment_reminder.html   # Template para recordatorios de pago
├── system_alert.html       # Template para alertas del sistema
├── performance_report.html # Template para reportes de performance
├── bulk_critical_alerts.html # Template para alertas críticas masivas
└── text/                   # Templates de texto plano
    ├── weekly_summary.txt
    ├── critical_alert.txt
    ├── payment_reminder.txt
    ├── system_alert.txt
    ├── performance_report.txt
    └── bulk_critical_alerts.txt
```

## Filosofía de Diseño

Todos los templates siguen la filosofía **"Executive Suite"** (Light Mode) definida en `Documentation/Styles.md`:

### Características Principales:

- **Tipografía**: Inter para texto general, JetBrains Mono para datos numéricos
- **Paleta de colores**: Colores claros y profesionales
- **Gradientes**: Headers con gradientes modernos
- **Responsive**: Diseño adaptable a dispositivos móviles
- **Consistencia**: Estructura unificada en todos los emails

### Colores por Tipo de Email:

- **Resumen Semanal**: Azul (#0066cc)
- **Alertas Críticas**: Rojo (#dc2626)
- **Recordatorios de Pago**: Naranja (#f59e0b)
- **Alertas del Sistema**: Gris (#6b7280)
- **Reportes de Performance**: Verde (#059669)

## Uso en el Código

### Métodos de Renderizado:

```python
# HTML templates
html_body = self._render_template_safe('emails/template_name.html', **context)

# Text templates
text_body = self._render_text_template_safe('emails/text/template_name.txt', **context)
```

### Ejemplo de Uso:

```python
def send_weekly_summary(self, kpis_data, recipients):
    processed_kpis = self._process_kpis_data(kpis_data)

    html_body = self._render_template_safe(
        'emails/weekly_summary.html',
        processed_kpis=processed_kpis,
        date=datetime.now().strftime('%d/%m/%Y'),
        app_url=current_app.config.get('APP_URL')
    )

    text_body = self._render_text_template_safe(
        'emails/text/weekly_summary.txt',
        processed_kpis=processed_kpis,
        date=datetime.now().strftime('%d/%m/%Y')
    )

    return self.send_email(subject, recipients, html_body, text_body)
```

## Ventajas de la Nueva Estructura

1. **Separación de Responsabilidades**: HTML/CSS separado del código Python
2. **Mantenibilidad**: Fácil modificación de estilos sin tocar lógica
3. **Reutilización**: Estilos base compartidos entre templates
4. **Consistencia**: Diseño unificado en todos los emails
5. **Legibilidad**: Código Python más limpio y enfocado en lógica
6. **Escalabilidad**: Fácil agregar nuevos tipos de email

## Personalización

### Agregar Nuevo Tipo de Email:

1. Crear template HTML en `emails/nuevo_tipo.html`
2. Crear template de texto en `emails/text/nuevo_tipo.txt`
3. Agregar método en `EmailService` usando los templates
4. Opcional: Agregar estilos específicos en el template

### Modificar Estilos:

- **Estilos globales**: Editar `base_styles.css`
- **Estilos específicos**: Usar bloques `{% block theme_styles %}` en templates
- **Colores**: Seguir la paleta definida en `Styles.md`

## Compatibilidad

- **Clientes de Email**: Compatible con la mayoría de clientes modernos
- **Responsive**: Optimizado para móviles y desktop
- **Accesibilidad**: Contraste adecuado y estructura semántica
- **Fallbacks**: Versiones de texto plano para compatibilidad máxima
