from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, Numeric, Text
from sqlalchemy.orm import relationship
from app.db.database import Base
from sqlalchemy.sql import func

class ReporteCuentaCorriente(Base):
    __tablename__ = "reportes_cuenta_corriente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    proyecto_id = Column(Integer, ForeignKey("proyecto.id"), nullable=False)
    periodo_inicio = Column(Date, nullable=False)
    periodo_fin = Column(Date, nullable=False)
    total_aridos = Column(Float, default=0.0)  # Total m³ de áridos entregados
    total_horas = Column(Float, default=0.0)  # Total horas de máquinas
    importe_aridos = Column(Numeric(12, 2), default=0.0)  # Importe total de áridos
    importe_horas = Column(Numeric(12, 2), default=0.0)  # Importe total de horas de máquinas
    importe_total = Column(Numeric(12, 2), default=0.0)  # Importe total del reporte
    estado = Column(String(20), default="pendiente")  # "pendiente", "parcial" o "pagado"
    fecha_generacion = Column(DateTime, nullable=False)

    # Campos adicionales opcionales
    observaciones = Column(Text, nullable=True)  # Notas u observaciones del reporte
    numero_factura = Column(String(50), nullable=True)  # Número de factura asociado
    fecha_pago = Column(Date, nullable=True)  # Fecha en que fue pagado

    # Relaciones
    proyecto = relationship("Proyecto", back_populates="reportes_cuenta_corriente")
    items_aridos_rel = relationship("ReporteItemArido", back_populates="reporte", cascade="all, delete-orphan")
    items_horas_rel = relationship("ReporteItemHora", back_populates="reporte", cascade="all, delete-orphan")

    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())
