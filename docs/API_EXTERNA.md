# API Externa - Kedikian CRM

Sistema de API REST con autenticación JWT para integración con sistemas externos (TerraSoft, etc.).

## 🔐 Autenticación

### Obtener Token JWT

**Endpoint:** `POST /auth/token`

**Parámetros:**
- `system_name`: Nombre del sistema (ej: "terrasoftarg")
- `secret`: Secreto compartido configurado en `.env`

**Ejemplo:**
```bash
curl -X POST "http://localhost:8000/auth/token?system_name=terrasoftarg&secret=terrasoft_kedikian_shared_secret_2025"
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 📋 Endpoints de Recursos

Todos los endpoints requieren el header:
```
Authorization: Bearer {token}
```

### GET - Obtener Recursos

**Endpoint:** `GET /api/v1/recursos`

**Parámetros:**
- `resource` (requerido): Tipo de recurso
- `id` (opcional): ID específico del recurso

**Recursos disponibles:**
- `maquinas`
- `proyectos`
- `contratos`
- `gastos`
- `pagos`
- `productos`
- `arrendamientos`
- `movimientos_inventario`
- `reportes_laborales`
- `entregas_arido`
- `usuarios`
- `mantenimientos`
- `jornadas_laborales`
- `reportes_cuenta_corriente`
- `cotizaciones`

**Ejemplos:**

```bash
# Obtener todas las máquinas
curl -X GET "http://localhost:8000/api/v1/recursos?resource=maquinas" \
  -H "Authorization: Bearer {token}"

# Obtener máquina con ID 5
curl -X GET "http://localhost:8000/api/v1/recursos?resource=maquinas&id=5" \
  -H "Authorization: Bearer {token}"

# Obtener todos los proyectos
curl -X GET "http://localhost:8000/api/v1/recursos?resource=proyectos" \
  -H "Authorization: Bearer {token}"
```

**Respuesta exitosa:**
```json
{
  "success": true,
  "message": "maquinas obtenidos exitosamente",
  "data": [
    {
      "id": 1,
      "nombre": "Excavadora CAT 320",
      "tipo": "Excavadora",
      "modelo": "CAT 320D",
      "horometro_inicial": 1000
    }
  ],
  "total": 1
}
```

### POST - Crear Recursos

**Endpoint:** `POST /api/v1/recursos`

**Body:**
```json
{
  "resource": "nombre_recurso",
  "payload": {
    // Datos del recurso
  }
}
```

**Ejemplo - Crear Máquina:**
```bash
curl -X POST "http://localhost:8000/api/v1/recursos" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "resource": "maquinas",
    "payload": {
      "nombre": "Bulldozer D8",
      "tipo": "Bulldozer",
      "modelo": "D8T",
      "horometro_inicial": 500
    }
  }'
```

**Ejemplo - Crear Proyecto:**
```bash
curl -X POST "http://localhost:8000/api/v1/recursos" \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "resource": "proyectos",
    "payload": {
      "nombre": "Proyecto Ruta 40",
      "descripcion": "Construcción tramo sur",
      "estado": "activo",
      "gerente": "Juan Pérez"
    }
  }'
```

---

## 🐍 Cliente Python

### Instalación

```bash
pip install httpx
```

### Uso Básico

```python
import asyncio
from app.services.external_client import KedikianClient

async def main():
    # Autenticar
    client = await KedikianClient.authenticate(
        base_url="http://localhost:8000",
        system_name="terrasoftarg",
        shared_secret="terrasoft_kedikian_shared_secret_2025"
    )

    try:
        # Obtener todas las máquinas
        response = await client.get("maquinas")
        print(f"Total máquinas: {response['total']}")
        print(response['data'])

        # Obtener máquina específica
        response = await client.get("maquinas", id=5)
        print(response['data'])

        # Crear nuevo proyecto
        response = await client.post("proyectos", {
            "nombre": "Proyecto Ruta 40",
            "descripcion": "Construcción tramo sur",
            "estado": "activo"
        })
        print(f"Proyecto creado: {response['data']}")

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Uso con Context Manager (recomendado)

```python
async def main():
    async with await KedikianClient.authenticate(
        base_url="http://localhost:8000",
        system_name="terrasoftarg",
        shared_secret="terrasoft_kedikian_shared_secret_2025"
    ) as client:
        # Realizar operaciones
        maquinas = await client.get("maquinas")
        print(maquinas)
    # El cliente se cierra automáticamente

asyncio.run(main())
```

---

## 🔒 Seguridad

1. **Secret Key**: Cambiar `JWT_SECRET_KEY` en producción (generar con `openssl rand -hex 32`)
2. **Shared Secret**: Cambiar `EXTERNAL_SHARED_SECRET` y compartirlo solo con sistemas autorizados
3. **HTTPS**: Usar siempre HTTPS en producción
4. **Token Expiration**: Los tokens expiran en 60 minutos por defecto
5. **Rate Limiting**: Considerar implementar rate limiting para proteger la API

---

## 📝 Configuración

### Variables de Entorno (.env)

```env
# JWT para API Externa
JWT_SECRET_KEY=4a8f5c7b9d2e6f1a3c5b7d9e0f2a4c6b8d0e2f4a6c8e0f2a4c6b8d0e2f4a6c8
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
EXTERNAL_SHARED_SECRET=terrasoft_kedikian_shared_secret_2025
```

### Generar Secret Key

```bash
openssl rand -hex 32
```

---

## 🧪 Testing

### Swagger UI

Visitar: `http://localhost:8000/docs`

Los endpoints de API Externa están bajo:
- **Tag "Autenticación Externa"**: `/auth/token`
- **Tag "API Externa"**: `/api/v1/recursos`

### Postman Collection

Importar los siguientes requests:

**1. Obtener Token**
- Method: POST
- URL: `http://localhost:8000/auth/token?system_name=terrasoftarg&secret=terrasoft_kedikian_shared_secret_2025`

**2. Obtener Recursos**
- Method: GET
- URL: `http://localhost:8000/api/v1/recursos?resource=maquinas`
- Headers: `Authorization: Bearer {token}`

**3. Crear Recurso**
- Method: POST
- URL: `http://localhost:8000/api/v1/recursos`
- Headers: `Authorization: Bearer {token}`, `Content-Type: application/json`
- Body: Ver ejemplos arriba

---

## ❌ Manejo de Errores

### 401 Unauthorized
Token inválido o expirado. Obtener un nuevo token.

```json
{
  "detail": "Token inválido o expirado"
}
```

### 403 Forbidden
Secreto compartido incorrecto.

```json
{
  "detail": "Secreto inválido. Acceso denegado."
}
```

### 400 Bad Request
Recurso no soportado.

```json
{
  "detail": "Recurso 'xyz' no soportado"
}
```

### 404 Not Found
Recurso con ID especificado no existe.

```json
{
  "detail": "maquinas con ID 999 no encontrado"
}
```

### 500 Internal Server Error
Error interno del servidor.

```json
{
  "detail": "Error al obtener maquinas: ..."
}
```
