-- Migración para agregar campos de precio y tarifa
-- Fecha: 2026-01-28
-- Descripción: Agrega precio_unitario a entrega_arido y tarifa_hora a reporte_laboral

-- 1. Agregar campo precio_unitario a tabla entrega_arido
ALTER TABLE entrega_arido
ADD COLUMN IF NOT EXISTS precio_unitario DOUBLE PRECISION NULL;

-- 2. Agregar campo tarifa_hora a tabla reporte_laboral
ALTER TABLE reporte_laboral
ADD COLUMN IF NOT EXISTS tarifa_hora DOUBLE PRECISION NULL;

-- 3. Crear índices para mejorar rendimiento de las consultas de actualización
CREATE INDEX IF NOT EXISTS idx_entrega_arido_tipo_fecha
    ON entrega_arido(tipo_arido, fecha_entrega);

CREATE INDEX IF NOT EXISTS idx_reporte_laboral_maquina_fecha
    ON reporte_laboral(maquina_id, fecha_asignacion);

CREATE INDEX IF NOT EXISTS idx_entrega_arido_proyecto_tipo_fecha
    ON entrega_arido(proyecto_id, tipo_arido, fecha_entrega);

CREATE INDEX IF NOT EXISTS idx_reporte_laboral_proyecto_maquina_fecha
    ON reporte_laboral(proyecto_id, maquina_id, fecha_asignacion);

-- Comentarios descriptivos
COMMENT ON COLUMN entrega_arido.precio_unitario IS 'Precio unitario del árido en el momento de la entrega (por m³)';
COMMENT ON COLUMN reporte_laboral.tarifa_hora IS 'Tarifa por hora de la máquina en el momento del reporte';
