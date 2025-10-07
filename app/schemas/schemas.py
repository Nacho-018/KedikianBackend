from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date
from typing import List, Optional, Union, Dict, Any

# Mantenimiento
class MantenimientoBase(BaseModel):
    maquina_id: int
    tipo_mantenimiento: str
    descripcion: str
    fecha_mantenimiento: datetime
    horas_maquina: int
    costo: Optional[float] = None
    responsable: Optional[str] = None
    observaciones: Optional[str] = None

class MantenimientoCreate(MantenimientoBase):
    pass

class MantenimientoSchema(MantenimientoBase):
    id: Optional[int] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        from_attributes = True

class MantenimientoOut(MantenimientoBase):
    id: Optional[int] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        from_attributes = True

# Usuario
class UsuarioBase(BaseModel):
    nombre: str
    email: EmailStr
    estado: bool
    roles: List[str]

class UsuarioCreate(UsuarioBase):
    hash_contrasena: str
    fecha_creacion: Optional[datetime] = None

class UsuarioSchema(UsuarioBase):
    id: Optional[int] = None
    hash_contrasena: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class UsuarioOut(UsuarioBase):
    id: Optional[int] = None
    hash_contrasena: Union[str, None] = ''
    fecha_creacion: datetime

    class Config:
        from_attributes = True

# Arrendamiento
class ArrendamientoBase(BaseModel):
    proyecto_id: Optional[int] = None
    maquina_id: Optional[int] = None
    horas_uso: int
    fecha_asignacion: datetime

class ArrendamientoCreate(ArrendamientoBase):
    pass

