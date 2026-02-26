from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.db.database import Base
from sqlalchemy.sql import func

class Cliente(Base):
    __tablename__ = "cliente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    telefono = Column(String(50), nullable=True)
    direccion = Column(String(500), nullable=True)

    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación con cotizaciones
    cotizaciones = relationship("Cotizacion", back_populates="cliente", cascade="all, delete-orphan")
