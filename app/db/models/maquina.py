# app/db/models.py
class Maquina(Base):
    __tablename__ = "maquina"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50))
    horas_uso = Column(Integer, default=0)
    horas_maquina = Column(Integer, default=0)
    horometro_inicial = Column(Float, default=0)  # ✅ AGREGAR ESTA LÍNEA

    # Relaciones
    reportes_laborales = relationship("ReporteLaboral", back_populates="maquina")
    gastos = relationship("Gasto", back_populates="maquina")
    arrendamientos = relationship("Arrendamiento", back_populates="maquina")
    mantenimientos = relationship("Mantenimiento", back_populates="maquina")
    
    # Timestamps
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())