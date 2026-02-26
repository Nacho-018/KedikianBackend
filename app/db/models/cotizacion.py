from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, Numeric, Text
from sqlalchemy.orm import relationship
from app.db.database import Base
from sqlalchemy.sql import func

class Cotizacion(Base):
    __tablename__ = "cotizacion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("cliente.id"), nullable=False)
    fecha_creacion = Column(DateTime, nullable=False, server_default=func.now())
    fecha_validez = Column(Date, nullable=True)  # Hasta cuándo vale la cotización
    estado = Column(String(20), default="borrador")  # "borrador", "enviada", "aprobada"
    observaciones = Column(Text, nullable=True)
    importe_total = Column(Numeric(12, 2), default=0.0)  # Calculado a partir de los items

    # Relaciones
    cliente = relationship("Cliente", back_populates="cotizaciones")
    items = relationship("CotizacionItem", back_populates="cotizacion", cascade="all, delete-orphan")

    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())


class CotizacionItem(Base):
    __tablename__ = "cotizacion_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cotizacion_id = Column(Integer, ForeignKey("cotizacion.id", ondelete="CASCADE"), nullable=False)
    nombre_servicio = Column(String(255), nullable=False)  # Ej: "Arena Fina", "BOBCAT 2018 S650."
    unidad = Column(String(50), nullable=False)  # Ej: "m³", "hora"
    cantidad = Column(Float, nullable=False)
    precio_unitario = Column(Numeric(12, 2), nullable=False)  # Editable por el usuario
    subtotal = Column(Numeric(12, 2), nullable=False)  # cantidad × precio_unitario

    # Relación
    cotizacion = relationship("Cotizacion", back_populates="items")

    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())
