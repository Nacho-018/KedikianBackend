from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base

class Maquina(Base):
    __tablename__ = "maquina"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String)
    estado = Column(Boolean, default=True)
    horas_uso = Column(Integer, default=0)

    # Relaciones
    reportes_laborales = relationship("ReporteLaboral", back_populates="maquina")
    gastos = relationship("Gasto", back_populates="maquina")
    arrendamientos = relationship("Arrendamiento", back_populates="maquina")