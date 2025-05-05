from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Gasto(Base):
    __tablename__ = "gasto"
    id = Column(Integer, primary_key=True, autoincrement=True)
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