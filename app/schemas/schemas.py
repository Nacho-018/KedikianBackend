from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

class UsuarioSchema(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    hash_contrasena: str
    estado: bool
    roles: List[str]
    fecha_creacion: datetime

    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    # hash_contrasena: str
    estado: bool
    # roles: List[str]
    fecha_creacion: datetime

class ArrendamientoSchema(BaseModel):
    id: int
    proyecto_id: int
    maquina_id: int
    horas_uso: int
    fecha_asignacion: datetime

    class Config:
        from_attributes = True

class ContratoSchema(BaseModel):
    id: int
    proyecto_id: int
    detalle: str
    cliente: str
    importe_total: int
    fecha_inicio: datetime
    fecha_terminacion: datetime

    class Config:
        from_attributes = True

class GastoSchema(BaseModel):
    id: int
    usuario_id: int
    maquina_id: int
    tipo: str
    importe_total: int
    fecha: datetime
    descripcion: str
    imagen: str

    class Config:
        from_attributes = True

class MaquinaSchema(BaseModel):
    id: int
    nombre: str
    estado: bool
    horas_uso: int

    class Config:
        from_attributes = True

class MovimientoInventarioSchema(BaseModel):
    id: int
    producto_id: int
    usuario_id: int
    cantidad: int
    fecha: datetime
    tipo_transaccion: str  # "entrada" o "salida"

    class Config:
        from_attributes = True

class PagoSchema(BaseModel):
    id: int
    proyecto_id: int
    producto_id: int
    importe_total: int
    fecha: datetime
    descripcion: str

    class Config:
        from_attributes = True

class ProductoSchema(BaseModel):
    id: int
    nombre: str
    codigo_producto: str
    inventario: int
    url_imagen: Optional[str] = None

    class Config:
        from_attributes = True

class ProyectoSchema(BaseModel):
    id: int
    nombre: str
    estado: bool
    fecha_creacion: datetime
    contrato_id: int
    ubicacion: str

    class Config:
        from_attributes = True

class ReporteLaboralSchema(BaseModel):
    id: int
    maquina_id: int
    usuario_id: int
    fecha_asignacion: datetime
    horas_turno: datetime

    class Config:
        from_attributes = True