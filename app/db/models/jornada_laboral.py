from sqlalchemy import Column, Integer, String, DateTime, Date, Float, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from app.db.database import Base

class JornadaLaboral(Base):
    __tablename__ = "jornada_laboral"
    
    # Campos principales
    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    fecha = Column(Date, nullable=False)
    
    # Control de tiempo
    hora_inicio = Column(DateTime, nullable=False)
    hora_fin = Column(DateTime, nullable=True)  # NULL mientras está activa
    tiempo_descanso = Column(Integer, default=0)  # minutos
    
    # Cálculo de horas - MANEJO COMPLETO DE HORAS EXTRAS
    horas_regulares = Column(Float, default=0.0)  # Máximo 9 horas
    horas_extras = Column(Float, default=0.0)     # Máximo 4 horas adicionales
    total_horas = Column(Float, default=0.0)      # Total trabajado
    
    # Estado y control de jornada
    estado = Column(String(20), default='activa')  # activa, pausada, completada, cancelada
    es_feriado = Column(Boolean, default=False)
    
    # CONTROL ESPECÍFICO DE HORAS EXTRAS
    limite_regular_alcanzado = Column(Boolean, default=False)  # ¿Se alcanzaron las 9h?
    hora_limite_regular = Column(DateTime, nullable=True)      # Momento exacto de las 9h
    overtime_solicitado = Column(Boolean, default=False)       # ¿Se mostró el diálogo?
    overtime_confirmado = Column(Boolean, default=False)       # ¿El usuario confirmó extras?
    overtime_iniciado = Column(DateTime, nullable=True)        # Momento de inicio de extras
    pausa_automatica = Column(Boolean, default=False)         # ¿Se pausó automáticamente?
    finalizacion_forzosa = Column(Boolean, default=False)     # ¿Se finalizó forzosamente?
    
    # Información adicional
    notas_inicio = Column(Text, nullable=True)
    notas_fin = Column(Text, nullable=True)
    motivo_finalizacion = Column(String(100), nullable=True)  # razón de finalización
    
    # Geolocalización (opcional)
    ubicacion_inicio = Column(Text, nullable=True)  # JSON string con lat/lng
    ubicacion_fin = Column(Text, nullable=True)
    
    # Control de advertencias
    advertencia_8h_mostrada = Column(Boolean, default=False)  # ¿Se mostró advertencia a las 8h?
    advertencia_limite_mostrada = Column(Boolean, default=False)  # ¿Se mostró advertencia de límite?
    
    # Campos de auditoría
    created = Column(DateTime(timezone=True), server_default=func.now())
    updated = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="jornadas_laborales")
    
    def __repr__(self):
        return f"<JornadaLaboral(id={self.id}, usuario_id={self.usuario_id}, fecha={self.fecha}, estado={self.estado})>"
    
    # MÉTODOS DE UTILIDAD PARA EL CÁLCULO DE HORAS
    
    @property
    def is_active(self):
        """Verifica si la jornada está activa"""
        return self.estado == 'activa' and self.hora_fin is None
    
    @property
    def is_paused(self):
        """Verifica si la jornada está pausada"""
        return self.estado == 'pausada'
    
    @property
    def is_in_overtime(self):
        """Verifica si está en modo horas extras"""
        return self.overtime_confirmado and self.overtime_iniciado is not None
    
    @property
    def tiempo_transcurrido_minutos(self):
        """Calcula tiempo transcurrido en minutos"""
        if not self.hora_inicio:
            return 0
        
        fin = self.hora_fin or func.now()
        delta = fin - self.hora_inicio
        return int(delta.total_seconds() / 60)
    
    @property
    def tiempo_trabajado_minutos(self):
        """Tiempo trabajado descontando descansos"""
        return max(0, self.tiempo_transcurrido_minutos - self.tiempo_descanso)
    
    @property
    def puede_iniciar_overtime(self):
        """Verifica si puede iniciar horas extras"""
        return (self.limite_regular_alcanzado and 
                not self.overtime_confirmado and 
                self.horas_extras < 4.0)
    
    @property
    def debe_finalizar_automaticamente(self):
        """Verifica si debe finalizar automáticamente"""
        return self.total_horas >= 13.0  # 9h regulares + 4h extras
    
    def calcular_horas(self):
        """Calcula y actualiza las horas trabajadas"""
        if not self.hora_inicio:
            return
        
        # Tiempo total trabajado en horas (descontando descansos)
        tiempo_trabajado_horas = self.tiempo_trabajado_minutos / 60.0
        
        # Separar horas regulares y extras
        if tiempo_trabajado_horas <= 9.0:
            self.horas_regulares = tiempo_trabajado_horas
            self.horas_extras = 0.0
        else:
            self.horas_regulares = 9.0
            self.horas_extras = min(4.0, tiempo_trabajado_horas - 9.0)
        
        self.total_horas = self.horas_regulares + self.horas_extras
        
        # Actualizar estado de límite regular
        if self.horas_regulares >= 9.0 and not self.limite_regular_alcanzado:
            self.limite_regular_alcanzado = True
            if not self.hora_limite_regular:
                # Calcular el momento exacto de las 9 horas
                from datetime import timedelta
                self.hora_limite_regular = self.hora_inicio + timedelta(hours=9, minutes=self.tiempo_descanso)
    
    def pausar_por_limite(self):
        """Pausa la jornada al alcanzar las 9 horas"""
        self.estado = 'pausada'
        self.pausa_automatica = True
        self.calcular_horas()
    
    def reanudar_con_overtime(self, notas_overtime=None):
        """Reanuda la jornada para horas extras"""
        self.estado = 'activa'
        self.overtime_confirmado = True
        self.overtime_iniciado = func.now()
        if notas_overtime:
            self.notas_fin = (self.notas_fin or '') + f' | Overtime: {notas_overtime}'
    
    def finalizar_jornada(self, hora_fin=None, notas_fin=None, motivo=None):
        """Finaliza la jornada laboral"""
        self.hora_fin = hora_fin or func.now()
        self.estado = 'completada'
        if notas_fin:
            self.notas_fin = notas_fin
        if motivo:
            self.motivo_finalizacion = motivo
        self.calcular_horas()
    
    def finalizar_forzosamente(self, motivo="Finalización forzosa"):
        """Finaliza la jornada forzosamente"""
        self.finalizacion_forzosa = True
        self.finalizar_jornada(motivo=motivo)
    
    def to_dict(self):
        """Convierte el objeto a diccionario para JSON"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'hora_inicio': self.hora_inicio.isoformat() if self.hora_inicio else None,
            'hora_fin': self.hora_fin.isoformat() if self.hora_fin else None,
            'tiempo_descanso': self.tiempo_descanso,
            'horas_regulares': self.horas_regulares,
            'horas_extras': self.horas_extras,
            'total_horas': self.total_horas,
            'estado': self.estado,
            'es_feriado': self.es_feriado,
            'limite_regular_alcanzado': self.limite_regular_alcanzado,
            'overtime_confirmado': self.overtime_confirmado,
            'is_active': self.is_active,
            'is_in_overtime': self.is_in_overtime,
            'puede_iniciar_overtime': self.puede_iniciar_overtime,
            'notas_inicio': self.notas_inicio,
            'notas_fin': self.notas_fin,
            'motivo_finalizacion': self.motivo_finalizacion,
            'created': self.created.isoformat() if self.created else None,
            'updated': self.updated.isoformat() if self.updated else None
        }