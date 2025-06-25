from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional, Union

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

class UserOut(UsuarioBase):
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
    usuario_id: Optional[int] = None
    maquina_id: Optional[int] = None
    tipo: str
    importe_total: int
    fecha: datetime
    descripcion: str
    imagen: str

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
    estado: bool
    horas_uso: int

class MaquinaCreate(MaquinaBase):
    pass

class MaquinaSchema(MaquinaBase):
    id: Optional[int] = None

    class Config:
        from_attributes = True

class MaquinaOut(MaquinaBase):
    id: Optional[int] = None

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
    producto_id: Optional[int] = None
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
    maquina_id: Optional[int] = None
    usuario_id: Optional[int] = None
    fecha_asignacion: datetime
    horas_turno: datetime

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