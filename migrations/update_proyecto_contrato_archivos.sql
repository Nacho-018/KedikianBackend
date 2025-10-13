-- Migración para actualizar modelo Proyecto y agregar ContratoArchivo
-- Fecha: 2024-12-19

-- 1. Actualizar tabla proyecto para hacer campos opcionales y agregar nuevos campos
ALTER TABLE proyecto 
ADD COLUMN contrato_file_path VARCHAR(500) NULL;

-- 2. Crear tabla contrato_archivos
CREATE TABLE contrato_archivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proyecto_id INTEGER NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    ruta_archivo VARCHAR(500) NOT NULL,
    tipo_archivo VARCHAR(50) NOT NULL,
    tamaño_archivo BIGINT NOT NULL,
    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proyecto_id) REFERENCES proyecto(id)  -- Referencia correcta a tabla proyecto
);

-- 3. Crear índice para mejorar rendimiento
CREATE INDEX idx_contrato_archivos_proyecto_id ON contrato_archivos(proyecto_id);
CREATE INDEX idx_contrato_archivos_fecha_subida ON contrato_archivos(fecha_subida);
