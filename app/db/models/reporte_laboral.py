from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class ReporteLaboral(Base):
    __tablename__ = "reporte_laboral"
    id = Column(Integer, primary_key=True, autoincrement=True)
    maquina_id = Column(Integer, ForeignKey("maquina.id"))
    usuario_id = Column(Integer, ForeignKey("usuario.id"))
    fecha_asignacion = Column(DateTime)
    horas_turno = Column(DateTime)

    # Relaciones
    maquina = relationship("Maquina", back_populates="reportes_laborales")
    usuario = relationship("Usuario", back_populates="reportes_laborales")