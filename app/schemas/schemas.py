from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime, date
from typing import List, Optional, Union, Dict, Any
import base64
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

# NotaMaquina
class NotaMaquinaBase(BaseModel):
    texto: str = Field(..., min_length=3, description="Contenido de la nota")

class NotaMaquinaCreate(NotaMaquinaBase):
    pass

class NotaMaquinaOut(NotaMaquinaBase):
    id: int
    maquina_id: int
    usuario: str
    fecha: datetime

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

class UsuarioUpdate(BaseModel):
    """Schema para actualizar usuarios - todos los campos opcionales"""
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    hash_contrasena: Optional[str] = None  # ← Opcional para actualización
    estado: Optional[bool] = None
    roles: Optional[List[str]] = None
    fecha_creacion: Optional[datetime] = None

    class Config:
        from_attributes = True

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

class GastoCreate(GastoBase):
    imagen: Optional[bytes] = None
    
    class Config:
        arbitrary_types_allowed = True

class GastoSchema(GastoBase):
    id: Optional[int] = None
    imagen: Optional[str] = None  # Base64 string para respuestas
    
    @field_validator('imagen', mode='before')
    @classmethod
    def convert_bytes_to_base64(cls, v):
        """Convierte bytes a base64 string para la respuesta"""
        if v is None:
            return None
        if isinstance(v, bytes):
            return base64.b64encode(v).decode('utf-8')
        return v

    class Config:
        from_attributes = True

class GastoOut(GastoBase):
    id: Optional[int] = None
    imagen: Optional[str] = None
    
    @field_validator('imagen', mode='before')
    @classmethod
    def convert_bytes_to_base64(cls, v):
        if v is None:
            return None
        if isinstance(v, bytes):
            return base64.b64encode(v).decode('utf-8')
        return v

    class Config:
        from_attributes = True

# Maquina
class MaquinaBase(BaseModel):
    nombre: str
    horas_uso: int = 0
    horometro_inicial: Optional[float] = 0
    proximo_mantenimiento: Optional[float] = None  # ✅ Horas para próximo mantenimiento

class MaquinaCreate(MaquinaBase):
    pass

class MaquinaSchema(BaseModel):
    id: Optional[int] = None
    nombre: str
    horas_uso: int = 0
    horas_maquina: int = 0
    horometro_inicial: Optional[float] = 0
    proximo_mantenimiento: Optional[float] = None  # ✅ Horas para próximo mantenimiento

    class Config:
        from_attributes = True

class MaquinaOut(BaseModel):
    id: int
    nombre: str
    horas_uso: int = 0
    horas_maquina: int = 0
    horometro_inicial: Optional[float] = 0
    proximo_mantenimiento: Optional[float] = None  # ✅ Horas para próximo mantenimiento
    horas_restantes: Optional[float] = None  # ✅ Campo calculado
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    @property
    def _horas_restantes_calculadas(self) -> Optional[float]:
        """Calcula horas restantes: horometro_inicial - proximo_mantenimiento"""
        if self.horometro_inicial is not None and self.proximo_mantenimiento is not None:
            return float(self.horometro_inicial) - float(self.proximo_mantenimiento)
        return None

    def __init__(self, **data):
        super().__init__(**data)
        # Si no viene horas_restantes, calcularlo automáticamente
        if self.horas_restantes is None:
            self.horas_restantes = self._horas_restantes_calculadas

    class Config:
        from_attributes = True

class ProximoMantenimientoUpdate(BaseModel):
    horas: Optional[float] = Field(None, description="Horas para próximo mantenimiento (null para resetear a cálculo automático)")

    @field_validator('horas')
    @classmethod
    def validate_horas(cls, v):
        """Validar que las horas sean positivas si no son None"""
        if v is not None and v <= 0:
            raise ValueError("Las horas deben ser un número positivo mayor a 0")
        return v

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

# ContratoArchivo
class ContratoArchivoBase(BaseModel):
    proyecto_id: int
    nombre_archivo: str
    ruta_archivo: str
    tipo_archivo: str
    tamaño_archivo: int
    fecha_subida: Optional[datetime] = None

