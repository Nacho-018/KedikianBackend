"""
Router de Autenticación Externa
Endpoint para que sistemas externos obtengan tokens JWT
"""

from fastapi import APIRouter, HTTPException, status
from app.schemas.external_api import Token
from app.security.jwt_auth import create_access_token
from app.core.config import settings
from datetime import timedelta

router = APIRouter(
    prefix="/v1/auth-external",
    tags=["Autenticación Externa"]
)


@router.post("/token", response_model=Token)
async def get_external_token(
    system_name: str,
    secret: str
):
    """
    Genera un token JWT para sistemas externos autorizados

    Este endpoint valida que el sistema externo proporcione el secreto compartido correcto
    y retorna un token JWT válido por el tiempo configurado en JWT_EXPIRE_MINUTES.

    Args:
        system_name: Nombre del sistema que solicita el token (ej: "terrasoftarg")
        secret: Secreto compartido previamente acordado

    Returns:
        Token: Objeto conteniendo el access_token, tipo y tiempo de expiración

    Raises:
        HTTPException 403: Si el secreto proporcionado no coincide

    Example:
        POST /auth/token?system_name=terrasoftarg&secret=CLAVE_COMPARTIDA

        Response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 3600
        }
    """
    # Validar secreto compartido
    if secret != settings.EXTERNAL_SHARED_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Secreto inválido. Acceso denegado."
        )

    # Generar token con tiempo de expiración configurado
    expires_delta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        sub=system_name,
        system=system_name,
        expires_delta=expires_delta
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRE_MINUTES * 60  # Convertir a segundos
    )
