-- Migración: Crear tabla pagos_reportes
-- Descripción: Tabla para registrar pagos de reportes de cuenta corriente
-- Fecha: 2026-02-26

CREATE TABLE IF NOT EXISTS pagos_reportes (
    id SERIAL PRIMARY KEY,
    reporte_id INTEGER NOT NULL REFERENCES reportes_cuenta_corriente(id) ON DELETE CASCADE,
    monto DECIMAL(12, 2) NOT NULL,
    fecha DATE NOT NULL,
    observaciones TEXT,
    fecha_registro TIMESTAMP DEFAULT NOW(),
    CONSTRAINT pagos_reportes_monto_positive CHECK (monto > 0)
);

-- Índices para mejorar rendimiento de consultas
CREATE INDEX IF NOT EXISTS idx_pagos_reportes_reporte_id ON pagos_reportes(reporte_id);
CREATE INDEX IF NOT EXISTS idx_pagos_reportes_fecha ON pagos_reportes(fecha);
CREATE INDEX IF NOT EXISTS idx_pagos_reportes_fecha_registro ON pagos_reportes(fecha_registro DESC);

-- Comentarios
COMMENT ON TABLE pagos_reportes IS 'Registro de pagos asociados a reportes de cuenta corriente';
COMMENT ON COLUMN pagos_reportes.id IS 'ID único del pago';
COMMENT ON COLUMN pagos_reportes.reporte_id IS 'ID del reporte de cuenta corriente asociado';
COMMENT ON COLUMN pagos_reportes.monto IS 'Monto del pago';
COMMENT ON COLUMN pagos_reportes.fecha IS 'Fecha en que se realizó el pago';
COMMENT ON COLUMN pagos_reportes.observaciones IS 'Notas u observaciones sobre el pago';
COMMENT ON COLUMN pagos_reportes.fecha_registro IS 'Fecha y hora de registro del pago en el sistema';
