# 📘 Documentación API de Clientes - Kedikian

**Versión:** 1.0.0
**Base URL:** `https://kedikian.site/api`
**Fecha:** Marzo 2026

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Autenticación](#autenticación)
3. [Endpoints Disponibles](#endpoints-disponibles)
4. [Modelos de Datos](#modelos-de-datos)
5. [Códigos de Error](#códigos-de-error)
6. [Ejemplos de Integración](#ejemplos-de-integración)
7. [Notas Importantes](#notas-importantes)

---

## 🎯 Introducción

Esta API permite consultar información de proyectos de construcción en tiempo real, incluyendo:
- Datos del proyecto (nombre, ubicación, estado, etc.)
- Máquinas asignadas con horas trabajadas
- Áridos utilizados con cantidades
- Totales calculados automáticamente

**Características:**
- ✅ Autenticación JWT
- ✅ Responses en JSON
- ✅ HTTPS seguro
- ✅ CORS habilitado

---

## 🔐 Autenticación

Todos los endpoints requieren autenticación mediante JWT (JSON Web Token).

### Paso 1: Obtener Token

**Endpoint:** `POST /v1/auth-external/token`

**URL Completa:**
```
https://kedikian.site/api/v1/auth-external/token
```

**Parámetros (Query String):**

| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `system_name` | string | Sí | Nombre del sistema (proporcionado por Kedikian) |
| `secret` | string | Sí | Clave secreta compartida (proporcionado por Kedikian) |

**Request de Ejemplo:**
```http
POST https://kedikian.site/api/v1/auth-external/token?system_name=terrasoftarg&secret=terrasoft_kedikian_shared_secret_2025
```

**Response Exitoso (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXJyYXNvZnRhcmciLCJzeXN0ZW0iOiJ0ZXJyYXNvZnRhcmciLCJpYXQiOjE3MTE4MjM0NTAsImV4cCI6MTcxMTgyNzA1MH0.abc123...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Importante:**
- El token expira en **60 minutos** (3600 segundos)
- Debe incluirse en todas las peticiones subsiguientes
- Formato del header: `Authorization: Bearer {access_token}`

---

## 📊 Endpoints Disponibles

### 1. Obtener Todos los Proyectos Activos

Retorna una lista de todos los proyectos en estado "EN PROGRESO" con toda su información.

**Endpoint:** `GET /v1/client/proyectos`

**URL Completa:**
```
https://kedikian.site/api/v1/client/proyectos
```

**Headers Requeridos:**
```http
Authorization: Bearer {access_token}
```

**Request de Ejemplo:**
```http
GET https://kedikian.site/api/v1/client/proyectos
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response Exitoso (200 OK):**
```json
{
  "success": true,
  "message": "Proyectos obtenidos exitosamente",
  "data": [
    {
      "id": 79,
      "nombre": "HOTEL KING",
      "estado": "EN PROGRESO",
      "descripcion": "Retiro de pileta y nivelación",
      "fecha_inicio": "2026-02-18",
      "ubicacion": "San martin",
      "maquinas_asignadas": [
        {
          "nombre": "EXCAVADORA 2023 XCMG E60.",
          "horas_trabajadas": 21.0
        },
        {
          "nombre": "BOBCAT 2018 S650.",
          "horas_trabajadas": 9.0
        }
      ],
      "total_horas_maquinas": 30.0,
      "aridos_utilizados": [
        {
          "tipo": "Relleno",
          "cantidad": 150.0,
          "unidad": "m³",
          "cantidad_registros": 5
        },
        {
          "tipo": "Arena",
          "cantidad": 25.0,
          "unidad": "m³",
          "cantidad_registros": 2
        }
      ],
      "total_aridos": 175.0
    },
    {
      "id": 80,
      "nombre": "CONSTRUCCIÓN EDIFICIO CENTRAL",
      "estado": "EN PROGRESO",
      "descripcion": "Excavación y cimientos",
      "fecha_inicio": "2026-03-01",
      "ubicacion": "Centro",
      "maquinas_asignadas": [
        {
          "nombre": "EXCAVADORA 2022 CAT 320",
          "horas_trabajadas": 45.0
        }
      ],
      "total_horas_maquinas": 45.0,
      "aridos_utilizados": [
        {
          "tipo": "Piedra",
          "cantidad": 200.0,
          "unidad": "m³",
          "cantidad_registros": 8
        }
      ],
      "total_aridos": 200.0
    }
  ],
  "total": 2
}
```

---

### 2. Obtener Proyecto por ID

Retorna un proyecto específico con toda su información.

**Endpoint:** `GET /v1/client/proyectos/{id}`

**URL Completa:**
```
https://kedikian.site/api/v1/client/proyectos/{id}
```

**Parámetros de Ruta:**

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `id` | integer | ID del proyecto a consultar |

**Headers Requeridos:**
```http
Authorization: Bearer {access_token}
```

**Request de Ejemplo:**
```http
GET https://kedikian.site/api/v1/client/proyectos/79
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response Exitoso (200 OK):**
```json
{
  "success": true,
  "message": "Proyecto obtenido exitosamente",
  "data": {
    "id": 79,
    "nombre": "HOTEL KING",
    "estado": "EN PROGRESO",
    "descripcion": "Retiro de pileta y nivelación",
    "fecha_inicio": "2026-02-18",
    "ubicacion": "San martin",
    "maquinas_asignadas": [
      {
        "nombre": "EXCAVADORA 2023 XCMG E60.",
        "horas_trabajadas": 21.0
      },
      {
        "nombre": "BOBCAT 2018 S650.",
        "horas_trabajadas": 9.0
      }
    ],
    "total_horas_maquinas": 30.0,
    "aridos_utilizados": [
      {
        "tipo": "Relleno",
        "cantidad": 150.0,
        "unidad": "m³",
        "cantidad_registros": 5
      }
    ],
    "total_aridos": 150.0
  },
  "total": 1
}
```

---

## 📦 Modelos de Datos

### Proyecto (ClientProjectView)

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `id` | integer | ID único del proyecto | `79` |
| `nombre` | string | Nombre del proyecto | `"HOTEL KING"` |
| `estado` | string | Estado del proyecto | `"EN PROGRESO"` o `"COMPLETADO"` |
| `descripcion` | string | Descripción detallada | `"Retiro de pileta y nivelación"` |
| `fecha_inicio` | string | Fecha de inicio (YYYY-MM-DD) | `"2026-02-18"` |
| `ubicacion` | string | Ubicación física del proyecto | `"San martin"` |
| `maquinas_asignadas` | array | Lista de máquinas asignadas | Ver tabla Máquina |
| `total_horas_maquinas` | float | Total de horas trabajadas | `30.0` |
| `aridos_utilizados` | array | Lista de áridos utilizados | Ver tabla Árido |
| `total_aridos` | float | Total de áridos en m³ | `175.0` |

### Máquina (ClientMaquinaView)

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `nombre` | string | Nombre/modelo de la máquina | `"EXCAVADORA 2023 XCMG E60."` |
| `horas_trabajadas` | float | Total de horas trabajadas | `21.0` |

### Árido (ClientAridoView)

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `tipo` | string | Tipo de árido | `"Relleno"`, `"Arena"`, `"Piedra"` |
| `cantidad` | float | Cantidad total utilizada | `150.0` |
| `unidad` | string | Unidad de medida | `"m³"` |
| `cantidad_registros` | integer | Número de entregas | `5` |

---

## ⚠️ Códigos de Error

### 200 OK
Petición exitosa.

### 401 Unauthorized
```json
{
  "detail": "Token inválido o expirado"
}
```

**Causa:** El token JWT es inválido o ha expirado.
**Solución:** Generar un nuevo token usando el endpoint `/auth-external/token`.

---

### 403 Forbidden
```json
{
  "detail": "Secreto inválido. Acceso denegado."
}
```

**Causa:** El secreto compartido es incorrecto.
**Solución:** Verificar las credenciales proporcionadas por Kedikian.

---

### 404 Not Found
```json
{
  "detail": "Proyecto con ID 999 no encontrado o no está activo"
}
```

**Causa:** El proyecto no existe o no está en estado activo.
**Solución:** Verificar el ID del proyecto o consultar la lista de proyectos activos.

---

### 500 Internal Server Error
```json
{
  "detail": "Error al obtener proyectos: ..."
}
```

**Causa:** Error interno del servidor.
**Solución:** Contactar al equipo de Kedikian.

---

## 💻 Ejemplos de Integración

### JavaScript / TypeScript (Fetch)

```javascript
// 1. Obtener Token
async function getToken() {
  const response = await fetch(
    'https://kedikian.site/api/v1/auth-external/token?system_name=terrasoftarg&secret=terrasoft_kedikian_shared_secret_2025',
    {
      method: 'POST'
    }
  );
  const data = await response.json();
  return data.access_token;
}

// 2. Obtener Todos los Proyectos
async function getAllProyectos() {
  const token = await getToken();

  const response = await fetch(
    'https://kedikian.site/api/v1/client/proyectos',
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );

  const data = await response.json();
  return data.data; // Array de proyectos
}

// 3. Obtener Proyecto por ID
async function getProyectoById(id) {
  const token = await getToken();

  const response = await fetch(
    `https://kedikian.site/api/v1/client/proyectos/${id}`,
    {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );

  const data = await response.json();
  return data.data; // Proyecto individual
}

// Uso
getAllProyectos().then(proyectos => {
  console.log('Proyectos:', proyectos);
});

getProyectoById(79).then(proyecto => {
  console.log('Proyecto:', proyecto);
});
```

---

### JavaScript / TypeScript (Axios)

```javascript
import axios from 'axios';

const BASE_URL = 'https://kedikian.site/api';
const SYSTEM_NAME = 'terrasoftarg';
const SECRET = 'terrasoft_kedikian_shared_secret_2025';

// Cliente Axios configurado
const apiClient = axios.create({
  baseURL: BASE_URL
});

// 1. Obtener Token
async function getToken() {
  const response = await apiClient.post('/v1/auth-external/token', null, {
    params: {
      system_name: SYSTEM_NAME,
      secret: SECRET
    }
  });
  return response.data.access_token;
}

// 2. Interceptor para agregar token automáticamente
apiClient.interceptors.request.use(async (config) => {
  const token = await getToken();
  config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// 3. Obtener Todos los Proyectos
export async function getAllProyectos() {
  const response = await apiClient.get('/v1/client/proyectos');
  return response.data.data;
}

// 4. Obtener Proyecto por ID
export async function getProyectoById(id) {
  const response = await apiClient.get(`/v1/client/proyectos/${id}`);
  return response.data.data;
}
```

---

### React Example

```typescript
// hooks/useProyectos.ts
import { useState, useEffect } from 'react';

interface Proyecto {
  id: number;
  nombre: string;
  estado: string;
  descripcion: string;
  fecha_inicio: string;
  ubicacion: string;
  maquinas_asignadas: Maquina[];
  total_horas_maquinas: number;
  aridos_utilizados: Arido[];
  total_aridos: number;
}

interface Maquina {
  nombre: string;
  horas_trabajadas: number;
}

interface Arido {
  tipo: string;
  cantidad: number;
  unidad: string;
  cantidad_registros: number;
}

export function useProyectos() {
  const [proyectos, setProyectos] = useState<Proyecto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchProyectos() {
      try {
        // Obtener token
        const tokenRes = await fetch(
          'https://kedikian.site/api/v1/auth-external/token?system_name=terrasoftarg&secret=terrasoft_kedikian_shared_secret_2025',
          { method: 'POST' }
        );
        const { access_token } = await tokenRes.json();

        // Obtener proyectos
        const proyectosRes = await fetch(
          'https://kedikian.site/api/v1/client/proyectos',
          {
            headers: {
              'Authorization': `Bearer ${access_token}`
            }
          }
        );
        const data = await proyectosRes.json();
        setProyectos(data.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchProyectos();
  }, []);

  return { proyectos, loading, error };
}

// Componente
export function ProyectosList() {
  const { proyectos, loading, error } = useProyectos();

  if (loading) return <div>Cargando...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {proyectos.map(proyecto => (
        <div key={proyecto.id}>
          <h2>{proyecto.nombre}</h2>
          <p>{proyecto.descripcion}</p>
          <p>Total horas: {proyecto.total_horas_maquinas}h</p>
          <p>Total áridos: {proyecto.total_aridos} m³</p>
        </div>
      ))}
    </div>
  );
}
```

---

### Angular Example

```typescript
// services/proyectos.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, switchMap } from 'rxjs';

interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

interface ProyectosResponse {
  success: boolean;
  message: string;
  data: Proyecto[];
  total: number;
}

interface Proyecto {
  id: number;
  nombre: string;
  estado: string;
  descripcion: string;
  fecha_inicio: string;
  ubicacion: string;
  maquinas_asignadas: Maquina[];
  total_horas_maquinas: number;
  aridos_utilizados: Arido[];
  total_aridos: number;
}

@Injectable({
  providedIn: 'root'
})
export class ProyectosService {
  private baseUrl = 'https://kedikian.site/api';
  private systemName = 'terrasoftarg';
  private secret = 'terrasoft_kedikian_shared_secret_2025';

  constructor(private http: HttpClient) {}

  private getToken(): Observable<string> {
    return this.http.post<TokenResponse>(
      `${this.baseUrl}/v1/auth-external/token?system_name=${this.systemName}&secret=${this.secret}`,
      null
    ).pipe(
      map(response => response.access_token)
    );
  }

  getAllProyectos(): Observable<Proyecto[]> {
    return this.getToken().pipe(
      switchMap(token => {
        const headers = new HttpHeaders({
          'Authorization': `Bearer ${token}`
        });
        return this.http.get<ProyectosResponse>(
          `${this.baseUrl}/v1/client/proyectos`,
          { headers }
        );
      }),
      map(response => response.data)
    );
  }

  getProyectoById(id: number): Observable<Proyecto> {
    return this.getToken().pipe(
      switchMap(token => {
        const headers = new HttpHeaders({
          'Authorization': `Bearer ${token}`
        });
        return this.http.get<ProyectosResponse>(
          `${this.baseUrl}/v1/client/proyectos/${id}`,
          { headers }
        );
      }),
      map(response => response.data)
    );
  }
}

// Componente
import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-proyectos',
  template: `
    <div *ngFor="let proyecto of proyectos">
      <h2>{{ proyecto.nombre }}</h2>
      <p>{{ proyecto.descripcion }}</p>
      <p>Total horas: {{ proyecto.total_horas_maquinas }}h</p>
    </div>
  `
})
export class ProyectosComponent implements OnInit {
  proyectos: Proyecto[] = [];

  constructor(private proyectosService: ProyectosService) {}

  ngOnInit() {
    this.proyectosService.getAllProyectos().subscribe(
      proyectos => this.proyectos = proyectos
    );
  }
}
```

---

## 📝 Notas Importantes

### Seguridad
- ✅ Siempre usar **HTTPS**
- ✅ Nunca exponer el `secret` en el frontend
- ✅ Implementar refresh de token antes de que expire
- ✅ Manejar errores de autenticación apropiadamente

### Rendimiento
- 💡 Cachear el token mientras sea válido (60 minutos)
- 💡 Implementar retry logic para errores 5xx
- 💡 Usar loading states en el frontend

### Manejo de Errores
```javascript
async function fetchWithErrorHandling() {
  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      if (response.status === 401) {
        // Token expirado, obtener nuevo token
        return refreshTokenAndRetry();
      }
      throw new Error(`Error ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error:', error);
    throw error;
  }
}
```

### CORS
La API tiene CORS habilitado para los siguientes orígenes:
- `http://localhost:4200`
- `http://localhost:3000`
- `http://kedikian.site`
- `https://kedikian.site`

Si necesitas agregar otro origen, contacta al equipo de Kedikian.

---

## 🆘 Soporte

**Contacto Técnico:**
- Email: soporte@kedikian.site
- Documentación OpenAPI: `https://kedikian.site/api/docs`
- ReDoc: `https://kedikian.site/api/redoc`

---

## 📄 Changelog

### v1.0.0 (Marzo 2026)
- ✅ Lanzamiento inicial
- ✅ Endpoints de proyectos
- ✅ Autenticación JWT
- ✅ Soporte para máquinas y áridos

---

**© 2026 Kedikian - Todos los derechos reservados**
