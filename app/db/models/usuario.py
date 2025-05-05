from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.database import Base

class Usuario(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String)
    email = Column(String, unique=True)
    hash_contrasena = Column(String)
    estado = Column(Boolean, default=True)
    roles = Column(String)
    fecha_creacion = Column(DateTime)

    # Relaciones
    reportes_laborales = relationship("ReporteLaboral", back_populates="usuario")
    gastos = relationship("Gasto", back_populates="usuario")
    movimientos_inventario = relationship("MovimientoInventario", back_populates="usuario")