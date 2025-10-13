from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date, BigInteger
from sqlalchemy.orm import relationship
from app.db.database import Base
from sqlalchemy.sql import func

class Proyecto(Base):
    __tablename__ = "proyecto"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(75))
    descripcion = Column(String(500), nullable=True)
    estado = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime)
    fecha_inicio = Column(Date, nullable=True)
    fecha_fin = Column(Date, nullable=True)
    progreso = Column(Integer, default=0)
    gerente = Column(String(100), nullable=True)
    contrato_id = Column(Integer, ForeignKey("contrato.id"), unique=True, nullable=True)
    ubicacion = Column(String(50))
    
    # Campos para manejo de archivos de contrato
    contrato_file_path = Column(String(500), nullable=True)  # Ruta física del archivo
    contrato_url = Column(String(500), nullable=True)  # URL pública del contrato (opcional)
    contrato_nombre = Column(String(255), nullable=True)  # Nombre original del archivo
    contrato_tipo = Column(String(100), nullable=True)  # Tipo MIME del archivo

    # Relaciones
    contrato = relationship("Contrato", back_populates="proyecto")
    contrato_archivos = relationship("ContratoArchivo", back_populates="proyecto", cascade="all, delete-orphan")
    arrendamientos = relationship("Arrendamiento", back_populates="proyecto")
    pagos = relationship("Pago", back_populates="proyecto")
    entrega_arido = relationship("EntregaArido", back_populates="proyecto")
    reportes_laborales = relationship("ReporteLaboral", back_populates="proyecto")
    
    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())


