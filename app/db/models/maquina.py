# app/db/models/maquina.py
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Maquina(Base):
    __tablename__ = "maquina"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50))
    horas_uso = Column(Integer, default=0)
    horas_maquina = Column(Integer, default=0)
    horometro_inicial = Column(Float, default=0)  # ✅ Horómetro actual
    proximo_mantenimiento = Column(Float, nullable=True)  # ✅ Horas para el próximo mantenimiento

    # Relaciones
    reportes_laborales = relationship("ReporteLaboral", back_populates="maquina")
    gastos = relationship("Gasto", back_populates="maquina")
    arrendamientos = relationship("Arrendamiento", back_populates="maquina")
    mantenimientos = relationship("Mantenimiento", back_populates="maquina")
    notas = relationship("NotaMaquina", back_populates="maquina", cascade="all, delete-orphan")
    
    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())