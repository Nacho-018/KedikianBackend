from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.models.base_custom import BaseCustom

class MovimientoInventario(BaseCustom):
    __tablename__ = "movimiento_inventario"
    producto_id = Column(Integer, ForeignKey("producto.id"))
    usuario_id = Column(Integer, ForeignKey("usuario.id"))
    cantidad = Column(Integer)
    fecha = Column(DateTime)
    tipo_transaccion = Column(String)  # "entrada" o "salida"

    # Relaciones
    producto = relationship("Producto", back_populates="movimientos_inventario")
    usuario = relationship("Usuario", back_populates="movimientos_inventario")