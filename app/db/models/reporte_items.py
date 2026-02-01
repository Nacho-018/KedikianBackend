from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class ReporteItemArido(Base):
    """
    Tabla relacional que vincula un reporte de cuenta corriente con una entrega de árido específica.
    Permite rastrear exactamente qué entregas de áridos pertenecen a cada reporte.
    """
    __tablename__ = "reporte_items_aridos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reporte_id = Column(Integer, ForeignKey("reportes_cuenta_corriente.id", ondelete="CASCADE"), nullable=False)
    entrega_arido_id = Column(Integer, ForeignKey("entrega_arido.id", ondelete="CASCADE"), nullable=False)

    # Relaciones
    reporte = relationship("ReporteCuentaCorriente", back_populates="items_aridos_rel")
    entrega_arido = relationship("EntregaArido")


class ReporteItemHora(Base):
    """
    Tabla relacional que vincula un reporte de cuenta corriente con un reporte laboral específico.
    Permite rastrear exactamente qué reportes de horas pertenecen a cada reporte.
    """
    __tablename__ = "reporte_items_horas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reporte_id = Column(Integer, ForeignKey("reportes_cuenta_corriente.id", ondelete="CASCADE"), nullable=False)
    reporte_laboral_id = Column(Integer, ForeignKey("reporte_laboral.id", ondelete="CASCADE"), nullable=False)

    # Relaciones
    reporte = relationship("ReporteCuentaCorriente", back_populates="items_horas_rel")
    reporte_laboral = relationship("ReporteLaboral")
