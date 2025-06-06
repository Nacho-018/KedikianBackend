from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.models.base_custom import BaseCustom

class Arrendamiento(BaseCustom):
    __tablename__ = "arrendamiento"
    proyecto_id = Column(Integer, ForeignKey("proyecto.id"))
    maquina_id = Column(Integer, ForeignKey("maquina.id"))
    horas_uso = Column(Integer, default=0)
    fecha_asignacion = Column(DateTime)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="arrendamientos")
    maquina = relationship("Maquina", back_populates="arrendamientos")