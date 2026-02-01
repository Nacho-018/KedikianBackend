-- Migración: Crear tablas relacionales para items de reportes de cuenta corriente
-- Fecha: 2026-01-30
-- Descripción: Crea tablas que vinculan reportes con items específicos de áridos y horas

-- Tabla para items de áridos de un reporte
CREATE TABLE IF NOT EXISTS reporte_items_aridos (
    id SERIAL PRIMARY KEY,
    reporte_id INTEGER NOT NULL REFERENCES reportes_cuenta_corriente(id) ON DELETE CASCADE,
    entrega_arido_id INTEGER NOT NULL REFERENCES entrega_arido(id) ON DELETE CASCADE,
    UNIQUE(reporte_id, entrega_arido_id)
);

-- Tabla para items de horas de un reporte
CREATE TABLE IF NOT EXISTS reporte_items_horas (
    id SERIAL PRIMARY KEY,
    reporte_id INTEGER NOT NULL REFERENCES reportes_cuenta_corriente(id) ON DELETE CASCADE,
    reporte_laboral_id INTEGER NOT NULL REFERENCES reporte_laboral(id) ON DELETE CASCADE,
    UNIQUE(reporte_id, reporte_laboral_id)
);

-- Índices para mejorar performance
CREATE INDEX IF NOT EXISTS idx_reporte_items_aridos_reporte_id ON reporte_items_aridos(reporte_id);
CREATE INDEX IF NOT EXISTS idx_reporte_items_aridos_entrega_id ON reporte_items_aridos(entrega_arido_id);
CREATE INDEX IF NOT EXISTS idx_reporte_items_horas_reporte_id ON reporte_items_horas(reporte_id);
CREATE INDEX IF NOT EXISTS idx_reporte_items_horas_laboral_id ON reporte_items_horas(reporte_laboral_id);

-- Comentarios para documentación
COMMENT ON TABLE reporte_items_aridos IS 'Vincula reportes de cuenta corriente con entregas de áridos específicas';
COMMENT ON TABLE reporte_items_horas IS 'Vincula reportes de cuenta corriente con reportes laborales específicos';
COMMENT ON COLUMN reporte_items_aridos.reporte_id IS 'ID del reporte de cuenta corriente';
COMMENT ON COLUMN reporte_items_aridos.entrega_arido_id IS 'ID de la entrega de árido incluida en el reporte';
COMMENT ON COLUMN reporte_items_horas.reporte_id IS 'ID del reporte de cuenta corriente';
COMMENT ON COLUMN reporte_items_horas.reporte_laboral_id IS 'ID del reporte laboral incluido en el reporte';
