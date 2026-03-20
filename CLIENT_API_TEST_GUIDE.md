# 🧪 Guía de Pruebas en Postman - API de Clientes

## 📍 Base URL
```
https://kedikian.site/api
```

---

## 🔐 AUTENTICACIÓN

Los endpoints de clientes usan el mismo sistema de autenticación JWT que la API externa.

### Obtener Token JWT

**Método:** `POST`
**URL:**
```
https://kedikian.site/api/v1/auth-external/token
```

**Query Params:**
| Key | Value |
|-----|-------|
| system_name | terrasoftarg |
| secret | [tu EXTERNAL_SHARED_SECRET] |

**Expected Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**⚠️ IMPORTANTE:** Guarda el `access_token` - lo necesitarás para todos los endpoints de clientes.

---

## 📊 ENDPOINTS DE CLIENTES

### 1️⃣ Obtener Todos los Proyectos Activos

**Método:** `GET`
**URL:**
```
https://kedikian.site/api/v1/client/proyectos
```

**Headers:**
```
Authorization: Bearer [tu_access_token]
```

**Expected Response (200 OK):**
```json
{
  "success": true,
  "message": "Proyectos obtenidos exitosamente",
  "data": [
    {
      "id": 1,
      "nombre": "La Quinta Livetti",
      "estado": "EN PROGRESO",
      "descripcion": "Demoler casa retirar escombro extraer arboles tapar sangría y cámara séptica",
      "fecha_inicio": "2026-03-09",
      "ubicacion": "estancia vieja",
      "maquinas_asignadas": [
        {
          "nombre": "BOBCAT 2018 S650",
          "horas_trabajadas": 13.0
        },
        {
          "nombre": "EXCAVADORA 2023 XCMG E60",
          "horas_trabajadas": 15.0
        }
      ],
      "total_horas_maquinas": 28.0,
      "aridos_utilizados": [
        {
          "tipo": "Relleno",
          "cantidad": 80.0,
          "unidad": "m³",
          "cantidad_registros": 3
        }
      ],
      "total_aridos": 80.0
    }
  ],
  "total": 1
}
```

---

### 2️⃣ Obtener Proyecto Específico por ID

**Método:** `GET`
**URL:**
```
https://kedikian.site/api/v1/client/proyectos/1
```

**Headers:**
```
Authorization: Bearer [tu_access_token]
```

**Path Parameters:**
- `proyecto_id` (integer): ID del proyecto a consultar

**Expected Response (200 OK):**
```json
{
  "success": true,
  "message": "Proyecto obtenido exitosamente",
  "data": {
    "id": 1,
    "nombre": "La Quinta Livetti",
    "estado": "EN PROGRESO",
    "descripcion": "Demoler casa retirar escombro extraer arboles tapar sangría y cámara séptica",
    "fecha_inicio": "2026-03-09",
    "ubicacion": "estancia vieja",
    "maquinas_asignadas": [
      {
        "nombre": "BOBCAT 2018 S650",
        "horas_trabajadas": 13.0
      }
    ],
    "total_horas_maquinas": 13.0,
    "aridos_utilizados": [
      {
        "tipo": "Relleno",
        "cantidad": 80.0,
        "unidad": "m³",
        "cantidad_registros": 3
      }
    ],
    "total_aridos": 80.0
  },
  "total": 1
}
```

---

## 🚨 Códigos de Error

### 401 Unauthorized
```json
{
  "detail": "Token inválido o expirado"
}
```
**Solución:** Genera un nuevo token (los tokens expiran en 60 minutos)

### 404 Not Found
```json
{
  "detail": "Proyecto con ID 999 no encontrado o no está activo"
}
```
**Solución:** Verifica que el ID del proyecto exista y esté activo

### 500 Internal Server Error
```json
{
  "detail": "Error al obtener proyectos: ..."
}
```
**Solución:** Revisa los logs del servidor para más detalles

---

## 🎯 Configuración en Postman

### Environment Variables

Crea un Environment "Kedikian Client" con estas variables:

