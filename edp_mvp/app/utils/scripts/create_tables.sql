-- SQL para crear todas las tablas de Google Sheets en Supabase
-- Ejecutar en orden en el SQL Editor de Supabase

-- 1. Tabla Projects (primero, ya que es referenciada)
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(100) UNIQUE NOT NULL,
    proyecto VARCHAR(100),
    cliente VARCHAR(100),
    gestor VARCHAR(100),
    jefe_proyecto VARCHAR(100),
    fecha_inicio DATE,
    fecha_fin_prevista DATE,
    monto_contrato BIGINT,
    moneda VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla EDP (principal)
CREATE TABLE IF NOT EXISTS edp (
    id SERIAL PRIMARY KEY,
    n_edp INTEGER NOT NULL,
    proyecto VARCHAR(100),
    cliente VARCHAR(100),
    gestor VARCHAR(100),
    jefe_proyecto VARCHAR(100),
    mes VARCHAR(100),
    fecha_emision TIMESTAMP,
    fecha_envio_cliente TIMESTAMP,
    monto_propuesto BIGINT,
    monto_aprobado BIGINT,
    fecha_estimada_pago TIMESTAMP,
    conformidad_enviada BOOLEAN,
    n_conformidad VARCHAR(100),
    fecha_conformidad TIMESTAMP,
    estado VARCHAR(100),
    observaciones TEXT,
    registrado_por VARCHAR(100),
    estado_detallado VARCHAR(100),
    fecha_registro TIMESTAMP,
    motivo_no_aprobado VARCHAR(100),
    tipo_falla VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabla Cost Header
CREATE TABLE IF NOT EXISTS cost_header (
    id SERIAL PRIMARY KEY,
    cost_id INTEGER UNIQUE NOT NULL,
    project_id VARCHAR(100),
    proveedor VARCHAR(100),
    factura VARCHAR(100),
    fecha_factura DATE,
    fecha_recepcion DATE,
    fecha_vencimiento DATE,
    fecha_pago DATE,
    importe_bruto BIGINT,
    importe_neto BIGINT,
    moneda VARCHAR(100),
    estado_costo VARCHAR(100),
    tipo_costo VARCHAR(100),
    detalle_costo VARCHAR(100),
    detalle_especifico_costo VARCHAR(100),
    responsable_registro VARCHAR(100),
    url_respaldo VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tabla Cost Lines
CREATE TABLE IF NOT EXISTS cost_lines (
    id SERIAL PRIMARY KEY,
    line_id INTEGER,
    cost_id INTEGER,
    categoria VARCHAR(100),
    descripcion_item TEXT,
    unidad VARCHAR(50),
    cantidad DECIMAL(10,2),
    precio_unitario DECIMAL(15,2),
    subtotal DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Tabla Log (historial de cambios)
CREATE TABLE IF NOT EXISTS edp_log (
    id SERIAL PRIMARY KEY,
    fecha_hora TIMESTAMP,
    n_edp INTEGER,
    edp_id INTEGER,
    proyecto VARCHAR(100),
    campo VARCHAR(100),
    antes VARCHAR(500),
    despues VARCHAR(500),
    usuario VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Tabla Issues
CREATE TABLE IF NOT EXISTS issues (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    tipo VARCHAR(100),
    tipo_falla VARCHAR(100),
    severidad VARCHAR(100),
    estado VARCHAR(100),
    descripcion TEXT,
    proceso_afectado VARCHAR(100),
    edp_relacionado VARCHAR(100),
    proyecto_relacionado VARCHAR(100),
    impacto VARCHAR(500),
    usuario VARCHAR(100),
    usuario_asignado VARCHAR(100),
    fecha_ultima_actualizacion TIMESTAMP,
    fecha_resolucion TIMESTAMP,
    acciones_correctivas TEXT,
    acciones_preventivas TEXT,
    comentarios TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Añadir índices para mejorar performance
CREATE INDEX IF NOT EXISTS idx_edp_proyecto ON edp(proyecto);
CREATE INDEX IF NOT EXISTS idx_edp_cliente ON edp(cliente);
CREATE INDEX IF NOT EXISTS idx_edp_estado ON edp(estado);
CREATE INDEX IF NOT EXISTS idx_edp_fecha_emision ON edp(fecha_emision);
CREATE INDEX IF NOT EXISTS idx_projects_project_id ON projects(project_id);
CREATE INDEX IF NOT EXISTS idx_cost_header_project_id ON cost_header(project_id);
CREATE INDEX IF NOT EXISTS idx_cost_header_cost_id ON cost_header(cost_id);
CREATE INDEX IF NOT EXISTS idx_issues_estado ON issues(estado);
CREATE INDEX IF NOT EXISTS idx_edp_log_n_edp ON edp_log(n_edp);
CREATE INDEX IF NOT EXISTS idx_edp_log_edp_id ON edp_log(edp_id);

-- 8. Añadir relaciones después (opcional - para integridad referencial)
-- Ejecutar solo si necesitas integridad referencial estricta:
-- ALTER TABLE cost_header ADD CONSTRAINT fk_cost_header_project FOREIGN KEY (project_id) REFERENCES projects(project_id);
-- ALTER TABLE cost_lines ADD CONSTRAINT fk_cost_lines_cost FOREIGN KEY (cost_id) REFERENCES cost_header(cost_id);
-- ALTER TABLE edp_log ADD CONSTRAINT fk_edp_log_edp_id FOREIGN KEY (edp_id) REFERENCES edp(id);
