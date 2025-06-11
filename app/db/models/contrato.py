from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Contrato(Base):
    __tablename__ = "contrato"
    id = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(Integer, ForeignKey("proyecto.id"))
    detalle = Column(String(350))
    cliente = Column(String(45))
    importe_total = Column(Integer)
    fecha_inicio = Column(DateTime)
    fecha_terminacion = Column(DateTime)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="contrato")
    
    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())