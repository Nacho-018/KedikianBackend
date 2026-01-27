-- Migración para crear tabla reportes_cuenta_corriente
-- Fecha: 2025-01-27
-- Sistema de Cuenta Corriente - Reportes de áridos y horas por proyecto

-- Crear tabla reportes_cuenta_corriente
CREATE TABLE IF NOT EXISTS reportes_cuenta_corriente (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER NOT NULL,
    periodo_inicio DATE NOT NULL,
    periodo_fin DATE NOT NULL,
    total_aridos DOUBLE PRECISION DEFAULT 0.0,
    total_horas DOUBLE PRECISION DEFAULT 0.0,
    importe_aridos NUMERIC(12, 2) DEFAULT 0.0,
    importe_horas NUMERIC(12, 2) DEFAULT 0.0,
    importe_total NUMERIC(12, 2) DEFAULT 0.0,
    estado VARCHAR(20) DEFAULT 'pendiente',
    fecha_generacion TIMESTAMP NOT NULL,
    observaciones TEXT NULL,
    numero_factura VARCHAR(50) NULL,
    fecha_pago DATE NULL,
    created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP WITH TIME ZONE DEFAULT NULL,

    -- Foreign key constraint
    CONSTRAINT fk_reportes_cuenta_corriente_proyecto
        FOREIGN KEY (proyecto_id)
        REFERENCES proyecto(id)
        ON DELETE CASCADE,

    -- Check constraints
    CONSTRAINT chk_estado_valido
        CHECK (estado IN ('pendiente', 'pagado')),

    CONSTRAINT chk_periodo_valido
        CHECK (periodo_fin >= periodo_inicio),

    CONSTRAINT chk_importes_positivos
        CHECK (importe_aridos >= 0 AND importe_horas >= 0 AND importe_total >= 0)
);

-- Crear índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_reportes_cc_proyecto_id
    ON reportes_cuenta_corriente(proyecto_id);

CREATE INDEX IF NOT EXISTS idx_reportes_cc_periodo
    ON reportes_cuenta_corriente(periodo_inicio, periodo_fin);

CREATE INDEX IF NOT EXISTS idx_reportes_cc_fecha_generacion
    ON reportes_cuenta_corriente(fecha_generacion DESC);

CREATE INDEX IF NOT EXISTS idx_reportes_cc_estado
    ON reportes_cuenta_corriente(estado);

-- Crear trigger para actualizar el campo 'updated' automáticamente
CREATE OR REPLACE FUNCTION update_reportes_cuenta_corriente_updated_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_update_reportes_cuenta_corriente_updated
    BEFORE UPDATE ON reportes_cuenta_corriente
    FOR EACH ROW
    EXECUTE FUNCTION update_reportes_cuenta_corriente_updated_column();

-- Comentarios descriptivos de la tabla
COMMENT ON TABLE reportes_cuenta_corriente IS 'Reportes de cuenta corriente que agrupan áridos y horas de máquinas por proyecto y período';
COMMENT ON COLUMN reportes_cuenta_corriente.proyecto_id IS 'ID del proyecto al que pertenece el reporte';
COMMENT ON COLUMN reportes_cuenta_corriente.periodo_inicio IS 'Fecha de inicio del período del reporte';
COMMENT ON COLUMN reportes_cuenta_corriente.periodo_fin IS 'Fecha de fin del período del reporte';
COMMENT ON COLUMN reportes_cuenta_corriente.total_aridos IS 'Total de m³ de áridos entregados en el período';
COMMENT ON COLUMN reportes_cuenta_corriente.total_horas IS 'Total de horas de máquinas en el período';
COMMENT ON COLUMN reportes_cuenta_corriente.importe_aridos IS 'Importe total de los áridos (cantidad * precio)';
COMMENT ON COLUMN reportes_cuenta_corriente.importe_horas IS 'Importe total de las horas (horas * tarifa)';
COMMENT ON COLUMN reportes_cuenta_corriente.importe_total IS 'Importe total del reporte (áridos + horas)';
COMMENT ON COLUMN reportes_cuenta_corriente.estado IS 'Estado del reporte: pendiente o pagado';
COMMENT ON COLUMN reportes_cuenta_corriente.fecha_generacion IS 'Fecha y hora en que se generó el reporte';
COMMENT ON COLUMN reportes_cuenta_corriente.observaciones IS 'Notas u observaciones adicionales del reporte';
COMMENT ON COLUMN reportes_cuenta_corriente.numero_factura IS 'Número de factura asociado al reporte';
COMMENT ON COLUMN reportes_cuenta_corriente.fecha_pago IS 'Fecha en que el reporte fue pagado';
