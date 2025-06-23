from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

class UsuarioSchema(BaseModel):
    id: Optional[int] = None
    nombre: str
    email: EmailStr
    hash_contrasena: str
    estado: bool
    roles: List[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    hash_contrasena: str
    estado: bool = True
    roles: List[str]
    fecha_creacion: Optional[datetime] = None

class UserOut(BaseModel):
    id: Optional[int] = None
    nombre: str
    email: EmailStr
    # hash_contrasena: str
    estado: bool
    # roles: List[str]
    fecha_creacion: datetime

class ArrendamientoSchema(BaseModel):
    id: Optional[int] = None
    proyecto_id: Optional[int] = None
    maquina_id: Optional[int] = None
    horas_uso: int
    fecha_asignacion: datetime

    class Config:
        from_attributes = True

class ContratoSchema(BaseModel):
    id: Optional[int] = None
    proyecto_id: Optional[int] = None
    detalle: str
    cliente: str
    importe_total: int
    fecha_inicio: datetime
    fecha_terminacion: datetime

    class Config:
        from_attributes = True

class GastoSchema(BaseModel):
    id: Optional[int] = None
    usuario_id: Optional[int] = None
    maquina_id: Optional[int] = None
    tipo: str
    importe_total: int
    fecha: datetime
    descripcion: str
    imagen: str

    class Config:
        from_attributes = True

class MaquinaSchema(BaseModel):
    id: Optional[int] = None
    nombre: str
    estado: bool
    horas_uso: int

    class Config:
        from_attributes = True

class MovimientoInventarioSchema(BaseModel):
    id: Optional[int] = None
    producto_id: Optional[int] = None
    usuario_id: Optional[int] = None
    cantidad: int
    fecha: datetime
    tipo_transaccion: str  # "entrada" o "salida"

    class Config:
        from_attributes = True

class PagoSchema(BaseModel):
    id: Optional[int] = None
    proyecto_id: Optional[int] = None
    producto_id: Optional[int] = None
    importe_total: int
    fecha: datetime
    descripcion: str

    class Config:
        from_attributes = True

class ProductoSchema(BaseModel):
    id: Optional[int] = None
    nombre: str
    codigo_producto: str
    inventario: int
    url_imagen: Optional[str] = None

    class Config:
        from_attributes = True

class ProyectoSchema(BaseModel):
    id: Optional[int] = None
    nombre: str
    estado: bool
    fecha_creacion: datetime
    contrato_id: Optional[int] = None
    ubicacion: str

    class Config:
        from_attributes = True

class ReporteLaboralSchema(BaseModel):
    id: Optional[int] = None
    maquina_id: Optional[int] = None
    usuario_id: Optional[int] = None
    fecha_asignacion: datetime
    horas_turno: datetime

    class Config:
        from_attributes = True