class ArrendamientoSchema(ArrendamientoBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

class ArrendamientoOut(ArrendamientoBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

# Contrato
class ContratoBase(BaseModel):
    proyecto_id: Optional[int] = None
    detalle: str
    cliente: str
    importe_total: int
    fecha_inicio: datetime
    fecha_terminacion: datetime

class ContratoCreate(ContratoBase):
    pass

class ContratoSchema(ContratoBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

class ContratoOut(ContratoBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

# Gasto
class GastoBase(BaseModel):
    usuario_id: int
    maquina_id: Optional[int] = None
    tipo: str
    importe_total: float
    fecha: datetime
    descripcion: str
    imagen: Optional[str] = None

class GastoCreate(GastoBase):
    pass

class GastoSchema(GastoBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

class GastoOut(GastoBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

# Maquina
class MaquinaBase(BaseModel):
    nombre: str
    horas_uso: int = 0

class MaquinaCreate(MaquinaBase):
    pass

class MaquinaSchema(BaseModel):
    id: Optional[int] = None
    nombre: str
    horas_uso: int = 0
    horas_maquina: int = 0

    class Config:
        from_attributes = True

class MaquinaOut(BaseModel):
    id: int
    nombre: str
    horas_uso: int = 0
    horas_maquina: int = 0
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        from_attributes = True

# MovimientoInventario
class MovimientoInventarioBase(BaseModel):
    producto_id: Optional[int] = None
    usuario_id: Optional[int] = None
    cantidad: int
    fecha: datetime
    tipo_transaccion: str  # "entrada" o "salida"

class MovimientoInventarioCreate(MovimientoInventarioBase):
    pass

class MovimientoInventarioSchema(MovimientoInventarioBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

class MovimientoInventarioOut(MovimientoInventarioBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

# Pago
class PagoBase(BaseModel):
    proyecto_id: Optional[int] = None
    importe_total: int
    fecha: datetime
    descripcion: str

class PagoCreate(PagoBase):
    pass

class PagoSchema(PagoBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

class PagoOut(PagoBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

# Producto
class ProductoBase(BaseModel):
    nombre: str
    codigo_producto: str
    inventario: int
    url_imagen: Optional[str] = None

class ProductoCreate(ProductoBase):
    pass

class ProductoSchema(ProductoBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

class ProductoOut(ProductoBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

# Proyecto
class ProyectoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    estado: bool
    fecha_creacion: Optional[datetime] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    progreso: Optional[int] = 0
    gerente: Optional[str] = None
    contrato_id: Optional[int] = None
    ubicacion: str

class ProyectoCreate(ProyectoBase):
    pass

class ProyectoSchema(ProyectoBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

class ProyectoOut(ProyectoBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

# ReporteLaboral
class ReporteLaboralBase(BaseModel):
    maquina_id: int
    usuario_id: int
    proyecto_id: Optional[int] = Field(None, description="ID del proyecto asignado")  # ← Field para forzar inclusión
    fecha_asignacion: datetime
    horas_turno: int
    horometro_inicial: Optional[float] = Field(None, description="Lectura inicial del horómetro")

class ReporteLaboralCreate(ReporteLaboralBase):
    pass

class ReporteLaboralSchema(ReporteLaboralBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

class ReporteLaboralOut(ReporteLaboralBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True
        # ✅ SOLUCIÓN PRINCIPAL: Incluir campos None en la serialización JSON
        validate_assignment = True

    # ✅ SOLUCIÓN: Sobrescribir dict() para incluir campos None
    def dict(self, **kwargs):
        """Forzar inclusión de todos los campos, incluso si son None"""
        kwargs.setdefault('exclude_none', False)  # No excluir campos None
        return super().dict(**kwargs)
    
    # ✅ ALTERNATIVA: Sobrescribir model_dump para Pydantic v2 (si usas v2)
    def model_dump(self, **kwargs):
        """Forzar inclusión de todos los campos para Pydantic v2"""
        kwargs.setdefault('exclude_none', False)
        return super().model_dump(**kwargs)

# ✅ CLASE ALTERNATIVA: Si las anteriores no funcionan, usa esta
class ReporteLaboralAPIResponse(BaseModel):
    """Clase específica para respuestas de API que garantiza incluir todos los campos"""
    id: Optional[int] = None
    maquina_id: Optional[int] = None
    usuario_id: Optional[int] = None
    proyecto_id: Optional[int] = None  # ← Siempre incluido
    fecha_asignacion: datetime
    horas_turno: int

    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm_manual(cls, orm_obj):
        """Método manual para asegurar que todos los campos se incluyan"""
        return cls(
            id=orm_obj.id,
            maquina_id=orm_obj.maquina_id,
            usuario_id=orm_obj.usuario_id,
            proyecto_id=orm_obj.proyecto_id,  # ← Incluir explícitamente
            fecha_asignacion=orm_obj.fecha_asignacion,
            horas_turno=orm_obj.horas_turno
        )


class ConfiguracionTarifasBase(BaseModel):
    hora_normal: float
    hora_feriado: float
    multiplicador_extra: float

class ConfiguracionTarifasCreate(ConfiguracionTarifasBase):
    pass

class ConfiguracionTarifasResponse(ConfiguracionTarifasBase):
    id: int
    activo: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class OperarioExcel(BaseModel):
    nombre: str
    dni: str
    horas_normales: float
    horas_feriado: float
    horas_extras: float
    precio_hora_normal: float
    precio_hora_feriado: float
    precio_hora_extra: float
    total_calculado: float

class RegistroHorasBase(BaseModel):
    operario_id: int
    periodo: str
    horas_normales: float = 0
    horas_feriado: float = 0
    horas_extras: float = 0

class RegistroHorasCreate(RegistroHorasBase):
    pass

class RegistroHorasUpdate(BaseModel):
    horas_normales: Optional[float] = None
    horas_feriado: Optional[float] = None
    horas_extras: Optional[float] = None

class RegistroHorasResponse(RegistroHorasBase):
    id: int
    total_calculado: float
    created_at: datetime
    updated_at: datetime
    operario: UsuarioSchema
    
    class Config:
        from_attributes = True

class ResumenExcelRequest(BaseModel):
    periodo: str
    operarios: List[OperarioExcel]

class ResumenExcelResponse(BaseModel):
    periodo: str
    total_horas_normales: float
    total_horas_feriado: float
    total_horas_extras: float
    basico_remunerativo: float
    asistencia_perfecta_remunerativo: float
    feriado_remunerativo: float
    extras_remunerativo: float
    total_remunerativo: float

# Excel Import/Export
class OperarioExcel(BaseModel):
    nombre: str
    dni: str
    horasNormales: float
    horasFeriado: float
    horasExtras: float
    precioHoraNormal: float
    precioHoraFeriado: float
    precioHoraExtra: float
    totalCalculado: float

class ConfiguracionTarifasExcel(BaseModel):
    horaNormal: float
    horaFeriado: float
    horaExtra: float
    multiplicadorExtra: float

class ExcelImportRequest(BaseModel):
    operarios: List[OperarioExcel]
    configuracion: ConfiguracionTarifasExcel

class ExcelImportResponse(BaseModel):
    message: str
    resumen: Optional[dict] = None

class OperarioCreateFromExcel(BaseModel):
    nombre: str
    dni: str
    email: Optional[str] = None
    estado: bool = True
    roles: List[str] = ["operario"]
    hash_contrasena: str = "default_password_hash"  # Contraseña por defecto

class OperarioCreateFromExcelFlexible(BaseModel):
    nombre: Optional[str] = None
    dni: Optional[str] = None
    email: Optional[str] = None
    estado: Optional[bool] = True
    roles: Optional[List[str]] = ["operario"]
    hash_contrasena: Optional[str] = "default_password_hash"
    
    # Campos alternativos que el frontend podría enviar
    horasNormales: Optional[float] = None
    horasFeriado: Optional[float] = None
    horasExtras: Optional[float] = None
    precioHoraNormal: Optional[float] = None
    precioHoraFeriado: Optional[float] = None
    precioHoraExtra: Optional[float] = None
    totalCalculado: Optional[float] = None

# EntregaArido
class EntregaAridoBase(BaseModel):
    proyecto_id: int
    usuario_id: int
    tipo_arido: str
    nombre: Optional[str] = None
    cantidad: int
    fecha_entrega: datetime

class EntregaAridoCreate(EntregaAridoBase):
    pass

class EntregaAridoSchema(EntregaAridoBase):
    id: Optional[int] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        from_attributes = True

class EntregaAridoOut(EntregaAridoBase):
    id: Optional[int] = None
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        from_attributes = True

class ResumenSueldoCreate(BaseModel):
    nombre: str
    dni: str
    periodo: str
    total_horas_normales: float = 0
    total_horas_feriado: float = 0
    total_horas_extras: float = 0
    basico_remunerativo: float = 0
    asistencia_perfecta_remunerativo: float = 0
    feriado_remunerativo: float = 0
    extras_remunerativo: float = 0
    total_remunerativo: float = 0
    observaciones: Optional[str] = None

class ResumenSueldoResponse(ResumenSueldoCreate):
    id: int
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        from_attributes = True

# Esquemas para endpoints de máquinas
class RegistroHorasMaquinaCreate(BaseModel):
    horas: int
    fecha: Union[datetime, str]  # Aceptar tanto datetime como string
    descripcion: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class HistorialProyectoOut(BaseModel):
    proyecto_id: int
    proyecto_nombre: str
    fecha_asignacion: datetime
    fecha_retiro: Optional[datetime] = None
    total_horas: int
    estado: str  # "activo" o "finalizado"

    class Config:
        from_attributes = True

class HistorialHorasOut(BaseModel):
    """Schema para registros individuales de horas trabajadas"""
    id: int
    maquina_id: int
    proyecto_id: Optional[int] = None
    horas_trabajadas: int  # mapea desde horas_turno
    fecha: datetime  # mapea desde fecha_asignacion
    usuario_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class EstadisticasHorasOut(BaseModel):
    """Schema para estadísticas de horas de una máquina"""
    total_horas: float
    total_registros: int
    promedio_horas: float
    fecha_primer_registro: Optional[datetime] = None
    fecha_ultimo_registro: Optional[datetime] = None

    class Config:
        from_attributes = True
        
class CambiarProyectoRequest(BaseModel):
    nuevo_proyecto_id: int
    fecha_cambio: datetime
    motivo: Optional[str] = None

class CambiarProyectoResponse(BaseModel):
    maquina_id: int
    proyecto_anterior_id: Optional[int] = None
    proyecto_nuevo_id: int
    fecha_cambio: datetime
    mensaje: str

    class Config:
        from_attributes = True

class JornadaLaboralBase(BaseModel):
    usuario_id: int
    fecha: date
    hora_inicio: datetime
    tiempo_descanso: int = Field(default=0, description="Tiempo de descanso en minutos")
    es_feriado: bool = Field(default=False)
    notas_inicio: Optional[str] = None
    notas_fin: Optional[str] = None
    ubicacion_inicio: Optional[str] = None
    ubicacion_fin: Optional[str] = None

class JornadaLaboralCreate(BaseModel):
    usuario_id: int
    notas_inicio: Optional[str] = None
    ubicacion: Optional[Dict[str, Any]] = None

class JornadaLaboralUpdate(BaseModel):
    tiempo_descanso: Optional[int] = None
    notas_fin: Optional[str] = None
    ubicacion_fin: Optional[Dict[str, Any]] = None
    estado: Optional[str] = None

class JornadaLaboralResponse(BaseModel):
    id: int
    usuario_id: int
    fecha: date
    hora_inicio: datetime
    hora_fin: Optional[datetime] = None
    tiempo_descanso: int
    
    # Cálculo de horas
    horas_regulares: float
    horas_extras: float
    total_horas: float
    
    # Estado y control
    estado: str  # activa, pausada, completada, cancelada
    es_feriado: bool
    
    # Control de horas extras
    limite_regular_alcanzado: bool
    hora_limite_regular: Optional[datetime] = None
    overtime_solicitado: bool
    overtime_confirmado: bool
    overtime_iniciado: Optional[datetime] = None
    pausa_automatica: bool
    finalizacion_forzosa: bool
    
    # Información adicional
    notas_inicio: Optional[str] = None
    notas_fin: Optional[str] = None
    motivo_finalizacion: Optional[str] = None
    ubicacion_inicio: Optional[str] = None
    ubicacion_fin: Optional[str] = None
    
    # Control de advertencias
    advertencia_8h_mostrada: bool
    advertencia_limite_mostrada: bool
    
    # Timestamps
    created: datetime
    updated: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_orm(cls, orm_obj):
        """Método personalizado para manejar la conversión desde el ORM"""
        return cls(
            id=orm_obj.id,
            usuario_id=orm_obj.usuario_id,
            fecha=orm_obj.fecha,
            hora_inicio=orm_obj.hora_inicio,
            hora_fin=orm_obj.hora_fin,
            tiempo_descanso=orm_obj.tiempo_descanso,
            horas_regulares=orm_obj.horas_regulares or 0.0,
            horas_extras=orm_obj.horas_extras or 0.0,
            total_horas=orm_obj.total_horas or 0.0,
            estado=orm_obj.estado,
            es_feriado=orm_obj.es_feriado or False,
            limite_regular_alcanzado=orm_obj.limite_regular_alcanzado or False,
            hora_limite_regular=orm_obj.hora_limite_regular,
            overtime_solicitado=orm_obj.overtime_solicitado or False,
            overtime_confirmado=orm_obj.overtime_confirmado or False,
            overtime_iniciado=orm_obj.overtime_iniciado,
            pausa_automatica=orm_obj.pausa_automatica or False,
            finalizacion_forzosa=orm_obj.finalizacion_forzosa or False,
            notas_inicio=orm_obj.notas_inicio,
            notas_fin=orm_obj.notas_fin,
            motivo_finalizacion=orm_obj.motivo_finalizacion,
            ubicacion_inicio=orm_obj.ubicacion_inicio,
            ubicacion_fin=orm_obj.ubicacion_fin,
            advertencia_8h_mostrada=orm_obj.advertencia_8h_mostrada or False,
            advertencia_limite_mostrada=orm_obj.advertencia_limite_mostrada or False,
            created=orm_obj.created,
            updated=orm_obj.updated
        )

class EstadisticasJornadaResponse(BaseModel):
    mes: int
    año: int
    total_jornadas: int
    total_horas_regulares: float
    total_horas_extras: float
    total_horas: float
    jornadas_con_extras: int
    promedio_horas_dia: float
    jornadas: List[Dict[str, Any]]

class TiempoRestanteResponse(BaseModel):
    tiempo_hasta_advertencia: int  # minutos
    tiempo_hasta_limite_regular: int  # minutos
    tiempo_hasta_limite_maximo: int  # minutos
    en_overtime: bool
    horas_trabajadas: float

class ResumenDiaResponse(BaseModel):
    fecha: str
    tiene_jornadas: bool
    jornada_id: Optional[int] = None
    estado: Optional[str] = None
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None
    total_horas: float
    horas_regulares: float
    horas_extras: float
    es_feriado: bool
    en_overtime: bool

# ============= SCHEMAS PARA TRABAJO (NO JORNADA) =============
# Estos son para machine-hours, que SÍ deben usar reporte_laboral

class TrabajoMaquinaCreate(BaseModel):
    """Para crear registros de trabajo con máquinas"""
    maquina_id: int
    proyecto_id: Optional[int] = None
    horas_turno: int  # Horas trabajadas con la máquina
    fecha_asignacion: datetime
    notas: Optional[str] = None

class TrabajoMaquinaResponse(BaseModel):
    """Para respuestas de trabajos con máquinas"""
    id: int
    maquina_id: int
    usuario_id: int
    proyecto_id: Optional[int] = None
    fecha_asignacion: datetime
    horas_turno: int
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    
    class Config:
        from_attributes = True