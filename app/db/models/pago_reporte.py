from sqlalchemy import Column, Integer, Numeric, Date, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from sqlalchemy.sql import func

class PagoReporte(Base):
    __tablename__ = "pagos_reportes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reporte_id = Column(Integer, ForeignKey("reportes_cuenta_corriente.id", ondelete="CASCADE"), nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    fecha = Column(Date, nullable=False)
    observaciones = Column(Text, nullable=True)
    fecha_registro = Column(DateTime, server_default=func.now())

    # Relación con el reporte
    reporte = relationship("ReporteCuentaCorriente", back_populates="pagos")
