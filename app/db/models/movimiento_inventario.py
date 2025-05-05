from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class MovimientoInventario(Base):
    __tablename__ = "movimiento_inventario"
    id = Column(Integer, primary_key=True, autoincrement=True)
    producto_id = Column(Integer, ForeignKey("producto.id"))
    usuario_id = Column(Integer, ForeignKey("usuario.id"))
    cantidad = Column(Integer)
    fecha = Column(DateTime)
    tipo_transaccion = Column(String)  # "entrada" o "salida"

    # Relaciones
    producto = relationship("Producto", back_populates="movimientos_inventario")
    usuario = relationship("Usuario", back_populates="movimientos_inventario")