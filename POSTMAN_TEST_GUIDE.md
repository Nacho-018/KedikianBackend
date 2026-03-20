# 🧪 Guía de Pruebas en Postman - API Externa Kedikian

## 📍 Base URL
```
https://kedikian.site/api
```

---

## 1️⃣ Obtener Token JWT

### Request
**Método:** `POST`
**URL:**
```
https://kedikian.site/api/v1/auth-external/token
```

### Query Params
| Key | Value |
|-----|-------|
| system_name | terrasoftarg |
| secret | terrasoft_kedikian_shared_secret_2025 |

### Expected Response (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### ⚠️ IMPORTANTE
**Copia el `access_token` completo - lo necesitarás para todos los siguientes endpoints**

---

## 2️⃣ Consultar Lista de Recursos

### Request
**Método:** `GET`
**URL:**
```
https://kedikian.site/api/v1/external/recursos?resource=maquinas
```

### Authorization
**Type:** Bearer Token
**Token:** `[pega aquí el access_token del paso 1]`

O en Headers:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Recursos disponibles
Cambia el parámetro `resource` por cualquiera de estos:

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

### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "maquinas obtenidos exitosamente",
  "data": [
    {
      "id": 1,
      "nombre": "Excavadora CAT 320",
      "tipo": "Excavadora",
      ...
    }
  ],
  "total": 10
}
```

---

## 3️⃣ Consultar Recurso Específico por ID

### Request
**Método:** `GET`
**URL:**
```
https://kedikian.site/api/v1/external/recursos?resource=maquinas&id=1
```

### Authorization
**Type:** Bearer Token
**Token:** `[tu access_token]`

### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "maquinas obtenido exitosamente",
  "data": {
    "id": 1,
    "nombre": "Excavadora CAT 320",
    "tipo": "Excavadora",
    ...
  },
  "total": 1
}
```

---

## 4️⃣ Crear Nuevo Recurso

### Request
**Método:** `POST`
**URL:**
```
https://kedikian.site/api/v1/external/recursos
```

### Headers
```
Authorization: Bearer [tu access_token]
Content-Type: application/json
```

### Body (raw JSON)
```json
{
  "resource": "maquinas",
  "payload": {
    "nombre": "Excavadora Nueva",
    "tipo": "Excavadora",
    "modelo": "CAT 330",
    "horometro_inicial": 500
  }
}
```

### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "maquinas creado exitosamente",
  "data": {
    "id": 15,
    "nombre": "Excavadora Nueva",
    ...
  }
}
```

---

## 🚨 Errores Comunes

### 401 Unauthorized
```json
{
  "detail": "Token inválido o expirado"
}
```
**Solución:** Genera un nuevo token (los tokens expiran en 60 minutos)

### 403 Forbidden
```json
{
  "detail": "Secreto inválido. Acceso denegado."
}
```
**Solución:** Verifica que el `secret` en el paso 1 sea correcto

### 400 Bad Request
```json
{
  "detail": "Recurso 'xyz' no soportado"
}
```
**Solución:** Verifica que el nombre del recurso sea correcto (ver lista en paso 2)

### 404 Not Found
```json
{
  "detail": "maquinas con ID 999 no encontrado"
}
```
**Solución:** El ID solicitado no existe en la base de datos

---

## 🎯 Configuración de Variables de Entorno en Postman

### Crear Environment "Kedikian Production"

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| base_url | https://kedikian.site/api | https://kedikian.site/api |
| system_name | terrasoftarg | terrasoftarg |
| secret | terrasoft_kedikian_shared_secret_2025 | terrasoft_kedikian_shared_secret_2025 |
| access_token | (vacío) | (se llenará automáticamente) |

### Usar variables en las requests

**URL del token:**
```
{{base_url}}/v1/auth-external/token?system_name={{system_name}}&secret={{secret}}
```

**URL de recursos:**
```
{{base_url}}/v1/external/recursos?resource=maquinas
```

**Authorization Header:**
```
Bearer {{access_token}}
```

---

## 🤖 Pre-request Script para Auto-refresh del Token

Agrega este script en la Collection para obtener el token automáticamente:

```javascript
// Pre-request Script
const baseUrl = pm.environment.get("base_url");
const systemName = pm.environment.get("system_name");
const secret = pm.environment.get("secret");
const currentToken = pm.environment.get("access_token");

// Solo obtener nuevo token si no existe o está por expirar
if (!currentToken) {
    const tokenUrl = `${baseUrl}/v1/auth-external/token?system_name=${systemName}&secret=${secret}`;

    pm.sendRequest({
        url: tokenUrl,
        method: 'POST'
    }, function (err, res) {
        if (!err && res.code === 200) {
            const token = res.json().access_token;
            pm.environment.set("access_token", token);
            console.log("✅ Token obtenido:", token.substring(0, 20) + "...");
        } else {
            console.error("❌ Error obteniendo token:", err || res.json());
        }
    });
}
```

---

## ✅ Checklist de Pruebas

- [ ] Obtener token exitosamente
- [ ] Consultar lista de maquinas
- [ ] Consultar lista de proyectos
- [ ] Consultar maquina específica por ID
- [ ] Crear nueva maquina
- [ ] Probar con token expirado (esperar 60 min o usar token viejo)
- [ ] Probar con secret incorrecto
- [ ] Probar sin Authorization header

---

## 📚 Documentación Adicional

**OpenAPI/Swagger:**
```
https://kedikian.site/api/docs
```

**ReDoc:**
```
https://kedikian.site/api/redoc
```
