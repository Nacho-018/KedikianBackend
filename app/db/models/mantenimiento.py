from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Mantenimiento(Base):
    __tablename__ = "mantenimiento"
    id = Column(Integer, primary_key=True, autoincrement=True)
    maquina_id = Column(Integer, ForeignKey("maquina.id"))
    tipo = Column(String(15), nullable=True)
    fecha = Column(DateTime)
    descripcion = Column(String(300))

    # Relaciones
    maquina = relationship("Maquina", back_populates="mantenimientos")
    
    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())