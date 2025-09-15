from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from sqlalchemy.sql import func

class ReporteLaboral(Base):
    __tablename__ = "reporte_laboral"
    id = Column(Integer, primary_key=True, autoincrement=True)
    maquina_id = Column(Integer, ForeignKey("maquina.id"))
    usuario_id = Column(Integer, ForeignKey("usuario.id"))
    proyecto_id = Column(Integer, ForeignKey("proyecto.id"))
    fecha_asignacion = Column(DateTime)
    horas_turno = Column(Integer)

    # Relaciones
    maquina = relationship("Maquina", back_populates="reportes_laborales")
    usuario = relationship("Usuario", back_populates="reportes_laborales")
    proyecto = relationship("Proyecto", back_populates="reportes_laborales")
    
    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())