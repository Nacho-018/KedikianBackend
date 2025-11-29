from sqlalchemy import Column, Integer, DateTime, Float, TIMESTAMP
from sqlalchemy.sql import func
from app.db.database import Base

class ConfiguracionTarifas(Base):
    __tablename__ = "configuracion_tarifas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hora_normal = Column(Float, nullable=False)
    hora_feriado = Column(Float, nullable=False)
    hora_extra = Column(Float, nullable=False)
    multiplicador_extra = Column(Float, nullable=False)
    fecha_actualizacion = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())