from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class TarifaMaquinaProyecto(Base):
    __tablename__ = "tarifa_maquina_proyecto"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(Integer, ForeignKey("proyecto.id", ondelete="CASCADE"), nullable=False)
    maquina_id = Column(Integer, ForeignKey("maquina.id", ondelete="CASCADE"), nullable=False)
    tarifa_hora = Column(Float, nullable=False)

    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())

    proyecto = relationship("Proyecto")
    maquina = relationship("Maquina")

    __table_args__ = (
        UniqueConstraint("proyecto_id", "maquina_id", name="uq_tarifa_maquina_proyecto"),
    )
