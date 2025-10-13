from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
from datetime import datetime

class Contrato(Base):
    __tablename__ = "contrato"
    id = Column(Integer, primary_key=True, autoincrement=True)
    detalle = Column(String(350))
    cliente = Column(String(45))
    importe_total = Column(Integer)
    fecha_inicio = Column(DateTime)
    fecha_terminacion = Column(DateTime)

    # Relación 1 a 1 con Proyecto
    proyecto = relationship(
        "Proyecto",
        back_populates="contrato",
        uselist=False,
        foreign_keys="[Proyecto.contrato_id]"
    )
    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())

class ContratoArchivo(Base):
    __tablename__ = "contrato_archivos"
    
    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(Integer, ForeignKey("proyecto.id"), nullable=False)  # Referencia correcta a tabla proyecto
    nombre_archivo = Column(String(255), nullable=False)
    ruta_archivo = Column(String(500), nullable=False)
    tipo_archivo = Column(String(50), nullable=False)
    tamaño_archivo = Column(BigInteger, nullable=False)
    fecha_subida = Column(DateTime, default=datetime.utcnow)
    
    proyecto = relationship("Proyecto", back_populates="contrato_archivos")