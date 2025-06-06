from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.models.base_custom import BaseCustom

class ReporteLaboral(BaseCustom):
    __tablename__ = "reporte_laboral"
    maquina_id = Column(Integer, ForeignKey("maquina.id"))
    usuario_id = Column(Integer, ForeignKey("usuario.id"))
    fecha_asignacion = Column(DateTime)
    horas_turno = Column(DateTime)

    # Relaciones
    maquina = relationship("Maquina", back_populates="reportes_laborales")
    usuario = relationship("Usuario", back_populates="reportes_laborales")