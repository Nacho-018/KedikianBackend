from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from app.db.database import Base
from sqlalchemy.sql import func

class Mantenimiento(Base):
    __tablename__ = "mantenimiento"
    id = Column(Integer, primary_key=True, autoincrement=True)
    maquina_id = Column(Integer, ForeignKey("maquina.id"), nullable=False)
    tipo_mantenimiento = Column(String(50), nullable=False)
    descripcion = Column(Text, nullable=False)
    fecha_mantenimiento = Column(DateTime(timezone=True), nullable=False)
    horas_maquina = Column(Integer, nullable=False)
    costo = Column(Float, nullable=True)
    responsable = Column(String(100), nullable=True)
    observaciones = Column(Text, nullable=True)
    
    # Relaciones
    maquina = relationship("Maquina", back_populates="mantenimientos")
    
    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())
