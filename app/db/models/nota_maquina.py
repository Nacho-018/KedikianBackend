from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from app.db.database import Base
from sqlalchemy.sql import func

class NotaMaquina(Base):
    __tablename__ = "notas_maquinas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    maquina_id = Column(Integer, ForeignKey("maquina.id", ondelete="CASCADE"), nullable=False)
    texto = Column(Text, nullable=False)
    usuario = Column(String(100), default='Usuario')
    fecha = Column(DateTime(timezone=True), nullable=False)

    # Relaciones
    maquina = relationship("Maquina", back_populates="notas")

    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())

    # Índices
    __table_args__ = (
        Index('idx_notas_maquina_id', 'maquina_id'),
        Index('idx_notas_fecha', 'fecha'),
    )
