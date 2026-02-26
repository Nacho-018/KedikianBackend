-- ============================================
-- Migración: Creación de tablas para módulo de Cotizaciones
-- Fecha: 2026-02-03
-- Descripción: Crea las tablas cliente, cotizacion y cotizacion_item
-- ============================================

-- Tabla: cliente
-- Almacena información de clientes para cotizaciones
CREATE TABLE IF NOT EXISTS cliente (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    telefono VARCHAR(50),
    direccion VARCHAR(500),
    created TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated TIMESTAMP WITH TIME ZONE
);

-- Índices para tabla cliente
CREATE INDEX idx_cliente_nombre ON cliente(nombre);
CREATE INDEX idx_cliente_email ON cliente(email);

-- Tabla: cotizacion
-- Cabecera de las cotizaciones
CREATE TABLE IF NOT EXISTS cotizacion (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES cliente(id) ON DELETE CASCADE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_validez DATE,
    estado VARCHAR(20) DEFAULT 'borrador' CHECK (estado IN ('borrador', 'enviada', 'aprobada')),
    observaciones TEXT,
    importe_total NUMERIC(12, 2) DEFAULT 0.00,
    created TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated TIMESTAMP WITH TIME ZONE
);

-- Índices para tabla cotizacion
CREATE INDEX idx_cotizacion_cliente_id ON cotizacion(cliente_id);
CREATE INDEX idx_cotizacion_fecha_creacion ON cotizacion(fecha_creacion);
CREATE INDEX idx_cotizacion_estado ON cotizacion(estado);

-- Tabla: cotizacion_item
-- Líneas/items de cada cotización
CREATE TABLE IF NOT EXISTS cotizacion_item (
    id SERIAL PRIMARY KEY,
    cotizacion_id INTEGER NOT NULL REFERENCES cotizacion(id) ON DELETE CASCADE,
    nombre_servicio VARCHAR(255) NOT NULL,
    unidad VARCHAR(50) NOT NULL,
    cantidad NUMERIC(10, 2) NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(12, 2) NOT NULL CHECK (precio_unitario > 0),
    subtotal NUMERIC(12, 2) NOT NULL,
    created TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated TIMESTAMP WITH TIME ZONE
);

-- Índices para tabla cotizacion_item
CREATE INDEX idx_cotizacion_item_cotizacion_id ON cotizacion_item(cotizacion_id);
CREATE INDEX idx_cotizacion_item_nombre_servicio ON cotizacion_item(nombre_servicio);

-- Comentarios en tablas
COMMENT ON TABLE cliente IS 'Clientes del sistema para cotizaciones';
COMMENT ON TABLE cotizacion IS 'Cotizaciones generadas para clientes';
COMMENT ON TABLE cotizacion_item IS 'Items/líneas de cada cotización';

-- Comentarios en columnas importantes
COMMENT ON COLUMN cotizacion.estado IS 'Estado de la cotización: borrador, enviada, aprobada';
COMMENT ON COLUMN cotizacion.importe_total IS 'Suma de todos los subtotales de los items';
COMMENT ON COLUMN cotizacion_item.subtotal IS 'Calculado como cantidad × precio_unitario';

-- ============================================
-- FIN DE MIGRACIÓN
-- ============================================
