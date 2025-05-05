from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base

class Producto(Base):
    __tablename__ = "producto"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String)
    codigo_producto = Column(String)
    inventario = Column(Integer)

    # Relaciones
    pagos = relationship("Pago", back_populates="producto")
    movimientos_inventario = relationship("MovimientoInventario", back_populates="producto")