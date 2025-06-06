from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.db.models.base_custom import BaseCustom

class Usuario(BaseCustom):
    __tablename__ = "usuario"
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