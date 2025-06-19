-- Esquema de Supabase para migración de Google Sheets
-- Ejecutar en el SQL Editor de Supabase

-- 1. Tabla EDP (equivalente a hoja 'edp')
CREATE TABLE IF NOT EXISTS edp (
    id SERIAL PRIMARY KEY,
    n_edp INTEGER UNIQUE,
    proyecto TEXT,
    cliente TEXT,
    gestor TEXT,
    jefe_proyecto TEXT,
    fecha_inicio DATE,
    fecha_fin_prevista DATE,
    monto_contrato DECIMAL(15,2),
    moneda TEXT DEFAULT 'CLP',
    estado TEXT,
    observaciones TEXT,
    last_modified_by TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Tabla Projects (equivalente a hoja 'projects') 
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    proyecto TEXT NOT NULL,
    cliente TEXT,
    gestor TEXT,
    jefe_proyecto TEXT,
    fecha_inicio DATE,
    fecha_fin_prevista DATE,
    monto_contrato DECIMAL(15,2),
    moneda TEXT DEFAULT 'CLP',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Tabla Cost Header (equivalente a hoja 'cost_header')
CREATE TABLE IF NOT EXISTS cost_header (
    cost_id SERIAL PRIMARY KEY,
    project_id TEXT REFERENCES projects(id),
    proveedor TEXT,
    factura TEXT,
    fecha_factura DATE,
    fecha_recepcion DATE,
    fecha_vencimiento DATE,
    fecha_pago DATE,
    importe_bruto DECIMAL(15,2),
    importe_neto DECIMAL(15,2),
    moneda TEXT DEFAULT 'CLP',
    estado_costo TEXT,
    tipo_costo TEXT,
    detalle_costo TEXT,
    detalle_especifico_costo TEXT,
    responsable_registro TEXT,
    url_respaldo TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Tabla Cost Lines (equivalente a hoja 'cost_lines')
CREATE TABLE IF NOT EXISTS cost_lines (
    line_id SERIAL PRIMARY KEY,
    cost_id INTEGER REFERENCES cost_header(cost_id),
    categoria TEXT,
    descripcion_item TEXT,
    unidad TEXT,
    cantidad DECIMAL(10,2),
    precio_unitario DECIMAL(15,2),
    subtotal DECIMAL(15,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Tabla Logs (equivalente a hoja 'log')
CREATE TABLE IF NOT EXISTS logs (
    id TEXT PRIMARY KEY,
    edp_id TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    log_type TEXT,
    message TEXT,
    user_name TEXT,
    details JSONB
);

-- 6. Tabla Caja (si existe, equivalente a hoja 'caja')
CREATE TABLE IF NOT EXISTS caja (
    id SERIAL PRIMARY KEY,
    fecha DATE,
    concepto TEXT,
    ingreso DECIMAL(15,2),
    egreso DECIMAL(15,2),
    saldo DECIMAL(15,2),
    observaciones TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para mejorar performance
CREATE INDEX IF NOT EXISTS idx_edp_n_edp ON edp(n_edp);
CREATE INDEX IF NOT EXISTS idx_edp_cliente ON edp(cliente);
CREATE INDEX IF NOT EXISTS idx_edp_estado ON edp(estado);
CREATE INDEX IF NOT EXISTS idx_projects_cliente ON projects(cliente);
CREATE INDEX IF NOT EXISTS idx_cost_header_project_id ON cost_header(project_id);
CREATE INDEX IF NOT EXISTS idx_cost_lines_cost_id ON cost_lines(cost_id);
CREATE INDEX IF NOT EXISTS idx_logs_edp_id ON logs(edp_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);

-- Triggers para updated_at automático
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_edp_updated_at BEFORE UPDATE ON edp
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cost_header_updated_at BEFORE UPDATE ON cost_header
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Políticas de RLS (Row Level Security) - ajustar según necesidades
ALTER TABLE edp ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_header ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE caja ENABLE ROW LEVEL SECURITY;

-- Política básica: permitir todo para usuarios autenticados
CREATE POLICY "Enable all operations for authenticated users" ON edp
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all operations for authenticated users" ON projects
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all operations for authenticated users" ON cost_header
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all operations for authenticated users" ON cost_lines
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all operations for authenticated users" ON logs
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Enable all operations for authenticated users" ON caja
    FOR ALL USING (auth.role() = 'authenticated');

-- Comentarios para documentación
COMMENT ON TABLE edp IS 'Tabla principal de EDP (migrada desde Google Sheets)';
COMMENT ON TABLE projects IS 'Tabla de proyectos (migrada desde Google Sheets)';
COMMENT ON TABLE cost_header IS 'Encabezados de costos (migrada desde Google Sheets)';
COMMENT ON TABLE cost_lines IS 'Líneas de detalle de costos (migrada desde Google Sheets)';
COMMENT ON TABLE logs IS 'Registro de actividades y cambios (migrada desde Google Sheets)';
COMMENT ON TABLE caja IS 'Movimientos de caja (migrada desde Google Sheets)';