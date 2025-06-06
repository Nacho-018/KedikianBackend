from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.models.base_custom import BaseCustom

class Gasto(BaseCustom):
    __tablename__ = "gasto"
    usuario_id = Column(Integer, ForeignKey("usuario.id"))
    maquina_id = Column(Integer, ForeignKey("maquina.id"))
    tipo = Column(String)
    importe_total = Column(Integer)
    fecha = Column(DateTime)
    descripcion = Column(String)
    imagen = Column(String)

    # Relaciones
    usuario = relationship("Usuario", back_populates="gastos")
    maquina = relationship("Maquina", back_populates="gastos")