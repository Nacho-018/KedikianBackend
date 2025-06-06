from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.models.base_custom import BaseCustom

class Pago(BaseCustom):
    __tablename__ = "pago"
    proyecto_id = Column(Integer, ForeignKey("proyecto.id"))
    producto_id = Column(Integer, ForeignKey("producto.id"))
    importe_total = Column(Integer)
    fecha = Column(DateTime)
    descripcion = Column(String)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="pagos")
    producto = relationship("Producto", back_populates="pagos")