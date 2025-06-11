from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Usuario(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50))
    email = Column(String(70), unique=True)
    hash_contrasena = Column(String(256))
    estado = Column(Boolean, default=True)
    roles = Column(String(15))
    fecha_creacion = Column(DateTime)

    # Relaciones
    reportes_laborales = relationship("ReporteLaboral", back_populates="usuario")
    gastos = relationship("Gasto", back_populates="usuario")
    movimientos_inventario = relationship("MovimientoInventario", back_populates="usuario")
    
    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())