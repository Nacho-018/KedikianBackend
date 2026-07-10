from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class PrecioAridoProyecto(Base):
    __tablename__ = "precio_arido_proyecto"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(Integer, ForeignKey("proyecto.id", ondelete="CASCADE"), nullable=False)
    tipo_arido = Column(String(100), nullable=False)
    precio_unitario = Column(Float, nullable=False)

    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())

    proyecto = relationship("Proyecto")

    __table_args__ = (
        UniqueConstraint("proyecto_id", "tipo_arido", name="uq_precio_arido_proyecto"),
    )
