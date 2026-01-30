-- Migración: Agregar campo 'pagado' a las tablas entrega_arido y reporte_laboral
-- Fecha: 2026-01-30
-- Descripción: Agrega un campo booleano 'pagado' para rastrear el estado de pago de áridos y horas

-- Agregar campo 'pagado' a entrega_arido
ALTER TABLE entrega_arido
ADD COLUMN IF NOT EXISTS pagado BOOLEAN NOT NULL DEFAULT FALSE;

-- Agregar campo 'pagado' a reporte_laboral
ALTER TABLE reporte_laboral
ADD COLUMN IF NOT EXISTS pagado BOOLEAN NOT NULL DEFAULT FALSE;

-- Comentarios para documentación
COMMENT ON COLUMN entrega_arido.pagado IS 'Indica si la entrega de árido ha sido pagada';
COMMENT ON COLUMN reporte_laboral.pagado IS 'Indica si las horas trabajadas han sido pagadas';
