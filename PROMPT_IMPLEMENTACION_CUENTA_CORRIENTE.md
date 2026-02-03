# PROMPT COMPLETO: IMPLEMENTACIÓN DEL MÓDULO CUENTA CORRIENTE

Este prompt contiene TODAS las instrucciones detalladas para implementar el sistema completo de Cuenta Corriente en un backend FastAPI + PostgreSQL + SQLAlchemy.

---

## ÍNDICE

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Prerrequisitos del Sistema](#prerrequisitos-del-sistema)
3. [Paso 1: Migraciones de Base de Datos](#paso-1-migraciones-de-base-de-datos)
4. [Paso 2: Modelos SQLAlchemy](#paso-2-modelos-sqlalchemy)
5. [Paso 3: Esquemas Pydantic](#paso-3-esquemas-pydantic)
6. [Paso 4: Servicio de Lógica de Negocio](#paso-4-servicio-de-lógica-de-negocio)
7. [Paso 5: Router de API](#paso-5-router-de-api)
8. [Paso 6: Registro del Router](#paso-6-registro-del-router)
9. [Paso 7: Configuración de Precios y Tarifas](#paso-7-configuración-de-precios-y-tarifas)
10. [Paso 8: Testing y Validación](#paso-8-testing-y-validación)

---

## RESUMEN EJECUTIVO

El módulo de **Cuenta Corriente** es un sistema integral para:

- **Agrupar y Totalizar**: Entregas de áridos (m³) y horas de máquinas por período
- **Calcular Importes**: Usando precios/tarifas desde BD con fallback a valores predeterminados
- **Gestionar Pagos**: Control granular de pagos individuales y estado general del reporte
- **Exportar Reportes**: Generación de Excel y PDF profesionales
- **Actualizar Precios**: Modificación retroactiva de precios/tarifas por período

**Componentes principales**:
- 4 tablas de base de datos (1 principal + 2 relacionales + datos en tablas existentes)
- 22 endpoints REST
- 20+ esquemas Pydantic
- Exportación a Excel y PDF con logo
- Sistema de pago granular (por item individual)

---

## PRERREQUISITOS DEL SISTEMA

Tu sistema DEBE tener las siguientes tablas y modelos ya implementados:

### Tablas Requeridas

```sql
-- 1. Tabla proyecto
CREATE TABLE proyecto (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(75) NOT NULL,
    descripcion VARCHAR(500),
    estado BOOLEAN DEFAULT TRUE,
    -- ... otros campos
);

-- 2. Tabla entrega_arido
CREATE TABLE entrega_arido (
    id SERIAL PRIMARY KEY,
    proyecto_id INTEGER REFERENCES proyecto(id),
    usuario_id INTEGER REFERENCES usuario(id),
    tipo_arido VARCHAR NOT NULL,
    nombre VARCHAR,
    cantidad DOUBLE PRECISION NOT NULL,  -- en m³
    fecha_entrega TIMESTAMP NOT NULL,
    observaciones VARCHAR,
    created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP WITH TIME ZONE
);

-- 3. Tabla reporte_laboral (horas de máquinas)
CREATE TABLE reporte_laboral (
    id SERIAL PRIMARY KEY,
    maquina_id INTEGER REFERENCES maquina(id),
    usuario_id INTEGER REFERENCES usuario(id),
    proyecto_id INTEGER REFERENCES proyecto(id),
    fecha_asignacion TIMESTAMP NOT NULL,
    horas_turno INTEGER NOT NULL,
    horometro_inicial DOUBLE PRECISION,
    created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP WITH TIME ZONE
);

-- 4. Tabla maquina
CREATE TABLE maquina (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    horas_uso INTEGER DEFAULT 0,
    -- ... otros campos
);

-- 5. Tabla usuario
CREATE TABLE usuario (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR NOT NULL,
    -- ... otros campos
);
```

### Modelos SQLAlchemy Requeridos

Debes tener modelos SQLAlchemy para:
- `Proyecto`
- `EntregaArido`
- `ReporteLaboral`
- `Maquina`
- `Usuario`

### Dependencias Python

Asegúrate de tener instaladas:
```bash
pip install fastapi sqlalchemy psycopg2-binary pandas openpyxl reportlab
```

---

## PASO 1: MIGRACIONES DE BASE DE DATOS

Ejecuta las siguientes migraciones SQL en tu base de datos PostgreSQL **en este orden exacto**:

### 1.1. Agregar campos de precio y tarifa a tablas existentes

**Archivo**: `migrations/add_precio_tarifa_fields.sql`

```sql
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
```

### 1.2. Agregar campo de estado de pago

**Archivo**: `migrations/add_pagado_field.sql`

```sql
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
```

### 1.3. Crear tabla principal de reportes

**Archivo**: `migrations/create_reportes_cuenta_corriente.sql`

```sql
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
        CHECK (estado IN ('pendiente', 'pagado', 'parcial')),

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
COMMENT ON COLUMN reportes_cuenta_corriente.estado IS 'Estado del reporte: pendiente, parcial o pagado';
COMMENT ON COLUMN reportes_cuenta_corriente.fecha_generacion IS 'Fecha y hora en que se generó el reporte';
COMMENT ON COLUMN reportes_cuenta_corriente.observaciones IS 'Notas u observaciones adicionales del reporte';
COMMENT ON COLUMN reportes_cuenta_corriente.numero_factura IS 'Número de factura asociado al reporte';
COMMENT ON COLUMN reportes_cuenta_corriente.fecha_pago IS 'Fecha en que el reporte fue pagado';
```

### 1.4. Crear tablas relacionales

**Archivo**: `migrations/add_reporte_items_tables.sql`

```sql
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
```

### 1.5. Actualizar modelos existentes

**IMPORTANTE**: Debes actualizar tus modelos SQLAlchemy existentes para agregar los nuevos campos:

**En tu modelo `EntregaArido`**, agrega:
```python
precio_unitario = Column(Float, nullable=True)
pagado = Column(Boolean, default=False)
```

**En tu modelo `ReporteLaboral`**, agrega:
```python
tarifa_hora = Column(Float, nullable=True)
pagado = Column(Boolean, default=False)
```

**En tu modelo `Proyecto`**, agrega la relación:
```python
reportes_cuenta_corriente = relationship("ReporteCuentaCorriente", back_populates="proyecto", cascade="all, delete-orphan")
```

---

## PASO 2: MODELOS SQLALCHEMY

Crea los siguientes archivos de modelos:

### 2.1. Modelo Principal

**Archivo**: `app/db/models/reporte_cuenta_corriente.py`

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, Numeric, Text
from sqlalchemy.orm import relationship
from app.db.database import Base
from sqlalchemy.sql import func

class ReporteCuentaCorriente(Base):
    __tablename__ = "reportes_cuenta_corriente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(Integer, ForeignKey("proyecto.id"), nullable=False)
    periodo_inicio = Column(Date, nullable=False)
    periodo_fin = Column(Date, nullable=False)
    total_aridos = Column(Float, default=0.0)  # Total m³ de áridos entregados
    total_horas = Column(Float, default=0.0)  # Total horas de máquinas
    importe_aridos = Column(Numeric(12, 2), default=0.0)  # Importe total de áridos
    importe_horas = Column(Numeric(12, 2), default=0.0)  # Importe total de horas de máquinas
    importe_total = Column(Numeric(12, 2), default=0.0)  # Importe total del reporte
    estado = Column(String(20), default="pendiente")  # "pendiente", "parcial" o "pagado"
    fecha_generacion = Column(DateTime, nullable=False)

    # Campos adicionales opcionales
    observaciones = Column(Text, nullable=True)  # Notas u observaciones del reporte
    numero_factura = Column(String(50), nullable=True)  # Número de factura asociado
    fecha_pago = Column(Date, nullable=True)  # Fecha en que fue pagado

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="reportes_cuenta_corriente")
    items_aridos_rel = relationship("ReporteItemArido", back_populates="reporte", cascade="all, delete-orphan")
    items_horas_rel = relationship("ReporteItemHora", back_populates="reporte", cascade="all, delete-orphan")

    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())
```

### 2.2. Modelos Relacionales

**Archivo**: `app/db/models/reporte_items.py`

```python
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class ReporteItemArido(Base):
    """
    Tabla relacional que vincula un reporte de cuenta corriente con una entrega de árido específica.
    Permite rastrear exactamente qué entregas de áridos pertenecen a cada reporte.
    """
    __tablename__ = "reporte_items_aridos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reporte_id = Column(Integer, ForeignKey("reportes_cuenta_corriente.id", ondelete="CASCADE"), nullable=False)
    entrega_arido_id = Column(Integer, ForeignKey("entrega_arido.id", ondelete="CASCADE"), nullable=False)

    # Relaciones
    reporte = relationship("ReporteCuentaCorriente", back_populates="items_aridos_rel")
    entrega_arido = relationship("EntregaArido")


class ReporteItemHora(Base):
    """
    Tabla relacional que vincula un reporte de cuenta corriente con un reporte laboral específico.
    Permite rastrear exactamente qué reportes de horas pertenecen a cada reporte.
    """
    __tablename__ = "reporte_items_horas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reporte_id = Column(Integer, ForeignKey("reportes_cuenta_corriente.id", ondelete="CASCADE"), nullable=False)
    reporte_laboral_id = Column(Integer, ForeignKey("reporte_laboral.id", ondelete="CASCADE"), nullable=False)

    # Relaciones
    reporte = relationship("ReporteCuentaCorriente", back_populates="items_horas_rel")
    reporte_laboral = relationship("ReporteLaboral")
```

### 2.3. Actualizar `__init__.py` de modelos

En `app/db/models/__init__.py`, agrega las importaciones:

```python
from .reporte_cuenta_corriente import ReporteCuentaCorriente
from .reporte_items import ReporteItemArido, ReporteItemHora
```

---

## PASO 3: ESQUEMAS PYDANTIC

En tu archivo de esquemas (por ejemplo `app/schemas/schemas.py`), agrega los siguientes esquemas al final:

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

# ============= ESQUEMAS DE CUENTA CORRIENTE =============

# Esquemas base para reportes
class ReporteCuentaCorrienteBase(BaseModel):
    proyecto_id: int
    periodo_inicio: date
    periodo_fin: date
    total_aridos: Optional[float] = 0.0
    total_horas: Optional[float] = 0.0
    importe_aridos: Optional[float] = 0.0
    importe_horas: Optional[float] = 0.0
    importe_total: Optional[float] = 0.0
    estado: Optional[str] = "pendiente"  # "pendiente", "parcial" o "pagado"
    fecha_generacion: datetime
    observaciones: Optional[str] = None
    numero_factura: Optional[str] = None
    fecha_pago: Optional[date] = None

class ReporteCuentaCorrienteCreate(BaseModel):
    proyecto_id: int
    periodo_inicio: date
    periodo_fin: date
    observaciones: Optional[str] = None
    aridos_seleccionados: Optional[List[str]] = None  # Tipos de áridos a incluir
    maquinas_seleccionadas: Optional[List[int]] = None  # IDs de máquinas a incluir

class ReporteCuentaCorrienteUpdate(BaseModel):
    estado: Optional[str] = None
    observaciones: Optional[str] = None
    numero_factura: Optional[str] = None
    fecha_pago: Optional[date] = None

class ReporteCuentaCorrienteOut(ReporteCuentaCorrienteBase):
    id: int
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        from_attributes = True

# Esquemas para el resumen de proyecto con precios
class DetalleAridoConPrecio(BaseModel):
    tipo_arido: str
    cantidad: float  # m³
    precio_unitario: float  # precio por m³
    importe: float  # cantidad * precio_unitario

class DetalleHorasConTarifa(BaseModel):
    maquina_id: int
    maquina_nombre: str
    total_horas: float
    tarifa_hora: float  # tarifa por hora
    importe: float  # total_horas * tarifa_hora

class ResumenProyectoSchema(BaseModel):
    proyecto_id: int
    proyecto_nombre: str
    periodo_inicio: date
    periodo_fin: date

    # Detalle de áridos
    aridos: List[DetalleAridoConPrecio]
    total_aridos_m3: float
    total_importe_aridos: float

    # Detalle de horas de máquinas
    horas_maquinas: List[DetalleHorasConTarifa]
    total_horas: float
    total_importe_horas: float

    # Total general
    importe_total: float

# Schema para precios de áridos
class PrecioAridoSchema(BaseModel):
    tipo_arido: str
    precio_m3: float

# Schema para tarifas de máquinas
class TarifaMaquinaSchema(BaseModel):
    maquina_id: int
    maquina_nombre: str
    tarifa_hora: float

# Schema para actualizar precio de áridos por período
class ActualizarPrecioAridoRequest(BaseModel):
    tipo_arido: str = Field(..., description="Tipo de árido a actualizar")
    nuevo_precio: float = Field(..., gt=0, description="Nuevo precio unitario")
    periodo_inicio: date = Field(..., description="Fecha de inicio del período")
    periodo_fin: date = Field(..., description="Fecha de fin del período")

class ActualizarPrecioAridoResponse(BaseModel):
    registros_actualizados: int
    precio_anterior: float
    precio_nuevo: float
    importe_anterior: float
    importe_nuevo: float
    diferencia: float

# Schema para actualizar tarifa de máquinas por período
class ActualizarTarifaMaquinaRequest(BaseModel):
    maquina_id: int = Field(..., description="ID de la máquina")
    nueva_tarifa: float = Field(..., gt=0, description="Nueva tarifa por hora")
    periodo_inicio: date = Field(..., description="Fecha de inicio del período")
    periodo_fin: date = Field(..., description="Fecha de fin del período")

class ActualizarTarifaMaquinaResponse(BaseModel):
    registros_actualizados: int
    tarifa_anterior: float
    tarifa_nueva: float
    importe_anterior: float
    importe_nuevo: float
    diferencia: float

# Schema para items individuales de áridos
class ItemAridoDetalle(BaseModel):
    id: int
    tipo_arido: str
    cantidad: float
    precio_unitario: float
    importe: float
    pagado: bool
    fecha: date

    class Config:
        from_attributes = True

# Schema para items individuales de horas
class ItemHoraDetalle(BaseModel):
    id: int
    maquina_id: int
    maquina_nombre: str
    total_horas: float
    tarifa_hora: float
    importe: float
    pagado: bool
    fecha: date
    usuario_nombre: Optional[str] = None

    class Config:
        from_attributes = True

# Schema para la respuesta del detalle del reporte
class DetalleReporteResponse(BaseModel):
    items_aridos: List[ItemAridoDetalle]
    items_horas: List[ItemHoraDetalle]

# Schema para actualizar estado de pago de items
class ItemPagoUpdate(BaseModel):
    item_id: int
    pagado: bool

class ActualizarItemsPagoRequest(BaseModel):
    items_aridos: List[ItemPagoUpdate] = []
    items_horas: List[ItemPagoUpdate] = []

class ActualizarItemsPagoResponse(BaseModel):
    aridos_actualizados: int
    horas_actualizadas: int
    reporte: ReporteCuentaCorrienteOut

# Schema para response con items incluidos
class ReporteCuentaCorrienteConDetalleOut(ReporteCuentaCorrienteOut):
    """Response que incluye los items individuales del reporte"""
    items_aridos: List[ItemAridoDetalle] = []
    items_horas: List[ItemHoraDetalle] = []
```

---

## PASO 4: SERVICIO DE LÓGICA DE NEGOCIO

Crea el archivo de servicio:

**Archivo**: `app/services/cuenta_corriente_service.py`

```python
from app.db.models import ReporteCuentaCorriente, Proyecto, EntregaArido, ReporteLaboral, Maquina, ReporteItemArido, ReporteItemHora
from app.schemas.schemas import (
    ReporteCuentaCorrienteCreate,
    ReporteCuentaCorrienteUpdate,
    ReporteCuentaCorrienteOut,
    ResumenProyectoSchema,
    DetalleAridoConPrecio,
    DetalleHorasConTarifa,
    PrecioAridoSchema,
    TarifaMaquinaSchema,
    DetalleReporteResponse,
    ItemAridoDetalle,
    ItemHoraDetalle,
    ActualizarItemsPagoRequest,
    ActualizarItemsPagoResponse,
    ReporteCuentaCorrienteConDetalleOut
)
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal

# ============= PRECIOS DE ÁRIDOS POR M³ =============
# Estos son valores por defecto que se usan como fallback
# Si el registro tiene precio_unitario en la BD, se usa ese valor
PRECIOS_ARIDOS: Dict[str, float] = {
    "Arena Fina": 54000.0,
    "Granza": 54000.0,
    "Arena Común": 33680.0,
    "Relleno": 16000.0,
    "Tierra Negra": 16000.0,
    "Piedra": 12000.0,
    "0.20": 8000.0,
    "Blinder": 10000.0,
    "Arena Lavada": 33680.0
}


# ============= TARIFAS DE MÁQUINAS POR HORA =============
# IMPORTANTE: Usa los nombres EXACTOS de las máquinas como aparecen en la BD
# Para obtener los nombres: SELECT id, nombre FROM maquina;
#
# Formato: "Nombre_Exacto_Maquina": tarifa_por_hora
#
# INSTRUCCIONES:
# 1. Consulta tus máquinas en la BD
# 2. Reemplaza estos ejemplos con tus máquinas reales
# 3. Usa el nombre EXACTO (case-sensitive)
# 4. La tarifa "default" se usa si la máquina no está en la lista

TARIFAS_MAQUINAS: Dict[str, float] = {
    # ===== TARIFA POR DEFECTO =====
    "default": 15000.0,  # Se usa si la máquina no está en la lista
    "BOBCAT 2018 S650.": 700000,
    "BOBCAT S530 2017": 700000,
    "EXCAVADORA 2020 SANY EU50.": 100000,
    "EXCAVADORA 2023 XCMG E60.": 100000,
    "EXCAVADORA 2022 LONKING 6150.": 150000,
    "EXCAVADORA 2015 LONKING 6150.": 150000,
    "PALA 2022 SINOMACH 933.": 100000
}

def get_precio_arido(tipo_arido: str) -> float:
    """Obtiene el precio por m³ de un tipo de árido"""
    return PRECIOS_ARIDOS.get(tipo_arido, 0.0)

def get_tarifa_maquina(maquina_nombre: str) -> float:
    """Obtiene la tarifa por hora de una máquina"""
    # Primero intenta buscar por nombre específico, si no usa la tarifa default
    return TARIFAS_MAQUINAS.get(maquina_nombre, TARIFAS_MAQUINAS["default"])

def get_resumen_proyecto(
    db: Session,
    proyecto_id: int,
    periodo_inicio: date,
    periodo_fin: date,
    tipos_aridos: Optional[List[str]] = None,
    maquinas_ids: Optional[List[int]] = None
) -> Optional[ResumenProyectoSchema]:
    """
    Obtiene el resumen de áridos y horas de un proyecto con sus precios calculados
    para un período determinado.

    IMPORTANTE: Lee los precios y tarifas desde la base de datos (precio_unitario y tarifa_hora)
    en lugar de usar valores predeterminados.

    Args:
        db: Sesión de base de datos
        proyecto_id: ID del proyecto
        periodo_inicio: Fecha de inicio del período
        periodo_fin: Fecha de fin del período
        tipos_aridos: Lista opcional de tipos de áridos a incluir (filtro)
        maquinas_ids: Lista opcional de IDs de máquinas a incluir (filtro)
    """
    # Verificar que el proyecto existe
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        return None

    # Obtener entregas de áridos en el período con precio_unitario desde la BD
    query_aridos = db.query(
        EntregaArido.tipo_arido,
        func.sum(EntregaArido.cantidad).label('total_cantidad'),
        func.avg(EntregaArido.precio_unitario).label('precio_promedio')
    ).filter(
        EntregaArido.proyecto_id == proyecto_id,
        EntregaArido.fecha_entrega >= periodo_inicio,
        EntregaArido.fecha_entrega <= periodo_fin
    )

    # Aplicar filtro de tipos de áridos si se especifica
    if tipos_aridos and len(tipos_aridos) > 0:
        query_aridos = query_aridos.filter(EntregaArido.tipo_arido.in_(tipos_aridos))

    entregas_aridos = query_aridos.group_by(EntregaArido.tipo_arido).all()

    # Calcular detalles de áridos con precios REALES de la BD
    detalles_aridos = []
    total_aridos_m3 = 0.0
    total_importe_aridos = 0.0

    for tipo_arido, cantidad, precio_promedio in entregas_aridos:
        # Usar el precio de la BD, si es None usar el diccionario como fallback
        precio_unitario = precio_promedio if precio_promedio is not None else get_precio_arido(tipo_arido)
        importe = cantidad * precio_unitario

        detalles_aridos.append(DetalleAridoConPrecio(
            tipo_arido=tipo_arido,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            importe=importe
        ))

        total_aridos_m3 += cantidad
        total_importe_aridos += importe

    # Obtener horas de máquinas en el período con tarifa_hora desde la BD
    query_horas = db.query(
        Maquina.id,
        Maquina.nombre,
        func.sum(ReporteLaboral.horas_turno).label('total_horas'),
        func.avg(ReporteLaboral.tarifa_hora).label('tarifa_promedio')
    ).join(
        ReporteLaboral, ReporteLaboral.maquina_id == Maquina.id
    ).filter(
        ReporteLaboral.proyecto_id == proyecto_id,
        ReporteLaboral.fecha_asignacion >= periodo_inicio,
        ReporteLaboral.fecha_asignacion <= periodo_fin
    )

    # Aplicar filtro de máquinas si se especifica
    if maquinas_ids and len(maquinas_ids) > 0:
        query_horas = query_horas.filter(Maquina.id.in_(maquinas_ids))

    horas_maquinas = query_horas.group_by(Maquina.id, Maquina.nombre).all()

    # Calcular detalles de horas con tarifas REALES de la BD
    detalles_horas = []
    total_horas = 0.0
    total_importe_horas = 0.0

    for maquina_id, maquina_nombre, horas, tarifa_promedio in horas_maquinas:
        # Usar la tarifa de la BD, si es None usar el diccionario como fallback
        tarifa_hora = tarifa_promedio if tarifa_promedio is not None else get_tarifa_maquina(maquina_nombre)
        importe = horas * tarifa_hora

        detalles_horas.append(DetalleHorasConTarifa(
            maquina_id=maquina_id,
            maquina_nombre=maquina_nombre,
            total_horas=horas,
            tarifa_hora=tarifa_hora,
            importe=importe
        ))

        total_horas += horas
        total_importe_horas += importe

    # Calcular importe total
    importe_total = total_importe_aridos + total_importe_horas

    return ResumenProyectoSchema(
        proyecto_id=proyecto_id,
        proyecto_nombre=proyecto.nombre,
        periodo_inicio=periodo_inicio,
        periodo_fin=periodo_fin,
        aridos=detalles_aridos,
        total_aridos_m3=total_aridos_m3,
        total_importe_aridos=total_importe_aridos,
        horas_maquinas=detalles_horas,
        total_horas=total_horas,
        total_importe_horas=total_importe_horas,
        importe_total=importe_total
    )

def get_reportes(db: Session, proyecto_id: Optional[int] = None) -> List[ReporteCuentaCorrienteOut]:
    """Obtiene todos los reportes de cuenta corriente, opcionalmente filtrados por proyecto"""
    query = db.query(ReporteCuentaCorriente)

    if proyecto_id:
        query = query.filter(ReporteCuentaCorriente.proyecto_id == proyecto_id)

    reportes = query.order_by(ReporteCuentaCorriente.fecha_generacion.desc()).all()

    return [ReporteCuentaCorrienteOut.model_validate(r) for r in reportes]

def get_reporte(db: Session, reporte_id: int) -> Optional[ReporteCuentaCorrienteOut]:
    """Obtiene un reporte específico por ID"""
    reporte = db.query(ReporteCuentaCorriente).filter(
        ReporteCuentaCorriente.id == reporte_id
    ).first()

    if reporte:
        return ReporteCuentaCorrienteOut.model_validate(reporte)
    return None

def create_reporte(db: Session, reporte_data: ReporteCuentaCorrienteCreate):
    """
    Crea un nuevo reporte de cuenta corriente calculando automáticamente
    los totales e importes del período especificado.

    Soporta selección de items específicos mediante:
    - aridos_seleccionados: Lista de tipos de áridos a incluir
    - maquinas_seleccionadas: Lista de IDs de máquinas a incluir

    Si no se especifican, se incluyen todos los items del período.
    """
    # Validar que el proyecto existe
    proyecto = db.query(Proyecto).filter(Proyecto.id == reporte_data.proyecto_id).first()
    if not proyecto:
        raise ValueError(f"No se encontró el proyecto con ID {reporte_data.proyecto_id}")

    # Validar tipos de áridos si se especificaron
    if reporte_data.aridos_seleccionados is not None and len(reporte_data.aridos_seleccionados) > 0:
        tipos_existentes = db.query(EntregaArido.tipo_arido).filter(
            EntregaArido.proyecto_id == reporte_data.proyecto_id,
            EntregaArido.fecha_entrega >= reporte_data.periodo_inicio,
            EntregaArido.fecha_entrega <= reporte_data.periodo_fin
        ).distinct().all()
        tipos_existentes = [t[0] for t in tipos_existentes]

        tipos_invalidos = [t for t in reporte_data.aridos_seleccionados if t not in tipos_existentes]
        if tipos_invalidos:
            raise ValueError(f"Tipos de áridos no encontrados en el período: {', '.join(tipos_invalidos)}")

    # Validar máquinas si se especificaron
    if reporte_data.maquinas_seleccionadas is not None and len(reporte_data.maquinas_seleccionadas) > 0:
        maquinas_existentes = db.query(ReporteLaboral.maquina_id).filter(
            ReporteLaboral.proyecto_id == reporte_data.proyecto_id,
            ReporteLaboral.fecha_asignacion >= reporte_data.periodo_inicio,
            ReporteLaboral.fecha_asignacion <= reporte_data.periodo_fin
        ).distinct().all()
        maquinas_existentes = [m[0] for m in maquinas_existentes]

        maquinas_invalidas = [m for m in reporte_data.maquinas_seleccionadas if m not in maquinas_existentes]
        if maquinas_invalidas:
            raise ValueError(f"Máquinas no encontradas en el período: {', '.join(map(str, maquinas_invalidas))}")

    # Obtener resumen del proyecto para el período con filtros opcionales
    resumen = get_resumen_proyecto(
        db,
        reporte_data.proyecto_id,
        reporte_data.periodo_inicio,
        reporte_data.periodo_fin,
        tipos_aridos=reporte_data.aridos_seleccionados,
        maquinas_ids=reporte_data.maquinas_seleccionadas
    )

    if not resumen:
        raise ValueError(f"No se encontró el proyecto con ID {reporte_data.proyecto_id}")

    # Validar que haya al menos un item para generar el reporte
    if resumen.total_aridos_m3 == 0 and resumen.total_horas == 0:
        raise ValueError("No se puede generar un reporte sin items. Debe seleccionar al menos un árido o máquina.")

    # Crear el reporte con los datos calculados
    nuevo_reporte = ReporteCuentaCorriente(
        proyecto_id=reporte_data.proyecto_id,
        periodo_inicio=reporte_data.periodo_inicio,
        periodo_fin=reporte_data.periodo_fin,
        total_aridos=resumen.total_aridos_m3,
        total_horas=resumen.total_horas,
        importe_aridos=Decimal(str(resumen.total_importe_aridos)),
        importe_horas=Decimal(str(resumen.total_importe_horas)),
        importe_total=Decimal(str(resumen.importe_total)),
        estado="pendiente",
        fecha_generacion=datetime.now(),
        observaciones=reporte_data.observaciones
    )

    db.add(nuevo_reporte)
    db.commit()
    db.refresh(nuevo_reporte)

    # Obtener los registros de áridos que pertenecen a este reporte
    query_aridos = db.query(EntregaArido).filter(
        EntregaArido.proyecto_id == reporte_data.proyecto_id,
        EntregaArido.fecha_entrega >= reporte_data.periodo_inicio,
        EntregaArido.fecha_entrega <= reporte_data.periodo_fin
    )
    if reporte_data.aridos_seleccionados and len(reporte_data.aridos_seleccionados) > 0:
        query_aridos = query_aridos.filter(EntregaArido.tipo_arido.in_(reporte_data.aridos_seleccionados))

    entregas_aridos = query_aridos.all()

    # Guardar relaciones de áridos
    for entrega in entregas_aridos:
        item_rel = ReporteItemArido(
            reporte_id=nuevo_reporte.id,
            entrega_arido_id=entrega.id
        )
        db.add(item_rel)

    # Obtener los reportes laborales que pertenecen a este reporte
    query_horas = db.query(ReporteLaboral).filter(
        ReporteLaboral.proyecto_id == reporte_data.proyecto_id,
        ReporteLaboral.fecha_asignacion >= reporte_data.periodo_inicio,
        ReporteLaboral.fecha_asignacion <= reporte_data.periodo_fin
    )
    if reporte_data.maquinas_seleccionadas and len(reporte_data.maquinas_seleccionadas) > 0:
        query_horas = query_horas.filter(ReporteLaboral.maquina_id.in_(reporte_data.maquinas_seleccionadas))

    reportes_horas = query_horas.all()

    # Guardar relaciones de horas
    for reporte_hora in reportes_horas:
        item_rel = ReporteItemHora(
            reporte_id=nuevo_reporte.id,
            reporte_laboral_id=reporte_hora.id
        )
        db.add(item_rel)

    # Commit de las relaciones
    db.commit()

    # Obtener items individuales filtrados para el response
    items_aridos = _get_items_aridos_filtrados(
        db,
        reporte_data.proyecto_id,
        reporte_data.periodo_inicio,
        reporte_data.periodo_fin,
        reporte_data.aridos_seleccionados
    )

    items_horas = _get_items_horas_filtrados(
        db,
        reporte_data.proyecto_id,
        reporte_data.periodo_inicio,
        reporte_data.periodo_fin,
        reporte_data.maquinas_seleccionadas
    )

    # Construir response con items incluidos
    return ReporteCuentaCorrienteConDetalleOut(
        **ReporteCuentaCorrienteOut.model_validate(nuevo_reporte).model_dump(),
        items_aridos=items_aridos,
        items_horas=items_horas
    )

def update_reporte_estado(
    db: Session,
    reporte_id: int,
    reporte_update: ReporteCuentaCorrienteUpdate
) -> Optional[ReporteCuentaCorrienteOut]:
    """Actualiza el estado y otros campos de un reporte"""
    reporte = db.query(ReporteCuentaCorriente).filter(
        ReporteCuentaCorriente.id == reporte_id
    ).first()

    if not reporte:
        return None

    # Actualizar solo los campos proporcionados
    update_data = reporte_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(reporte, field, value)

    # Si se marca como pagado y no tiene fecha de pago, asignarla
    if reporte_update.estado == "pagado" and not reporte.fecha_pago:
        reporte.fecha_pago = date.today()

    db.commit()
    db.refresh(reporte)

    return ReporteCuentaCorrienteOut.model_validate(reporte)

def delete_reporte(db: Session, reporte_id: int) -> bool:
    """Elimina un reporte de cuenta corriente"""
    reporte = db.query(ReporteCuentaCorriente).filter(
        ReporteCuentaCorriente.id == reporte_id
    ).first()

    if not reporte:
        return False

    db.delete(reporte)
    db.commit()
    return True

def get_todos_precios_aridos() -> List[PrecioAridoSchema]:
    """Obtiene todos los precios de áridos disponibles"""
    return [
        PrecioAridoSchema(tipo_arido=tipo, precio_m3=precio)
        for tipo, precio in PRECIOS_ARIDOS.items()
    ]

def get_tarifa_maquina_por_id(db: Session, maquina_id: int) -> Optional[TarifaMaquinaSchema]:
    """Obtiene la tarifa por hora de una máquina específica"""
    maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()

    if not maquina:
        return None

    tarifa = get_tarifa_maquina(maquina.nombre)

    return TarifaMaquinaSchema(
        maquina_id=maquina.id,
        maquina_nombre=maquina.nombre,
        tarifa_hora=tarifa
    )

def _get_items_aridos_filtrados(
    db: Session,
    proyecto_id: int,
    periodo_inicio: date,
    periodo_fin: date,
    tipos_aridos: Optional[List[str]] = None
) -> List[ItemAridoDetalle]:
    """
    Obtiene los items individuales de áridos con filtros opcionales.
    Función auxiliar privada para create_reporte.
    """
    query = db.query(EntregaArido).filter(
        EntregaArido.proyecto_id == proyecto_id,
        EntregaArido.fecha_entrega >= periodo_inicio,
        EntregaArido.fecha_entrega <= periodo_fin
    )

    # Aplicar filtro de tipos si se especifica
    if tipos_aridos and len(tipos_aridos) > 0:
        query = query.filter(EntregaArido.tipo_arido.in_(tipos_aridos))

    entregas_aridos = query.all()

    items_aridos = []
    for arido in entregas_aridos:
        precio_unitario = arido.precio_unitario if arido.precio_unitario is not None else get_precio_arido(arido.tipo_arido)
        importe = arido.cantidad * precio_unitario

        items_aridos.append(ItemAridoDetalle(
            id=arido.id,
            tipo_arido=arido.tipo_arido,
            cantidad=arido.cantidad,
            precio_unitario=precio_unitario,
            importe=importe,
            pagado=arido.pagado if arido.pagado is not None else False,
            fecha=arido.fecha_entrega.date()
        ))

    return items_aridos

def _get_items_horas_filtrados(
    db: Session,
    proyecto_id: int,
    periodo_inicio: date,
    periodo_fin: date,
    maquinas_ids: Optional[List[int]] = None
) -> List[ItemHoraDetalle]:
    """
    Obtiene los items individuales de horas con filtros opcionales.
    Función auxiliar privada para create_reporte.
    """
    query = db.query(ReporteLaboral).options(
        joinedload(ReporteLaboral.maquina),
        joinedload(ReporteLaboral.usuario)
    ).filter(
        ReporteLaboral.proyecto_id == proyecto_id,
        ReporteLaboral.fecha_asignacion >= periodo_inicio,
        ReporteLaboral.fecha_asignacion <= periodo_fin
    )

    # Aplicar filtro de máquinas si se especifica
    if maquinas_ids and len(maquinas_ids) > 0:
        query = query.filter(ReporteLaboral.maquina_id.in_(maquinas_ids))

    reportes_horas = query.all()

    items_horas = []
    for reporte_hora in reportes_horas:
        tarifa_hora = reporte_hora.tarifa_hora if reporte_hora.tarifa_hora is not None else get_tarifa_maquina(reporte_hora.maquina.nombre)
        importe = reporte_hora.horas_turno * tarifa_hora

        items_horas.append(ItemHoraDetalle(
            id=reporte_hora.id,
            maquina_id=reporte_hora.maquina_id,
            maquina_nombre=reporte_hora.maquina.nombre,
            total_horas=reporte_hora.horas_turno,
            tarifa_hora=tarifa_hora,
            importe=importe,
            pagado=reporte_hora.pagado if reporte_hora.pagado is not None else False,
            fecha=reporte_hora.fecha_asignacion.date(),
            usuario_nombre=reporte_hora.usuario.nombre if reporte_hora.usuario else None
        ))

    return items_horas

def get_detalle_reporte(
    db: Session,
    reporte_id: int
) -> Optional[DetalleReporteResponse]:
    """
    Obtiene el detalle de items individuales de áridos y horas de un reporte.

    IMPORTANTE: Lee los items desde las tablas relacionales (reporte_items_aridos, reporte_items_horas)
    para obtener SOLO los items que fueron seleccionados al crear el reporte.
    """
    # Obtener el reporte
    reporte = db.query(ReporteCuentaCorriente).filter(
        ReporteCuentaCorriente.id == reporte_id
    ).first()

    if not reporte:
        return None

    # Obtener items de áridos desde la tabla relacional
    items_aridos_rel = db.query(ReporteItemArido).filter(
        ReporteItemArido.reporte_id == reporte_id
    ).all()

    # Obtener las entregas de áridos correspondientes
    entregas_aridos = []
    for item_rel in items_aridos_rel:
        arido = db.query(EntregaArido).filter(EntregaArido.id == item_rel.entrega_arido_id).first()
        if arido:
            entregas_aridos.append(arido)

    # Convertir áridos a ItemAridoDetalle
    items_aridos = []
    for arido in entregas_aridos:
        precio_unitario = arido.precio_unitario if arido.precio_unitario is not None else get_precio_arido(arido.tipo_arido)
        importe = arido.cantidad * precio_unitario

        items_aridos.append(ItemAridoDetalle(
            id=arido.id,
            tipo_arido=arido.tipo_arido,
            cantidad=arido.cantidad,
            precio_unitario=precio_unitario,
            importe=importe,
            pagado=arido.pagado if arido.pagado is not None else False,
            fecha=arido.fecha_entrega.date()
        ))

    # Obtener items de horas desde la tabla relacional
    items_horas_rel = db.query(ReporteItemHora).filter(
        ReporteItemHora.reporte_id == reporte_id
    ).all()

    # Obtener los reportes laborales correspondientes
    reportes_horas = []
    for item_rel in items_horas_rel:
        reporte_hora = db.query(ReporteLaboral).options(
            joinedload(ReporteLaboral.maquina),
            joinedload(ReporteLaboral.usuario)
        ).filter(ReporteLaboral.id == item_rel.reporte_laboral_id).first()
        if reporte_hora:
            reportes_horas.append(reporte_hora)

    # Convertir horas a ItemHoraDetalle
    items_horas = []
    for reporte_hora in reportes_horas:
        tarifa_hora = reporte_hora.tarifa_hora if reporte_hora.tarifa_hora is not None else get_tarifa_maquina(reporte_hora.maquina.nombre)
        importe = reporte_hora.horas_turno * tarifa_hora

        items_horas.append(ItemHoraDetalle(
            id=reporte_hora.id,
            maquina_id=reporte_hora.maquina_id,
            maquina_nombre=reporte_hora.maquina.nombre,
            total_horas=reporte_hora.horas_turno,
            tarifa_hora=tarifa_hora,
            importe=importe,
            pagado=reporte_hora.pagado if reporte_hora.pagado is not None else False,
            fecha=reporte_hora.fecha_asignacion.date(),
            usuario_nombre=reporte_hora.usuario.nombre if reporte_hora.usuario else None
        ))

    return DetalleReporteResponse(
        items_aridos=items_aridos,
        items_horas=items_horas
    )

def actualizar_items_pago(
    db: Session,
    reporte_id: int,
    items_data: ActualizarItemsPagoRequest
) -> Optional[ActualizarItemsPagoResponse]:
    """
    Actualiza el estado de pago de items individuales (áridos y horas) de un reporte.

    Args:
        db: Sesión de base de datos
        reporte_id: ID del reporte
        items_data: Lista de items a actualizar con sus estados de pago

    Returns:
        Respuesta con el número de items actualizados y el reporte actualizado
    """
    # Verificar que el reporte existe
    reporte = db.query(ReporteCuentaCorriente).filter(
        ReporteCuentaCorriente.id == reporte_id
    ).first()

    if not reporte:
        return None

    aridos_actualizados = 0
    horas_actualizadas = 0

    # Actualizar items de áridos
    for item in items_data.items_aridos:
        arido = db.query(EntregaArido).filter(
            EntregaArido.id == item.item_id,
            EntregaArido.proyecto_id == reporte.proyecto_id
        ).first()

        if arido:
            arido.pagado = item.pagado
            aridos_actualizados += 1

    # Actualizar items de horas
    for item in items_data.items_horas:
        reporte_hora = db.query(ReporteLaboral).filter(
            ReporteLaboral.id == item.item_id,
            ReporteLaboral.proyecto_id == reporte.proyecto_id
        ).first()

        if reporte_hora:
            reporte_hora.pagado = item.pagado
            horas_actualizadas += 1

    # Guardar cambios de items individuales
    db.commit()

    # ============= CALCULAR ESTADO GENERAL DEL REPORTE =============
    # Obtener SOLO los items de áridos que pertenecen a este reporte (desde tabla relacional)
    items_aridos_rel = db.query(ReporteItemArido).filter(
        ReporteItemArido.reporte_id == reporte_id
    ).all()

    todos_aridos = []
    for item_rel in items_aridos_rel:
        arido = db.query(EntregaArido).filter(EntregaArido.id == item_rel.entrega_arido_id).first()
        if arido:
            todos_aridos.append(arido)

    # Obtener SOLO los items de horas que pertenecen a este reporte (desde tabla relacional)
    items_horas_rel = db.query(ReporteItemHora).filter(
        ReporteItemHora.reporte_id == reporte_id
    ).all()

    todos_reportes_horas = []
    for item_rel in items_horas_rel:
        reporte_hora = db.query(ReporteLaboral).filter(ReporteLaboral.id == item_rel.reporte_laboral_id).first()
        if reporte_hora:
            todos_reportes_horas.append(reporte_hora)

    # Calcular totales
    total_items = len(todos_aridos) + len(todos_reportes_horas)

    if total_items == 0:
        # Si no hay items, mantener el estado pendiente
        reporte.estado = "pendiente"
    else:
        # Contar items pagados
        aridos_pagados = sum(1 for arido in todos_aridos if arido.pagado)
        horas_pagadas = sum(1 for hora in todos_reportes_horas if hora.pagado)
        total_pagados = aridos_pagados + horas_pagadas

        # Determinar estado del reporte basándose en items pagados
        if total_pagados == 0:
            # Ningún item pagado
            reporte.estado = "pendiente"
        elif total_pagados == total_items:
            # Todos los items pagados
            reporte.estado = "pagado"
        else:
            # Algunos items pagados (pago parcial)
            reporte.estado = "parcial"

    # Guardar cambios del estado del reporte
    db.commit()
    db.refresh(reporte)

    return ActualizarItemsPagoResponse(
        aridos_actualizados=aridos_actualizados,
        horas_actualizadas=horas_actualizadas,
        reporte=ReporteCuentaCorrienteOut.model_validate(reporte)
    )
```

---

## PASO 5: ROUTER DE API

Crea el archivo del router:

**Archivo**: `app/routers/cuenta_corriente_router.py`

**NOTA**: Este archivo es extenso (700+ líneas). Lo dividiré en secciones para claridad.

### Sección 1: Importaciones y configuración

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional
from datetime import date, datetime
from app.db.dependencies import get_db
from app.db.models import Proyecto, EntregaArido, ReporteLaboral
from app.schemas.schemas import (
    ReporteCuentaCorrienteCreate,
    ReporteCuentaCorrienteUpdate,
    ReporteCuentaCorrienteOut,
    ResumenProyectoSchema,
    PrecioAridoSchema,
    TarifaMaquinaSchema,
    ActualizarPrecioAridoRequest,
    ActualizarPrecioAridoResponse,
    ActualizarTarifaMaquinaRequest,
    ActualizarTarifaMaquinaResponse,
    DetalleReporteResponse,
    ActualizarItemsPagoRequest,
    ActualizarItemsPagoResponse,
    ReporteCuentaCorrienteConDetalleOut
)
from sqlalchemy.orm import Session
from app.services import cuenta_corriente_service
from app.security.auth import get_current_user  # Ajusta según tu sistema de autenticación
import io
import pandas as pd
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.units import inch
import os

router = APIRouter(
    prefix="/cuenta-corriente",
    tags=["Cuenta Corriente"],
    dependencies=[Depends(get_current_user)]  # Ajusta según tu sistema
)
```

### Sección 2: Endpoints de Precios y Tarifas

```python
# ============= Endpoints de Precios y Tarifas =============

@router.get("/aridos/precios", response_model=List[PrecioAridoSchema])
def get_precios_aridos(session: Session = Depends(get_db)):
    """
    Obtiene todos los precios de áridos disponibles por m³
    """
    return cuenta_corriente_service.get_todos_precios_aridos()

@router.get("/maquinas/{maquina_id}/tarifa", response_model=TarifaMaquinaSchema)
def get_tarifa_maquina(
    maquina_id: int,
    session: Session = Depends(get_db)
):
    """
    Obtiene la tarifa por hora de una máquina específica
    """
    tarifa = cuenta_corriente_service.get_tarifa_maquina_por_id(session, maquina_id)

    if not tarifa:
        raise HTTPException(status_code=404, detail=f"Máquina con ID {maquina_id} no encontrada")

    return tarifa
```

### Sección 3: Endpoints de Resumen de Proyecto

```python
# ============= Endpoints de Resumen de Proyecto =============

@router.get("/proyectos/{proyecto_id}/resumen", response_model=ResumenProyectoSchema)
def get_resumen_proyecto(
    proyecto_id: int,
    periodo_inicio: date = Query(..., description="Fecha de inicio del período"),
    periodo_fin: date = Query(..., description="Fecha de fin del período"),
    session: Session = Depends(get_db)
):
    """
    Obtiene el resumen de áridos y horas de un proyecto con precios calculados
    para un período determinado.

    Retorna:
    - Detalle de áridos entregados con sus precios por m³
    - Detalle de horas de máquinas con sus tarifas por hora
    - Totales e importes calculados
    """
    resumen = cuenta_corriente_service.get_resumen_proyecto(
        session,
        proyecto_id,
        periodo_inicio,
        periodo_fin
    )

    if not resumen:
        raise HTTPException(
            status_code=404,
            detail=f"Proyecto con ID {proyecto_id} no encontrado"
        )

    return resumen
```

### Sección 4: Endpoints CRUD de Reportes

```python
# ============= Endpoints de Reportes =============

@router.get("/reportes", response_model=List[ReporteCuentaCorrienteOut])
def get_reportes(
    proyecto_id: Optional[int] = Query(None, description="Filtrar por proyecto"),
    session: Session = Depends(get_db)
):
    """
    Lista todos los reportes de cuenta corriente generados.
    Opcionalmente filtra por proyecto.
    """
    return cuenta_corriente_service.get_reportes(session, proyecto_id)

@router.get("/reportes/{reporte_id}", response_model=ReporteCuentaCorrienteOut)
def get_reporte(
    reporte_id: int,
    session: Session = Depends(get_db)
):
    """
    Obtiene un reporte específico por su ID
    """
    reporte = cuenta_corriente_service.get_reporte(session, reporte_id)

    if not reporte:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    return reporte

@router.get("/reportes/{reporte_id}/detalle", response_model=DetalleReporteResponse)
def get_detalle_reporte(
    reporte_id: int,
    session: Session = Depends(get_db)
):
    """
    Obtiene el detalle de items individuales (áridos y horas) de un reporte.

    Retorna:
    - items_aridos: Lista de entregas de áridos con id, tipo, cantidad, precio, importe, pagado, fecha
    - items_horas: Lista de reportes de horas con id, maquina_id, nombre, horas, tarifa, importe, pagado, fecha, usuario
    """
    detalle = cuenta_corriente_service.get_detalle_reporte(session, reporte_id)

    if not detalle:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    return detalle

@router.put("/reportes/{reporte_id}/items-pago", response_model=ActualizarItemsPagoResponse)
def actualizar_items_pago(
    reporte_id: int,
    items_data: ActualizarItemsPagoRequest,
    session: Session = Depends(get_db)
):
    """
    Actualiza el estado de pago de items individuales (áridos y horas) de un reporte.

    Permite marcar items específicos como pagados o no pagados, actualizando las columnas
    'pagado' en las tablas entrega_arido y reporte_laboral.

    Args:
        reporte_id: ID del reporte
        items_data: Lista de items de áridos y horas con sus estados de pago

    Returns:
        Resumen de actualización con número de items actualizados y reporte actualizado
    """
    resultado = cuenta_corriente_service.actualizar_items_pago(
        session,
        reporte_id,
        items_data
    )

    if not resultado:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    return resultado

@router.post("/reportes", response_model=ReporteCuentaCorrienteConDetalleOut, status_code=201)
def create_reporte(
    reporte_data: ReporteCuentaCorrienteCreate,
    session: Session = Depends(get_db)
):
    """
    Genera un nuevo reporte de cuenta corriente para un proyecto y período específico.

    El reporte calculará automáticamente:
    - Total de áridos entregados (m³)
    - Total de horas de máquinas
    - Importes según precios y tarifas configurados

    Soporta selección de items específicos mediante:
    - aridos_seleccionados: Lista de tipos de áridos a incluir (opcional)
    - maquinas_seleccionadas: Lista de IDs de máquinas a incluir (opcional)

    Si no se especifican, se incluyen todos los items del período.
    """
    try:
        return cuenta_corriente_service.create_reporte(session, reporte_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el reporte: {str(e)}")

@router.put("/reportes/{reporte_id}/estado", response_model=ReporteCuentaCorrienteOut)
def update_estado_reporte(
    reporte_id: int,
    reporte_update: ReporteCuentaCorrienteUpdate,
    session: Session = Depends(get_db)
):
    """
    Actualiza el estado de un reporte (pendiente/pagado) y otros campos opcionales.

    Permite actualizar:
    - Estado (pendiente/pagado)
    - Observaciones
    - Número de factura
    - Fecha de pago
    """
    reporte = cuenta_corriente_service.update_reporte_estado(
        session,
        reporte_id,
        reporte_update
    )

    if not reporte:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    return reporte

@router.delete("/reportes/{reporte_id}", status_code=204)
def delete_reporte(
    reporte_id: int,
    session: Session = Depends(get_db)
):
    """
    Elimina un reporte de cuenta corriente
    """
    success = cuenta_corriente_service.delete_reporte(session, reporte_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    return JSONResponse(
        status_code=204,
        content={"message": "Reporte eliminado exitosamente"}
    )
```

### Sección 5: Endpoints de Exportación (Excel)

```python
# ============= Endpoints de Exportación =============

@router.get("/reportes/{reporte_id}/excel")
def exportar_reporte_excel(
    reporte_id: int,
    session: Session = Depends(get_db)
):
    """
    Exporta un reporte de cuenta corriente a formato Excel (.xlsx)
    """
    # Obtener el reporte
    reporte = cuenta_corriente_service.get_reporte(session, reporte_id)
    if not reporte:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    # Obtener el resumen detallado
    resumen = cuenta_corriente_service.get_resumen_proyecto(
        session,
        reporte.proyecto_id,
        reporte.periodo_inicio,
        reporte.periodo_fin
    )

    if not resumen:
        raise HTTPException(status_code=404, detail="No se pudo obtener el resumen del proyecto")

    # Crear el archivo Excel en memoria
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Información general
        info_data = {
            'Campo': ['Proyecto', 'Período', 'Fecha Generación', 'Estado', 'N° Factura'],
            'Valor': [
                resumen.proyecto_nombre,
                f"{reporte.periodo_inicio} - {reporte.periodo_fin}",
                reporte.fecha_generacion.strftime("%d/%m/%Y %H:%M"),
                reporte.estado,
                reporte.numero_factura or 'N/A'
            ]
        }
        df_info = pd.DataFrame(info_data)
        df_info.to_excel(writer, sheet_name='Información', index=False)

        # Detalle de áridos
        if resumen.aridos:
            aridos_data = {
                'Tipo Árido': [a.tipo_arido for a in resumen.aridos],
                'Cantidad (m³)': [a.cantidad for a in resumen.aridos],
                'Precio Unitario': [a.precio_unitario for a in resumen.aridos],
                'Importe': [a.importe for a in resumen.aridos]
            }
            df_aridos = pd.DataFrame(aridos_data)
            df_aridos.to_excel(writer, sheet_name='Áridos', index=False)

        # Detalle de horas de máquinas
        if resumen.horas_maquinas:
            horas_data = {
                'Máquina': [h.maquina_nombre for h in resumen.horas_maquinas],
                'Total Horas': [h.total_horas for h in resumen.horas_maquinas],
                'Tarifa/Hora': [h.tarifa_hora for h in resumen.horas_maquinas],
                'Importe': [h.importe for h in resumen.horas_maquinas]
            }
            df_horas = pd.DataFrame(horas_data)
            df_horas.to_excel(writer, sheet_name='Horas Máquinas', index=False)

        # Resumen de totales
        totales_data = {
            'Concepto': [
                'Total Áridos (m³)',
                'Importe Áridos',
                'Total Horas',
                'Importe Horas',
                'IMPORTE TOTAL'
            ],
            'Valor': [
                resumen.total_aridos_m3,
                resumen.total_importe_aridos,
                resumen.total_horas,
                resumen.total_importe_horas,
                resumen.importe_total
            ]
        }
        df_totales = pd.DataFrame(totales_data)
        df_totales.to_excel(writer, sheet_name='Totales', index=False)

    output.seek(0)

    filename = f"reporte_cuenta_corriente_{reporte_id}_{resumen.proyecto_nombre.replace(' ', '_')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

### Sección 6: Endpoints de Exportación (PDF)

```python
@router.get("/reportes/{reporte_id}/pdf")
def exportar_reporte_pdf(
    reporte_id: int,
    session: Session = Depends(get_db)
):
    """
    Exporta un reporte de cuenta corriente a formato PDF
    """
    # Obtener el reporte
    reporte = cuenta_corriente_service.get_reporte(session, reporte_id)
    if not reporte:
        raise HTTPException(
            status_code=404,
            detail=f"Reporte con ID {reporte_id} no encontrado"
        )

    # Obtener el resumen detallado
    resumen = cuenta_corriente_service.get_resumen_proyecto(
        session,
        reporte.proyecto_id,
        reporte.periodo_inicio,
        reporte.periodo_fin
    )

    if not resumen:
        raise HTTPException(status_code=404, detail="No se pudo obtener el resumen del proyecto")

    # Crear el PDF en memoria
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Logo en el encabezado (si existe)
    logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'assets', 'logo-kedikian.png')
    if os.path.exists(logo_path):
        try:
            # El logo es casi cuadrado (536x528), mantener proporción 1:1
            logo = Image(logo_path, width=120, height=120)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 0.2*inch))
        except Exception as e:
            # Si hay error al cargar la imagen, continuar sin logo
            print(f"Advertencia: No se pudo cargar el logo: {e}")

    # Título
    title = Paragraph(f"<b>REPORTE DE CUENTA CORRIENTE</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))

    # Información general
    info_text = f"""
    <b>Proyecto:</b> {resumen.proyecto_nombre}<br/>
    <b>Período:</b> {reporte.periodo_inicio} al {reporte.periodo_fin}<br/>
    <b>Fecha de Generación:</b> {reporte.fecha_generacion.strftime("%d/%m/%Y %H:%M")}<br/>
    <b>Estado:</b> {reporte.estado.upper()}<br/>
    <b>N° Factura:</b> {reporte.numero_factura or 'N/A'}
    """
    info_para = Paragraph(info_text, styles['Normal'])
    elements.append(info_para)
    elements.append(Spacer(1, 0.3*inch))

    # Tabla de áridos
    if resumen.aridos:
        aridos_title = Paragraph("<b>DETALLE DE ÁRIDOS</b>", styles['Heading2'])
        elements.append(aridos_title)
        elements.append(Spacer(1, 0.1*inch))

        aridos_data = [['Tipo Árido', 'Cantidad (m³)', 'Precio/m³', 'Importe']]
        for arido in resumen.aridos:
            aridos_data.append([
                arido.tipo_arido,
                f"{arido.cantidad:.2f}",
                f"${arido.precio_unitario:,.2f}",
                f"${arido.importe:,.2f}"
            ])

        aridos_table = Table(aridos_data)
        aridos_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(aridos_table)
        elements.append(Spacer(1, 0.3*inch))

    # Tabla de horas de máquinas
    if resumen.horas_maquinas:
        horas_title = Paragraph("<b>DETALLE DE HORAS DE MÁQUINAS</b>", styles['Heading2'])
        elements.append(horas_title)
        elements.append(Spacer(1, 0.1*inch))

        horas_data = [['Máquina', 'Total Horas', 'Tarifa/Hora', 'Importe']]
        for hora in resumen.horas_maquinas:
            horas_data.append([
                hora.maquina_nombre,
                f"{hora.total_horas:.2f}",
                f"${hora.tarifa_hora:,.2f}",
                f"${hora.importe:,.2f}"
            ])

        horas_table = Table(horas_data)
        horas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(horas_table)
        elements.append(Spacer(1, 0.3*inch))

    # Totales
    totales_title = Paragraph("<b>TOTALES</b>", styles['Heading2'])
    elements.append(totales_title)
    elements.append(Spacer(1, 0.1*inch))

    totales_data = [
        ['Concepto', 'Valor'],
        ['Total Áridos (m³)', f"{resumen.total_aridos_m3:.2f}"],
        ['Importe Áridos', f"${resumen.total_importe_aridos:,.2f}"],
        ['Total Horas', f"{resumen.total_horas:.2f}"],
        ['Importe Horas', f"${resumen.total_importe_horas:,.2f}"],
        ['IMPORTE TOTAL', f"${resumen.importe_total:,.2f}"]
    ]

    totales_table = Table(totales_data)
    totales_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(totales_table)

    # Observaciones
    if reporte.observaciones:
        elements.append(Spacer(1, 0.3*inch))
        obs_title = Paragraph("<b>OBSERVACIONES</b>", styles['Heading2'])
        elements.append(obs_title)
        obs_text = Paragraph(reporte.observaciones, styles['Normal'])
        elements.append(obs_text)

    # Generar PDF
    doc.build(elements)
    buffer.seek(0)

    filename = f"reporte_cuenta_corriente_{reporte_id}_{resumen.proyecto_nombre.replace(' ', '_')}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

### Sección 7: Endpoints de Actualización de Precios y Tarifas

```python
# ============= ENDPOINTS PARA ACTUALIZACIÓN DE PRECIOS Y TARIFAS =============

@router.put("/proyectos/{proyecto_id}/aridos/actualizar-precio", response_model=ActualizarPrecioAridoResponse)
async def actualizar_precio_arido(
    proyecto_id: int,
    data: ActualizarPrecioAridoRequest,
    db: Session = Depends(get_db)
):
    """
    Actualiza el precio unitario de todos los registros de áridos
    de un tipo específico en un período determinado.

    Args:
        proyecto_id: ID del proyecto
        data: Datos de actualización (tipo_arido, nuevo_precio, periodo_inicio, periodo_fin)
        db: Sesión de base de datos

    Returns:
        Resumen de la actualización con información de precios e importes

    Raises:
        HTTPException 404: Si el proyecto no existe
        HTTPException 400: Si no hay registros que actualizar o el precio no es válido
    """
    try:
        # Verificar que el proyecto existe
        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        # Validar nuevo precio
        if data.nuevo_precio <= 0:
            raise HTTPException(status_code=400, detail="El precio debe ser mayor a 0")

        # Validar fechas
        if data.periodo_inicio > data.periodo_fin:
            raise HTTPException(
                status_code=400,
                detail="La fecha de inicio debe ser anterior a la fecha de fin"
            )

        # Buscar todos los registros de áridos que coinciden con los criterios
        registros = db.query(EntregaArido).filter(
            EntregaArido.proyecto_id == proyecto_id,
            EntregaArido.tipo_arido == data.tipo_arido,
            EntregaArido.fecha_entrega >= datetime.combine(data.periodo_inicio, datetime.min.time()),
            EntregaArido.fecha_entrega <= datetime.combine(data.periodo_fin, datetime.max.time())
        ).all()

        if not registros:
            raise HTTPException(
                status_code=400,
                detail=f"No se encontraron registros de árido '{data.tipo_arido}' en el período especificado"
            )

        # Calcular estadísticas anteriores
        registros_actualizados = len(registros)

        # Calcular precio anterior promedio (solo de los registros que tienen precio)
        precios_anteriores = [r.precio_unitario for r in registros if r.precio_unitario is not None]
        precio_anterior = sum(precios_anteriores) / len(precios_anteriores) if precios_anteriores else 0.0

        # Calcular importe anterior (suma de cantidad * precio_unitario)
        importe_anterior = sum(
            (r.cantidad * r.precio_unitario) if r.precio_unitario is not None else 0.0
            for r in registros
        )

        # Actualizar precio_unitario de cada registro
        for registro in registros:
            registro.precio_unitario = data.nuevo_precio

        # Calcular importe nuevo
        importe_nuevo = sum(r.cantidad * data.nuevo_precio for r in registros)

        # Calcular diferencia
        diferencia = importe_nuevo - importe_anterior

        # Guardar cambios
        db.commit()

        return ActualizarPrecioAridoResponse(
            registros_actualizados=registros_actualizados,
            precio_anterior=round(precio_anterior, 2),
            precio_nuevo=round(data.nuevo_precio, 2),
            importe_anterior=round(importe_anterior, 2),
            importe_nuevo=round(importe_nuevo, 2),
            diferencia=round(diferencia, 2)
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar precio de áridos: {str(e)}"
        )

@router.put("/proyectos/{proyecto_id}/maquinas/actualizar-tarifa", response_model=ActualizarTarifaMaquinaResponse)
async def actualizar_tarifa_maquina(
    proyecto_id: int,
    data: ActualizarTarifaMaquinaRequest,
    db: Session = Depends(get_db)
):
    """
    Actualiza la tarifa por hora de todos los registros de horas
    de una máquina específica en un período determinado.

    Args:
        proyecto_id: ID del proyecto
        data: Datos de actualización (maquina_id, nueva_tarifa, periodo_inicio, periodo_fin)
        db: Sesión de base de datos

    Returns:
        Resumen de la actualización con información de tarifas e importes

    Raises:
        HTTPException 404: Si el proyecto no existe
        HTTPException 400: Si no hay registros que actualizar o la tarifa no es válida
    """
    try:
        # Verificar que el proyecto existe
        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        # Validar nueva tarifa
        if data.nueva_tarifa <= 0:
            raise HTTPException(status_code=400, detail="La tarifa debe ser mayor a 0")

        # Validar fechas
        if data.periodo_inicio > data.periodo_fin:
            raise HTTPException(
                status_code=400,
                detail="La fecha de inicio debe ser anterior a la fecha de fin"
            )

        # Buscar todos los registros de reportes laborales que coinciden con los criterios
        registros = db.query(ReporteLaboral).filter(
            ReporteLaboral.proyecto_id == proyecto_id,
            ReporteLaboral.maquina_id == data.maquina_id,
            ReporteLaboral.fecha_asignacion >= datetime.combine(data.periodo_inicio, datetime.min.time()),
            ReporteLaboral.fecha_asignacion <= datetime.combine(data.periodo_fin, datetime.max.time())
        ).all()

        if not registros:
            raise HTTPException(
                status_code=400,
                detail=f"No se encontraron registros de horas para la máquina {data.maquina_id} en el período especificado"
            )

        # Calcular estadísticas anteriores
        registros_actualizados = len(registros)

        # Calcular tarifa anterior promedio (solo de los registros que tienen tarifa)
        tarifas_anteriores = [r.tarifa_hora for r in registros if r.tarifa_hora is not None]
        tarifa_anterior = sum(tarifas_anteriores) / len(tarifas_anteriores) if tarifas_anteriores else 0.0

        # Calcular importe anterior (suma de horas_turno * tarifa_hora)
        importe_anterior = sum(
            (r.horas_turno * r.tarifa_hora) if r.tarifa_hora is not None else 0.0
            for r in registros
        )

        # Actualizar tarifa_hora de cada registro
        for registro in registros:
            registro.tarifa_hora = data.nueva_tarifa

        # Calcular importe nuevo
        importe_nuevo = sum(r.horas_turno * data.nueva_tarifa for r in registros)

        # Calcular diferencia
        diferencia = importe_nuevo - importe_anterior

        # Guardar cambios
        db.commit()

        return ActualizarTarifaMaquinaResponse(
            registros_actualizados=registros_actualizados,
            tarifa_anterior=round(tarifa_anterior, 2),
            tarifa_nueva=round(data.nueva_tarifa, 2),
            importe_anterior=round(importe_anterior, 2),
            importe_nuevo=round(importe_nuevo, 2),
            diferencia=round(diferencia, 2)
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar tarifa de máquina: {str(e)}"
        )
```

---

## PASO 6: REGISTRO DEL ROUTER

En tu archivo principal (por ejemplo `main.py` o `app.py`), registra el router:

```python
from fastapi import FastAPI
from app.routers import cuenta_corriente_router

app = FastAPI()

# ... otros routers ...

# Registrar router de Cuenta Corriente
app.include_router(
    cuenta_corriente_router.router,
    prefix="/v1",
    tags=["Cuenta Corriente"]
)
```

---

## PASO 7: CONFIGURACIÓN DE PRECIOS Y TARIFAS

### 7.1. Actualizar diccionarios de precios

Edita el archivo `app/services/cuenta_corriente_service.py` y actualiza los diccionarios:

**PRECIOS_ARIDOS**: Reemplaza con tus tipos de áridos y precios reales.

```python
PRECIOS_ARIDOS: Dict[str, float] = {
    "Arena Fina": 54000.0,
    "Granza": 54000.0,
    "Arena Común": 33680.0,
    # ... tus tipos de áridos
}
```

**TARIFAS_MAQUINAS**: Para obtener los nombres exactos de tus máquinas, ejecuta:

```sql
SELECT id, nombre FROM maquina;
```

Luego actualiza el diccionario con los nombres EXACTOS (case-sensitive):

```python
TARIFAS_MAQUINAS: Dict[str, float] = {
    "default": 15000.0,  # Tarifa por defecto
    "NOMBRE_EXACTO_MAQUINA_1": 100000,
    "NOMBRE_EXACTO_MAQUINA_2": 150000,
    # ... tus máquinas
}
```

### 7.2. Agregar logo para PDF (OPCIONAL)

Si quieres incluir un logo en los PDFs, coloca tu imagen en:

```
static/assets/logo-kedikian.png
```

O ajusta la ruta en el router:

```python
logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'assets', 'TU_LOGO.png')
```

---

## PASO 8: TESTING Y VALIDACIÓN

### 8.1. Ejecutar migraciones

```bash
# Si usas Alembic
alembic upgrade head

# Si ejecutas SQL manualmente
psql -U tu_usuario -d tu_database -f migrations/add_precio_tarifa_fields.sql
psql -U tu_usuario -d tu_database -f migrations/add_pagado_field.sql
psql -U tu_usuario -d tu_database -f migrations/create_reportes_cuenta_corriente.sql
psql -U tu_usuario -d tu_database -f migrations/add_reporte_items_tables.sql
```

### 8.2. Verificar tablas

```sql
-- Verificar que las tablas fueron creadas
\dt reportes_cuenta_corriente
\dt reporte_items_aridos
\dt reporte_items_horas

-- Verificar campos nuevos
\d entrega_arido
\d reporte_laboral
```

### 8.3. Probar endpoints

```bash
# Iniciar servidor
uvicorn main:app --reload

# Acceder a la documentación Swagger
http://localhost:8000/docs
```

### 8.4. Casos de prueba

**1. Obtener precios de áridos**:
```
GET /v1/cuenta-corriente/aridos/precios
```

**2. Crear un reporte completo**:
```
POST /v1/cuenta-corriente/reportes
{
  "proyecto_id": 1,
  "periodo_inicio": "2026-01-01",
  "periodo_fin": "2026-01-31",
  "observaciones": "Reporte mensual de enero"
}
```

**3. Obtener detalle de reporte**:
```
GET /v1/cuenta-corriente/reportes/1/detalle
```

**4. Actualizar estado de pago de items**:
```
PUT /v1/cuenta-corriente/reportes/1/items-pago
{
  "items_aridos": [
    {"item_id": 1, "pagado": true},
    {"item_id": 2, "pagado": true}
  ],
  "items_horas": [
    {"item_id": 1, "pagado": false}
  ]
}
```

**5. Exportar a Excel**:
```
GET /v1/cuenta-corriente/reportes/1/excel
```

**6. Exportar a PDF**:
```
GET /v1/cuenta-corriente/reportes/1/pdf
```

**7. Actualizar precio retroactivo de áridos**:
```
PUT /v1/cuenta-corriente/proyectos/1/aridos/actualizar-precio
{
  "tipo_arido": "Arena Fina",
  "nuevo_precio": 60000.0,
  "periodo_inicio": "2026-01-01",
  "periodo_fin": "2026-01-31"
}
```

---

## CARACTERÍSTICAS AVANZADAS

### Estados del Reporte

El sistema calcula automáticamente el estado del reporte basándose en items pagados:

- **"pendiente"**: Ningún item pagado (0%)
- **"parcial"**: Algunos items pagados (1-99%)
- **"pagado"**: Todos los items pagados (100%)

### Filtrado Selectivo

Al crear reportes, puedes filtrar:

```json
{
  "proyecto_id": 1,
  "periodo_inicio": "2026-01-01",
  "periodo_fin": "2026-01-31",
  "aridos_seleccionados": ["Arena Fina", "Granza"],
  "maquinas_seleccionadas": [1, 3, 5]
}
```

### Actualización Retroactiva de Precios

Permite cambiar precios/tarifas de registros pasados, útil para:
- Corregir errores de facturación
- Aplicar ajustes comerciales
- Actualizar precios según contratos

---

## TROUBLESHOOTING

### Error: "relation does not exist"

Verifica que ejecutaste todas las migraciones en orden.

### Error: "column does not exist"

Asegúrate de haber agregado los campos `precio_unitario`, `tarifa_hora` y `pagado` a las tablas existentes.

### Error al exportar PDF

Verifica que `reportlab` esté instalado:
```bash
pip install reportlab
```

### Tarifas/Precios en 0

Revisa que los diccionarios `PRECIOS_ARIDOS` y `TARIFAS_MAQUINAS` estén correctamente configurados con tus datos.

---

## RESUMEN DE ARCHIVOS CREADOS

```
migrations/
├── add_precio_tarifa_fields.sql
├── add_pagado_field.sql
├── create_reportes_cuenta_corriente.sql
└── add_reporte_items_tables.sql

app/
├── db/
│   └── models/
│       ├── reporte_cuenta_corriente.py
│       └── reporte_items.py
├── schemas/
│   └── schemas.py (actualizado)
├── services/
│   └── cuenta_corriente_service.py
└── routers/
    └── cuenta_corriente_router.py

static/
└── assets/
    └── logo-kedikian.png (opcional)
```

---

## ENDPOINTS FINALES (22 TOTAL)

### Precios y Tarifas (2)
- `GET /v1/cuenta-corriente/aridos/precios`
- `GET /v1/cuenta-corriente/maquinas/{maquina_id}/tarifa`

### Resumen (1)
- `GET /v1/cuenta-corriente/proyectos/{proyecto_id}/resumen`

### Reportes CRUD (5)
- `GET /v1/cuenta-corriente/reportes`
- `GET /v1/cuenta-corriente/reportes/{reporte_id}`
- `POST /v1/cuenta-corriente/reportes`
- `PUT /v1/cuenta-corriente/reportes/{reporte_id}/estado`
- `DELETE /v1/cuenta-corriente/reportes/{reporte_id}`

### Detalle y Pagos (2)
- `GET /v1/cuenta-corriente/reportes/{reporte_id}/detalle`
- `PUT /v1/cuenta-corriente/reportes/{reporte_id}/items-pago`

### Exportación (2)
- `GET /v1/cuenta-corriente/reportes/{reporte_id}/excel`
- `GET /v1/cuenta-corriente/reportes/{reporte_id}/pdf`

### Actualización de Precios/Tarifas (2)
- `PUT /v1/cuenta-corriente/proyectos/{proyecto_id}/aridos/actualizar-precio`
- `PUT /v1/cuenta-corriente/proyectos/{proyecto_id}/maquinas/actualizar-tarifa`

---

## CONCLUSIÓN

Este prompt contiene TODA la información necesaria para implementar el módulo completo de Cuenta Corriente.

**Orden de ejecución recomendado**:
1. Ejecutar migraciones SQL (Paso 1)
2. Crear modelos SQLAlchemy (Paso 2)
3. Agregar esquemas Pydantic (Paso 3)
4. Crear servicio (Paso 4)
5. Crear router (Paso 5)
6. Registrar router en main (Paso 6)
7. Configurar precios/tarifas (Paso 7)
8. Probar endpoints (Paso 8)

**Duración estimada**: El sistema completo está listo para producción una vez completados todos los pasos.

---

**IMPORTANTE**: Recuerda adaptar:
- Nombres de tablas si difieren de los estándares
- Sistema de autenticación (`get_current_user`)
- Rutas de archivos estáticos
- Precios y tarifas según tu negocio
- Nombres de máquinas según tu base de datos
