from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Pago(Base):
    __tablename__ = "pago"
    id = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(Integer, ForeignKey("proyecto.id"))
    producto_id = Column(Integer, ForeignKey("producto.id"))
    monto = Column(Integer)
    fecha = Column(DateTime)
    descripcion = Column(String)

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="pagos")
    producto = relationship("Producto", back_populates="pagos")