class ContratoArchivoCreate(ContratoArchivoBase):
    pass

class ContratoArchivoResponse(ContratoArchivoBase):
    id: int
    
    class Config:
        from_attributes = True

# Proyecto
# ... (todo tu código anterior permanece igual hasta ProyectoBase)

# Proyecto - ACTUALIZADO
class ProyectoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    estado: bool = True
    fecha_creacion: Optional[datetime] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    progreso: Optional[int] = 0
    gerente: Optional[str] = None
    contrato_id: Optional[int] = None
    ubicacion: str
    # NUEVOS CAMPOS para manejo de archivos
    contrato_url: Optional[str] = None  # URL pública del contrato
    contrato_nombre: Optional[str] = None  # Nombre del archivo
    contrato_tipo: Optional[str] = None  # Tipo MIME

class ProyectoCreate(ProyectoBase):
    pass

class ProyectoUpdate(BaseModel):
    """Schema para actualizar proyectos - todos los campos opcionales"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    estado: Optional[bool] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    progreso: Optional[int] = None
    gerente: Optional[str] = None
    contrato_id: Optional[int] = None
    ubicacion: Optional[str] = None
    
class ProyectoSchema(ProyectoBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

class ProyectoResponse(ProyectoBase):
    id: int
    fecha_creacion: datetime
    contrato_archivos: Optional[List[ContratoArchivoResponse]] = None
    # Campos adicionales para el frontend
    contrato_url: Optional[str] = None
    contrato_nombre: Optional[str] = None
    contrato_tipo: Optional[str] = None
    
    class Config:
        from_attributes = True

class ProyectoOut(ProyectoBase):
    id: Optional[int] = None
    contrato_url: Optional[str] = None
    contrato_nombre: Optional[str] = None
    contrato_tipo: Optional[str] = None

    class Config:
        from_attributes = True

# ReporteLaboral
class ReporteLaboralBase(BaseModel):
    maquina_id: int
    usuario_id: Optional[int] = None
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
    horaNormal: float
    horaFeriado: float
    horaExtra: float
    multiplicadorExtra: float = 1.5

class ConfiguracionTarifasCreate(ConfiguracionTarifasBase):
    """Schema para crear/actualizar configuración de tarifas"""
    pass

class ConfiguracionTarifasResponse(BaseModel):
    """Schema para respuesta de configuración de tarifas"""
    horaNormal: float
    horaFeriado: float
    horaExtra: float
    multiplicadorExtra: float

    class Config:
        from_attributes = True
        populate_by_name = True

    @classmethod
    def from_orm(cls, orm_obj):
        """Convierte el objeto ORM a camelCase para la respuesta"""
        return cls(
            horaNormal=orm_obj.hora_normal,
            horaFeriado=orm_obj.hora_feriado,
            horaExtra=orm_obj.hora_extra,
            multiplicadorExtra=orm_obj.multiplicador_extra
        )

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
    observaciones: Optional[str] = None

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

class JornadaLaboralCreateManual(BaseModel):
    """Schema para crear jornadas laborales manualmente con todos los campos"""
    usuario_id: int
    fecha: str  # formato: "2025-11-23"
    hora_inicio: str  # formato: "2025-11-23T08:00:00"
    hora_fin: Optional[str] = None  # formato: "2025-11-23T18:00:00" o null
    tiempo_descanso: int = Field(default=60, ge=0, description="Tiempo de descanso en minutos (>= 0)")
    es_feriado: bool = Field(default=False, description="Indica si es un día feriado")
    estado: str = Field(default="activa", description="Estado de la jornada: activa, completada, pausada, cancelada")
    notas_inicio: Optional[str] = None
    notas_fin: Optional[str] = None

    @field_validator('estado')
    @classmethod
    def validar_estado(cls, v: str) -> str:
        estados_validos = ['activa', 'completada', 'pausada', 'cancelada']
        if v.lower() not in estados_validos:
            raise ValueError(f'Estado debe ser uno de: {estados_validos}')
        return v.lower()

    @field_validator('hora_fin')
    @classmethod
    def validar_hora_fin(cls, v: Optional[str], info) -> Optional[str]:
        # Verificar si estado es completada y hora_fin es None
        estado = info.data.get('estado', '').lower()
        if estado == 'completada' and not v:
            raise ValueError('hora_fin es obligatorio cuando estado es "completada"')

        # Verificar que hora_fin sea posterior a hora_inicio
        if v and 'hora_inicio' in info.data:
            try:
                hora_inicio = datetime.fromisoformat(info.data['hora_inicio'])
                hora_fin = datetime.fromisoformat(v)
                if hora_fin <= hora_inicio:
                    raise ValueError('hora_fin debe ser posterior a hora_inicio')
            except ValueError as e:
                if 'posterior' in str(e):
                    raise
                raise ValueError(f'Formato de fecha inválido: {str(e)}')

        return v

    @field_validator('fecha', 'hora_inicio')
    @classmethod
    def validar_formato_fecha(cls, v: str) -> str:
        try:
            if len(v) == 10:  # formato fecha: "2025-11-23"
                datetime.strptime(v, '%Y-%m-%d')
            else:  # formato datetime: "2025-11-23T08:00:00"
                datetime.fromisoformat(v)
        except ValueError:
            raise ValueError(f'Formato de fecha/hora inválido. Use ISO format (YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS)')
        return v

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

# ============= SCHEMAS PARA ENDPOINT OPTIMIZADO CON DETALLES =============

class MaquinaConHorasSchema(BaseModel):
    """Schema para máquinas con horas totales calculadas por proyecto"""
    id: int
    nombre: str
    horas_uso: int = 0
    horas_maquina: int = 0
    horometro_inicial: Optional[float] = 0
    proximo_mantenimiento: Optional[float] = None
    horas_totales: int = 0  # Horas totales trabajadas en el proyecto
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        from_attributes = True

class UsuarioDetalladoSchema(BaseModel):
    """Schema completo de usuario para relaciones anidadas"""
    id: int
    nombre: str
    email: EmailStr
    estado: bool
    roles: List[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class AridoDetalladoSchema(BaseModel):
    """Schema para áridos con información completa del usuario"""
    id: int
    tipo_arido: str
    nombre: Optional[str] = None
    cantidad: int
    fecha_entrega: datetime
    usuario: UsuarioDetalladoSchema
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReporteLaboralDetalladoSchema(BaseModel):
    """Schema para reportes laborales con máquina y usuario completos"""
    id: int
    maquina_id: int
    usuario_id: Optional[int] = None
    proyecto_id: Optional[int] = None
    fecha_asignacion: datetime
    horas_turno: int
    horometro_inicial: Optional[float] = None
    maquina: MaquinaOut  # Máquina completa
    usuario: Optional[UsuarioDetalladoSchema] = None  # Usuario completo
    created: Optional[datetime] = None
    updated: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProyectoConDetallesResponse(BaseModel):
    """Schema optimizado que retorna proyecto con todas sus relaciones en una sola query"""
    # Datos del proyecto
    id: int
    nombre: str
    descripcion: Optional[str] = None
    estado: bool
    fecha_creacion: Optional[datetime] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    progreso: Optional[int] = 0
    gerente: Optional[str] = None
    contrato_id: Optional[int] = None
    ubicacion: Optional[str] = None
    contrato_url: Optional[str] = None
    contrato_nombre: Optional[str] = None
    contrato_tipo: Optional[str] = None

    # Relaciones optimizadas
    maquinas: List[MaquinaConHorasSchema] = []  # Máquinas con horas totales
    aridos: List[AridoDetalladoSchema] = []  # Áridos con usuario
    reportes_laborales: List[ReporteLaboralDetalladoSchema] = []  # Reportes con máquina y usuario
    contrato_archivos: List[ContratoArchivoResponse] = []  # Archivos de contrato

    class Config:
        from_attributes = True