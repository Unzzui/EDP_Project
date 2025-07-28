-- Script para agregar la columna email a la tabla usuarios
-- Ejecutar en PostgreSQL

-- Agregar la columna email
ALTER TABLE usuarios ADD COLUMN email VARCHAR(255);

-- Crear un índice para búsquedas por email
CREATE INDEX idx_usuarios_email ON usuarios(email);

-- Comentario sobre la columna
COMMENT ON COLUMN usuarios.email IS 'Dirección de correo electrónico del usuario';

-- Verificar que la columna se agregó correctamente
SELECT 
    column_name,
    data_type,
    is_nullable,
    character_maximum_length
FROM 
    information_schema.columns
WHERE 
    table_name = 'usuarios'
    AND table_schema = 'public'
    AND column_name = 'email'; 