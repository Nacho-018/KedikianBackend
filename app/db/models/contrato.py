from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.models.base_custom import BaseCustom

class Contrato(BaseCustom):
    __tablename__ = "contrato"
    proyecto_id = Column(Integer, ForeignKey("proyecto.id"))
    detalle = Column(String)
    cliente = Column(String)
    importe_total = Column(Integer)
    fecha_inicio = Column(DateTime)
    fecha_terminacion = Column(DateTime)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="contrato")