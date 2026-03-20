"""
Schemas para API Externa
Modelos Pydantic utilizados por los endpoints de integración externa
"""

from pydantic import BaseModel
from typing import Optional, Any, Dict


class APIResponse(BaseModel):
    """
    Respuesta estándar de la API externa

    Attributes:
        success: Indica si la operación fue exitosa
        message: Mensaje descriptivo del resultado
        data: Datos retornados (opcional)
        total: Total de registros (opcional, útil para paginación)
    """
    success: bool
    message: str
    data: Optional[Any] = None
    total: Optional[int] = None


class GenericRequest(BaseModel):
    """
    Request genérico para crear/actualizar recursos

    Attributes:
        resource: Nombre del recurso a manipular
        payload: Datos del recurso en formato diccionario
    """
    resource: str
    payload: Dict[str, Any]


class TokenData(BaseModel):
    """
    Datos decodificados del JWT

    Attributes:
        sub: Subject (identificador principal)
        system: Sistema que generó el token
    """
    sub: str
    system: Optional[str] = None


class Token(BaseModel):
    """
    Token de acceso JWT

    Attributes:
        access_token: Token JWT firmado
        token_type: Tipo de token (siempre "bearer")
        expires_in: Tiempo de expiración en segundos
    """
    access_token: str
    token_type: str = "bearer"
    expires_in: int
