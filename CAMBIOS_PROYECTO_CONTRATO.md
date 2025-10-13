# Cambios Implementados - Proyecto y ContratoArchivo

## Resumen de Cambios

Se han implementado los siguientes cambios en el backend para soportar la funcionalidad de contratos con archivos:

### 1. Modelos de Base de Datos

#### Modelo Proyecto (`app/db/models/proyecto.py`)
- ✅ Cambiado `fecha_fin` de `DateTime` a `Date` y hecho opcional
- ✅ `contrato_id` ya era opcional (no se modificó)
- ✅ Agregado campo `contrato_file_path` (String 500, opcional)
- ✅ Agregada relación `contrato_archivos` con modelo ContratoArchivo

#### Nuevo Modelo ContratoArchivo (`app/db/models/contrato.py`)
- ✅ Creada tabla `contrato_archivos` con campos:
  - `id` (Primary Key)
  - `proyecto_id` (Foreign Key a proyecto)
  - `nombre_archivo` (String 255)
  - `ruta_archivo` (String 500)
  - `tipo_archivo` (String 50)
  - `tamaño_archivo` (BigInteger)
  - `fecha_subida` (DateTime, default UTC now)
- ✅ Relación con Proyecto configurada

### 2. Esquemas Pydantic (`app/schemas/schemas.py`)

#### Esquemas ContratoArchivo
- ✅ `ContratoArchivoBase`
- ✅ `ContratoArchivoCreate`
- ✅ `ContratoArchivoResponse`

#### Esquemas Proyecto Actualizados
- ✅ `ProyectoBase` actualizado con nuevos campos
- ✅ `ProyectoCreate` y `ProyectoUpdate` actualizados
- ✅ `ProyectoResponse` con relación a `contrato_archivos`

### 3. Endpoints de API (`app/routers/proyectos_router.py`)

#### Nuevos Endpoints
- ✅ `POST /proyectos/{proyecto_id}/contrato` - Subir contrato
- ✅ `GET /proyectos/{proyecto_id}/contrato` - Descargar contrato

#### Endpoint Actualizado
- ✅ `GET /proyectos/` - Agregado parámetro `solo_activos` para filtrar por estado

### 4. Configuración de Archivos Estáticos (`main.py`)
- ✅ Configurado directorio `uploads` para archivos de contratos
- ✅ Middleware para servir archivos estáticos en `/uploads`

### 5. Migración de Base de Datos
- ✅ Script SQL: `migrations/update_proyecto_contrato_archivos.sql`
- ✅ Script Python: `migrate_proyecto_contrato_archivos.py`

## Funcionalidades Implementadas

### Subir Contrato
```http
POST /v1/proyectos/{proyecto_id}/contrato
Content-Type: multipart/form-data

archivo: [archivo PDF/DOC/DOCX]
```

**Validaciones:**
- Proyecto debe existir
- Tipos de archivo permitidos: PDF, DOC, DOCX
- Generación de nombre único para evitar conflictos

### Descargar Contrato
```http
GET /v1/proyectos/{proyecto_id}/contrato
```

**Respuesta:** Archivo del contrato

### Obtener Proyectos con Filtro
```http
GET /v1/proyectos/?solo_activos=true&skip=0&limit=100
```

**Parámetros:**
- `solo_activos`: Filtrar solo proyectos activos
- `skip`: Paginación (offset)
- `limit`: Límite de resultados

## Estructura de Archivos

```
uploads/
└── contratos/
    └── {proyecto_id}/
        └── contrato_{proyecto_id}_{timestamp}.{ext}
```

## Próximos Pasos

1. **Ejecutar migración:**
   ```bash
   python migrate_proyecto_contrato_archivos.py
   ```

2. **Reiniciar servidor** para aplicar cambios

3. **Probar endpoints** con el frontend

## Notas Importantes

- Los archivos se almacenan en `uploads/contratos/{proyecto_id}/`
- Se generan nombres únicos para evitar conflictos
- Se valida el tipo de archivo antes de guardar
- La relación entre Proyecto y ContratoArchivo es 1:N
- Se mantiene compatibilidad con el modelo existente
