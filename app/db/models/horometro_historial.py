from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class HorometroHistorial(Base):
    __tablename__ = "horometro_historial"

    id = Column(Integer, primary_key=True, autoincrement=True)
    maquina_id = Column(Integer, ForeignKey("maquina.id"), nullable=False)
    valor_anterior = Column(Float, nullable=False)
    valor_nuevo = Column(Float, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=True)
    motivo = Column(String(255), nullable=False)  # "reporte_laboral", "manual", "ajuste"
    reporte_laboral_id = Column(Integer, ForeignKey("reporte_laboral.id"), nullable=True)

    # Relaciones
    maquina = relationship("Maquina", backref="historial_horometro")
    usuario = relationship("Usuario", backref="cambios_horometro")
    reporte_laboral = relationship("ReporteLaboral", backref="cambio_horometro")

    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())