| Variable | Value |
|----------|-------|
| base_url | https://kedikian.site/api |
| system_name | terrasoftarg |
| secret | [tu_EXTERNAL_SHARED_SECRET] |
| access_token | (vacío, se llenará después) |

### Collection Structure

```
Kedikian Client API
├── Auth
│   └── POST Get Token
└── Proyectos
    ├── GET Todos los Proyectos
    └── GET Proyecto por ID
```

### Pre-request Script (Auto Token)

Agrega este script a la Collection para obtener el token automáticamente:

```javascript
const baseUrl = pm.environment.get("base_url");
const systemName = pm.environment.get("system_name");
const secret = pm.environment.get("secret");
const currentToken = pm.environment.get("access_token");

// Solo obtener nuevo token si no existe
if (!currentToken) {
    const tokenUrl = `${baseUrl}/v1/auth-external/token?system_name=${systemName}&secret=${secret}`;

    pm.sendRequest({
        url: tokenUrl,
        method: 'POST'
    }, function (err, res) {
        if (!err && res.code === 200) {
            const token = res.json().access_token;
            pm.environment.set("access_token", token);
            console.log("✅ Token obtenido");
        } else {
            console.error("❌ Error obteniendo token");
        }
    });
}
```

---

## 📋 Estructura de Datos

### ClientProjectView

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | integer | ID único del proyecto |
| nombre | string | Nombre del proyecto |
| estado | string | "EN PROGRESO" o "COMPLETADO" |
| descripcion | string | Descripción detallada |
| fecha_inicio | string | Formato YYYY-MM-DD |
| ubicacion | string | Ubicación física |
| maquinas_asignadas | array | Lista de máquinas con horas |
| total_horas_maquinas | float | Total de horas trabajadas |
| aridos_utilizados | array | Lista de áridos por tipo |
| total_aridos | float | Total de áridos en m³ |

### ClientMaquinaView

| Campo | Tipo | Descripción |
|-------|------|-------------|
| nombre | string | Nombre de la máquina |
| horas_trabajadas | float | Horas totales en el proyecto |

### ClientAridoView

| Campo | Tipo | Descripción |
|-------|------|-------------|
| tipo | string | Tipo de árido |
| cantidad | float | Cantidad total |
| unidad | string | Unidad de medida (m³) |
| cantidad_registros | integer | Número de entregas |

---

## ✅ Checklist de Pruebas

- [ ] Obtener token exitosamente
- [ ] Consultar todos los proyectos activos
- [ ] Consultar proyecto específico por ID
- [ ] Verificar que las horas de máquinas se suman correctamente
- [ ] Verificar que los áridos se agrupan por tipo
- [ ] Probar con token expirado
- [ ] Probar con ID de proyecto inexistente
- [ ] Probar sin Authorization header

---

## 🔍 Validación de Datos

### Verificar cálculos:

**Total de horas:**
```
total_horas_maquinas = suma de todas las horas_trabajadas de maquinas_asignadas
```

**Total de áridos:**
```
total_aridos = suma de todas las cantidades de aridos_utilizados
```

**Estado del proyecto:**
- `proyecto.estado = true` → "EN PROGRESO"
- `proyecto.estado = false` → "COMPLETADO"

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

---

## 🐛 Troubleshooting

### Problema: No aparecen máquinas en maquinas_asignadas
**Causa:** No hay reportes laborales asociados al proyecto
**Verificación:** Revisar tabla `reporte_laboral` con el `proyecto_id`

### Problema: No aparecen áridos en aridos_utilizados
**Causa:** No hay entregas de áridos asociadas al proyecto
**Verificación:** Revisar tabla `entrega_arido` con el `proyecto_id`

### Problema: total_horas_maquinas no coincide
**Causa:** Hay registros con horas_turno NULL
**Verificación:** Revisar que todos los reportes tengan horas_turno válidas

---

## 📞 Soporte

Si encuentras errores o comportamientos inesperados, revisa:
1. Logs del servidor: `sudo journalctl -u kedikian-api -f`
2. Swagger docs: `/api/docs`
3. Base de datos directamente para validar datos
