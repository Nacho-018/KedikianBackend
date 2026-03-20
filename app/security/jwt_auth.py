"""
Autenticación JWT para API Externa
Sistema de autenticación separado para comunicación entre sistemas
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.external_api import TokenData
from app.core.config import settings

# Esquema de seguridad HTTP Bearer
security = HTTPBearer()


def create_access_token(
    sub: str,
    system: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Genera un token JWT para autenticación de sistemas externos

    Args:
        sub: Subject del token (identificador del sistema)
        system: Nombre del sistema que solicita el token
        expires_delta: Tiempo de expiración personalizado (opcional)

    Returns:
        str: Token JWT firmado

    Example:
        >>> token = create_access_token("terrasoftarg", "terrasoft")
        >>> print(token)
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    """
    to_encode = {
        "sub": sub,
        "system": system,
        "iat": datetime.utcnow()
    }

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Dependency de FastAPI que verifica y decodifica el token JWT

    Args:
        credentials: Credenciales HTTP Bearer del header Authorization

    Returns:
        TokenData: Datos decodificados del token

    Raises:
        HTTPException: Si el token es inválido, expiró o no contiene los campos requeridos

    Example:
        En un endpoint:
        >>> @app.get("/api/v1/recursos")
        >>> async def get_recursos(token: TokenData = Depends(verify_token)):
        >>>     print(f"Sistema autenticado: {token.system}")
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        sub: str = payload.get("sub")
        system: str = payload.get("system")

        if sub is None:
            raise credentials_exception

        token_data = TokenData(sub=sub, system=system)
        return token_data

    except JWTError:
        raise credentials_exception
