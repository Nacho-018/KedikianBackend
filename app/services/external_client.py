"""
Cliente HTTP para comunicación con la API Externa de Kedikian
Facilita la integración desde sistemas externos (TerraSoft, etc.)
"""

import httpx
from typing import Optional, Dict, Any


class KedikianClient:
    """
    Cliente asíncrono para interactuar con la API Externa de Kedikian

    Este cliente maneja automáticamente la autenticación JWT y proporciona
    métodos convenientes para operaciones GET y POST sobre recursos.

    Attributes:
        base_url: URL base de la API de Kedikian
        token: Token JWT de autenticación
        timeout: Timeout en segundos para las peticiones HTTP

    Example:
        >>> # Autenticar y crear cliente
        >>> client = await KedikianClient.authenticate(
        ...     base_url="http://localhost:8000",
        ...     system_name="terrasoftarg",
        ...     shared_secret="CLAVE_COMPARTIDA"
        ... )
        >>>
        >>> # Obtener todas las máquinas
        >>> maquinas = await client.get("maquinas")
        >>> print(maquinas)
        >>>
        >>> # Obtener una máquina específica
        >>> maquina = await client.get("maquinas", id=5)
        >>> print(maquina)
        >>>
        >>> # Crear un nuevo proyecto
        >>> proyecto = await client.post("proyectos", {
        ...     "nombre": "Proyecto Ruta 40",
        ...     "descripcion": "Construcción tramo sur",
        ...     "estado": "activo"
        ... })
        >>> print(proyecto)
    """

    def __init__(self, base_url: str, token: str, timeout: int = 15):
        """
        Inicializa el cliente con un token JWT

        Args:
            base_url: URL base de la API (ej: "http://localhost:8000")
            token: Token JWT obtenido del endpoint /auth/token
            timeout: Timeout en segundos (default: 15)
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )

    @classmethod
    async def authenticate(
        cls,
        base_url: str,
        system_name: str,
        shared_secret: str,
        timeout: int = 15
    ) -> "KedikianClient":
        """
        Crea y autentica un nuevo cliente contra la API de Kedikian

        Este método de clase obtiene automáticamente el token JWT necesario
        y retorna un cliente ya autenticado listo para usar.

        Args:
            base_url: URL base de la API (ej: "http://localhost:8000")
            system_name: Nombre del sistema externo (ej: "terrasoftarg")
            shared_secret: Secreto compartido configurado en .env
            timeout: Timeout en segundos (default: 15)

        Returns:
            KedikianClient: Cliente autenticado y listo para usar

        Raises:
            httpx.HTTPStatusError: Si la autenticación falla (401, 403)
            httpx.RequestError: Si hay problemas de conexión

        Example:
            >>> client = await KedikianClient.authenticate(
            ...     base_url="http://kedikian.site",
            ...     system_name="terrasoftarg",
            ...     shared_secret="mi_clave_secreta"
            ... )
            >>> print("✅ Autenticado correctamente")
        """
        auth_url = f"{base_url.rstrip('/')}/auth/token"

        async with httpx.AsyncClient(timeout=timeout) as temp_client:
            response = await temp_client.post(
                auth_url,
                params={
                    "system_name": system_name,
                    "secret": shared_secret
                }
            )
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data["access_token"]

        return cls(base_url=base_url, token=access_token, timeout=timeout)

    async def get(
        self,
        resource: str,
        id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Obtiene recursos mediante GET

        Args:
            resource: Nombre del recurso (ej: "maquinas", "proyectos")
            id: ID específico del recurso (opcional)

        Returns:
            Dict con la respuesta de la API (APIResponse)

        Raises:
            httpx.HTTPStatusError: Si el servidor retorna error (400, 404, 500)
            httpx.RequestError: Si hay problemas de conexión

        Example:
            >>> # Obtener todas las máquinas
            >>> response = await client.get("maquinas")
            >>> print(response["data"])
            >>>
            >>> # Obtener máquina con ID 5
            >>> response = await client.get("maquinas", id=5)
            >>> print(response["data"]["nombre"])
        """
        url = f"{self.base_url}/api/v1/recursos"
        params = {"resource": resource}

        if id is not None:
            params["id"] = id

        response = await self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def post(
        self,
        resource: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea recursos mediante POST

        Args:
            resource: Nombre del recurso (ej: "maquinas", "proyectos")
            payload: Datos del recurso a crear

        Returns:
            Dict con la respuesta de la API (APIResponse)

        Raises:
            httpx.HTTPStatusError: Si el servidor retorna error (400, 500)
            httpx.RequestError: Si hay problemas de conexión

        Example:
            >>> # Crear una nueva máquina
            >>> response = await client.post("maquinas", {
            ...     "nombre": "Bulldozer D8",
            ...     "tipo": "Bulldozer",
            ...     "modelo": "D8T",
            ...     "horometro_inicial": 500
            ... })
            >>> print(f"Máquina creada con ID: {response['data']['id']}")
        """
        url = f"{self.base_url}/api/v1/recursos"
        body = {
            "resource": resource,
            "payload": payload
        }

        response = await self._client.post(url, json=body)
        response.raise_for_status()
        return response.json()

    async def close(self):
        """
        Cierra la conexión HTTP del cliente

        Importante: Siempre llamar este método cuando se termine de usar el cliente
        para liberar recursos de red.

        Example:
            >>> client = await KedikianClient.authenticate(...)
            >>> # ... realizar operaciones ...
            >>> await client.close()
            >>>
            >>> # O usar context manager (recomendado):
            >>> async with await KedikianClient.authenticate(...) as client:
            ...     data = await client.get("maquinas")
        """
        await self._client.aclose()

    async def __aenter__(self):
        """Soporte para async context manager"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cierre automático al salir del context manager"""
        await self.close()
