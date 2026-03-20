"""
Schemas para API de Clientes
Modelos Pydantic utilizados por los endpoints de consulta de clientes
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class ClientMaquinaView(BaseModel):
    """
    Vista de máquina asignada a un proyecto para clientes

    Attributes:
        nombre: Nombre/modelo de la máquina
        horas_trabajadas: Total de horas trabajadas en el proyecto
    """
    nombre: str
    horas_trabajadas: float

    class Config:
        from_attributes = True


class ClientAridoView(BaseModel):
    """
    Vista de árido utilizado en un proyecto para clientes

    Attributes:
        tipo: Tipo de árido (ej: "Relleno", "Arena", etc.)
        cantidad: Cantidad total utilizada
        unidad: Unidad de medida (ej: "m³", "kg", etc.)
        cantidad_registros: Número de registros de este árido
    """
    tipo: str
    cantidad: float
    unidad: str
    cantidad_registros: int

    class Config:
        from_attributes = True


class ClientProjectView(BaseModel):
    """
    Vista completa de proyecto para clientes

    Attributes:
        id: ID único del proyecto
        nombre: Nombre del proyecto
        estado: Estado del proyecto ("EN PROGRESO", "COMPLETADO")
        descripcion: Descripción detallada del trabajo
        fecha_inicio: Fecha de inicio del proyecto
        ubicacion: Ubicación física del proyecto
        maquinas_asignadas: Lista de máquinas con horas trabajadas
        total_horas_maquinas: Suma total de horas de todas las máquinas
        aridos_utilizados: Lista de áridos utilizados agrupados por tipo
        total_aridos: Suma total de áridos (en m³ o unidad correspondiente)
    """
    id: int
    nombre: str
    estado: str
    descripcion: Optional[str] = ""
    fecha_inicio: Optional[str] = None
    ubicacion: Optional[str] = ""
    maquinas_asignadas: List[ClientMaquinaView] = []
    total_horas_maquinas: float = 0.0
    aridos_utilizados: List[ClientAridoView] = []
    total_aridos: float = 0.0

    class Config:
        from_attributes = True


class ClientAPIResponse(BaseModel):
    """
    Respuesta estándar de la API de clientes

    Attributes:
        success: Indica si la operación fue exitosa
        message: Mensaje descriptivo del resultado
        data: Datos retornados (proyecto individual o lista)
        total: Total de registros (opcional, para listas)
    """
    success: bool
    message: str
    data: ClientProjectView | List[ClientProjectView]
    total: Optional[int] = None
