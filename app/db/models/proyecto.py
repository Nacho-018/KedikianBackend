from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from sqlalchemy.sql import func

class Proyecto(Base):
    __tablename__ = "proyecto"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(75))
    estado = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime)
    contrato_id = Column(Integer, ForeignKey("contrato.id"))
    ubicacion = Column(String(50))

    # Relaciones
    contrato = relationship("Contrato", back_populates="proyecto", foreign_keys=[contrato_id])
    arrendamientos = relationship("Arrendamiento", back_populates="proyecto")
    pagos = relationship("Pago", back_populates="proyecto")
    
    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())