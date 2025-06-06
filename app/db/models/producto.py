from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.models.base_custom import BaseCustom

class Producto(BaseCustom):
    __tablename__ = "producto"
    nombre = Column(String)
    codigo_producto = Column(String)
    inventario = Column(Integer)
    url_imagen = Column(String, nullable=True)

    # Relaciones
    pagos = relationship("Pago", back_populates="producto")
    movimientos_inventario = relationship("MovimientoInventario", back_populates="producto")