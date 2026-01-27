# Sistema de Cuenta Corriente - Documentación

## 📋 Descripción General

Se ha implementado un sistema completo de **Cuenta Corriente** que permite generar reportes de costos de proyectos basados en:
- **Áridos entregados**: Cantidad (m³) × precio por m³
- **Horas de máquinas**: Total de horas × tarifa por hora

El sistema calcula automáticamente los importes y genera reportes que pueden exportarse a Excel y PDF.

---

## 🗂️ Archivos Creados

### 1. Modelo de Datos
**Archivo:** `app/db/models/reporte_cuenta_corriente.py`

Modelo SQLAlchemy para la tabla `reportes_cuenta_corriente` con los siguientes campos:
- `id`: ID único del reporte
- `proyecto_id`: Referencia al proyecto (FK)
- `periodo_inicio` / `periodo_fin`: Rango de fechas del reporte
- `total_aridos`: Total m³ de áridos entregados
- `total_horas`: Total de horas de máquinas
- `importe_aridos`: Importe calculado de áridos
- `importe_horas`: Importe calculado de horas
- `importe_total`: Suma total
- `estado`: "pendiente" o "pagado"
- `fecha_generacion`: Timestamp de creación
- `observaciones`: Notas opcionales
- `numero_factura`: Número de factura asociado
- `fecha_pago`: Fecha de pago (si aplica)

### 2. Schemas Pydantic
**Archivo:** `app/schemas/schemas.py`

Se agregaron los siguientes schemas (líneas 996-1074):

#### Schemas de Reporte
- `ReporteCuentaCorrienteBase`: Base con todos los campos
- `ReporteCuentaCorrienteCreate`: Para crear nuevos reportes
- `ReporteCuentaCorrienteUpdate`: Para actualizar estado y campos opcionales
- `ReporteCuentaCorrienteOut`: Para respuestas API con todos los campos

#### Schemas de Resumen
- `DetalleAridoConPrecio`: Detalle de un tipo de árido con precio calculado
- `DetalleHorasConTarifa`: Detalle de horas de una máquina con tarifa
- `ResumenProyectoSchema`: Resumen completo con áridos, horas e importes

#### Schemas de Configuración
- `PrecioAridoSchema`: Precio por m³ de un tipo de árido
- `TarifaMaquinaSchema`: Tarifa por hora de una máquina

### 3. Servicio de Negocio
**Archivo:** `app/services/cuenta_corriente_service.py`

Lógica de negocio con las siguientes funciones:

#### Configuración de Precios y Tarifas
```python
PRECIOS_ARIDOS = {
    "Arena Fina": 8500.0,
    "Granza": 7500.0,
    "Arena Común": 7000.0,
    "Relleno": 6000.0,
    "Tierra Negra": 9000.0,
    "Piedra": 12000.0,
    "0.20": 8000.0,
    "Blinder": 10000.0,
    "Arena Lavada": 8800.0
}

TARIFAS_MAQUINAS = {
    "default": 15000.0,
    "Excavadora": 18000.0,
    "Retroexcavadora": 16000.0,
    "Cargadora": 17000.0,
    "Motoniveladora": 20000.0,
    "Compactadora": 14000.0,
    "Camión": 12000.0
}
```

#### Funciones Principales
- `get_resumen_proyecto()`: Calcula resumen de áridos y horas con precios
- `get_reportes()`: Lista todos los reportes (con filtro opcional por proyecto)
- `get_reporte()`: Obtiene un reporte específico
- `create_reporte()`: Crea nuevo reporte con cálculos automáticos
- `update_reporte_estado()`: Actualiza estado del reporte
- `delete_reporte()`: Elimina un reporte
- `get_todos_precios_aridos()`: Lista todos los precios de áridos
- `get_tarifa_maquina_por_id()`: Obtiene tarifa de una máquina específica

### 4. Router (Endpoints API)
**Archivo:** `app/routers/cuenta_corriente_router.py`

Endpoints disponibles bajo el prefijo `/api/v1/cuenta-corriente`:

#### Precios y Tarifas
- **GET** `/aridos/precios`
  - Obtiene todos los precios de áridos disponibles
  - Respuesta: `List[PrecioAridoSchema]`

- **GET** `/maquinas/{maquina_id}/tarifa`
  - Obtiene la tarifa por hora de una máquina
  - Respuesta: `TarifaMaquinaSchema`

#### Resumen de Proyecto
- **GET** `/proyectos/{proyecto_id}/resumen`
  - Query params: `periodo_inicio`, `periodo_fin` (fechas en formato YYYY-MM-DD)
  - Obtiene resumen detallado con áridos y horas calculadas
  - Respuesta: `ResumenProyectoSchema`

#### Reportes
- **GET** `/reportes`
  - Query param opcional: `proyecto_id`
  - Lista todos los reportes generados
  - Respuesta: `List[ReporteCuentaCorrienteOut]`

- **GET** `/reportes/{reporte_id}`
  - Obtiene un reporte específico
  - Respuesta: `ReporteCuentaCorrienteOut`

- **POST** `/reportes`
  - Crea un nuevo reporte (calcula automáticamente los importes)
  - Body: `ReporteCuentaCorrienteCreate`
  - Respuesta: `ReporteCuentaCorrienteOut` (status 201)

- **PUT** `/reportes/{reporte_id}/estado`
  - Actualiza el estado del reporte (pendiente/pagado)
  - Body: `ReporteCuentaCorrienteUpdate`
  - Respuesta: `ReporteCuentaCorrienteOut`

- **DELETE** `/reportes/{reporte_id}`
  - Elimina un reporte
  - Respuesta: 204 No Content

#### Exportación
- **GET** `/reportes/{reporte_id}/excel`
  - Exporta el reporte a formato Excel (.xlsx)
  - Respuesta: Archivo Excel descargable
  - Hojas incluidas:
    - Información general
    - Detalle de áridos
    - Detalle de horas de máquinas
    - Totales

- **GET** `/reportes/{reporte_id}/pdf`
  - Exporta el reporte a formato PDF
  - Respuesta: Archivo PDF descargable
  - Incluye tablas formateadas con totales y observaciones

### 5. Scripts de Migración

#### Script SQL
**Archivo:** `migrations/create_reportes_cuenta_corriente.sql`

Script SQL para PostgreSQL que:
- Crea la tabla `reportes_cuenta_corriente`
- Agrega constraints de validación
- Crea índices para optimizar consultas
- Crea trigger para actualizar campo `updated` automáticamente
- Agrega comentarios descriptivos

#### Script Python
**Archivo:** `migrate_reportes_cuenta_corriente.py`

Script ejecutable que:
- Detecta automáticamente el tipo de base de datos (PostgreSQL/SQLite)
- Crea la tabla usando SQLAlchemy ORM
- Crea índices y triggers (si aplica)
- Verifica que la migración se haya aplicado correctamente
- Proporciona output detallado del proceso

---

## 🚀 Instalación y Configuración

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

Se agregaron las siguientes dependencias:
- `reportlab`: Para generación de PDFs
- `pydantic-settings`: Para configuración (si no estaba)

### 2. Ejecutar Migración

```bash
# Opción 1: Usando Python directamente
python migrate_reportes_cuenta_corriente.py

# Opción 2: Si el script es ejecutable
./migrate_reportes_cuenta_corriente.py
```

El script creará:
- Tabla `reportes_cuenta_corriente`
- Índices optimizados
- Triggers de actualización (PostgreSQL)

### 3. Reiniciar el Servidor

```bash
# Desarrollo
uvicorn main:app --reload --port 8000

# Producción (con Gunicorn)
gunicorn -c gunicorn.config.py main:app
```

### 4. Verificar Endpoints

Accede a la documentación interactiva:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Busca la sección **"Cuenta Corriente"** en la documentación.

---

## 📖 Ejemplos de Uso

### 1. Obtener Resumen de Proyecto

```bash
curl -X GET "http://localhost:8000/api/v1/cuenta-corriente/proyectos/1/resumen?periodo_inicio=2025-01-01&periodo_fin=2025-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Respuesta:**
```json
{
  "proyecto_id": 1,
  "proyecto_nombre": "Proyecto Ejemplo",
  "periodo_inicio": "2025-01-01",
  "periodo_fin": "2025-01-31",
  "aridos": [
    {
      "tipo_arido": "Arena Fina",
      "cantidad": 150.5,
      "precio_unitario": 8500.0,
      "importe": 1279250.0
    }
  ],
  "total_aridos_m3": 150.5,
  "total_importe_aridos": 1279250.0,
  "horas_maquinas": [
    {
      "maquina_id": 1,
      "maquina_nombre": "Excavadora",
      "total_horas": 120.0,
      "tarifa_hora": 18000.0,
      "importe": 2160000.0
    }
  ],
  "total_horas": 120.0,
  "total_importe_horas": 2160000.0,
  "importe_total": 3439250.0
}
```

### 2. Crear un Nuevo Reporte

```bash
curl -X POST "http://localhost:8000/api/v1/cuenta-corriente/reportes" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "proyecto_id": 1,
    "periodo_inicio": "2025-01-01",
    "periodo_fin": "2025-01-31",
    "observaciones": "Reporte mensual de enero"
  }'
```

**Respuesta:**
```json
{
  "id": 1,
  "proyecto_id": 1,
  "periodo_inicio": "2025-01-01",
  "periodo_fin": "2025-01-31",
  "total_aridos": 150.5,
  "total_horas": 120.0,
  "importe_aridos": 1279250.0,
  "importe_horas": 2160000.0,
  "importe_total": 3439250.0,
  "estado": "pendiente",
  "fecha_generacion": "2025-01-27T10:30:00",
  "observaciones": "Reporte mensual de enero",
  "numero_factura": null,
  "fecha_pago": null,
  "created": "2025-01-27T10:30:00",
  "updated": null
}
```

### 3. Marcar Reporte como Pagado

```bash
curl -X PUT "http://localhost:8000/api/v1/cuenta-corriente/reportes/1/estado" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "pagado",
    "numero_factura": "FAC-2025-001",
    "fecha_pago": "2025-02-15"
  }'
```

### 4. Exportar a Excel

```bash
curl -X GET "http://localhost:8000/api/v1/cuenta-corriente/reportes/1/excel" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o reporte_proyecto_enero.xlsx
```

### 5. Exportar a PDF

```bash
curl -X GET "http://localhost:8000/api/v1/cuenta-corriente/reportes/1/pdf" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o reporte_proyecto_enero.pdf
```

---

## 🔧 Configuración de Precios y Tarifas

Los precios de áridos y tarifas de máquinas están **hardcodeados** en el archivo `cuenta_corriente_service.py`.

### Modificar Precios de Áridos

Editar el diccionario `PRECIOS_ARIDOS` en `app/services/cuenta_corriente_service.py`:

```python
PRECIOS_ARIDOS: Dict[str, float] = {
    "Arena Fina": 8500.0,      # Cambiar según necesidad
    "Granza": 7500.0,
    # ... más tipos
}
```

### Modificar Tarifas de Máquinas

Editar el diccionario `TARIFAS_MAQUINAS`:

```python
TARIFAS_MAQUINAS: Dict[str, float] = {
    "default": 15000.0,         # Tarifa por defecto
    "Excavadora": 18000.0,      # Tarifa específica por tipo
    # ... más tipos
}
```

### Futuras Mejoras

Para una solución más flexible, se puede crear una tabla de configuración en la base de datos:
- `configuracion_precios_aridos` (tipo_arido, precio, fecha_vigencia)
- `configuracion_tarifas_maquinas` (maquina_id, tarifa, fecha_vigencia)

---

## 🗃️ Estructura de la Base de Datos

### Tabla: `reportes_cuenta_corriente`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | SERIAL | ID único (PK) |
| `proyecto_id` | INTEGER | ID del proyecto (FK) |
| `periodo_inicio` | DATE | Fecha inicio del período |
| `periodo_fin` | DATE | Fecha fin del período |
| `total_aridos` | FLOAT | Total m³ de áridos |
| `total_horas` | FLOAT | Total horas de máquinas |
| `importe_aridos` | NUMERIC(12,2) | Importe total áridos |
| `importe_horas` | NUMERIC(12,2) | Importe total horas |
| `importe_total` | NUMERIC(12,2) | Importe total del reporte |
| `estado` | VARCHAR(20) | "pendiente" o "pagado" |
| `fecha_generacion` | TIMESTAMP | Fecha de creación |
| `observaciones` | TEXT | Notas opcionales |
| `numero_factura` | VARCHAR(50) | Número de factura |
| `fecha_pago` | DATE | Fecha de pago |
| `created` | TIMESTAMP TZ | Timestamp de creación |
| `updated` | TIMESTAMP TZ | Timestamp de actualización |

### Índices Creados

- `idx_reportes_cc_proyecto_id`: Búsqueda por proyecto
- `idx_reportes_cc_periodo`: Búsqueda por rango de fechas
- `idx_reportes_cc_fecha_generacion`: Ordenamiento por fecha de generación
- `idx_reportes_cc_estado`: Filtrado por estado

### Constraints

- Foreign Key: `proyecto_id` → `proyecto(id)` ON DELETE CASCADE
- Check: `estado` IN ('pendiente', 'pagado')
- Check: `periodo_fin >= periodo_inicio`
- Check: Importes >= 0

---

## 📊 Flujo de Trabajo

1. **Usuario consulta resumen de proyecto**
   - Endpoint: `GET /proyectos/{id}/resumen`
   - El sistema consulta entregas de áridos y horas de máquinas del período
   - Calcula importes usando precios y tarifas configurados
   - Retorna resumen detallado

2. **Usuario genera reporte formal**
   - Endpoint: `POST /reportes`
   - El sistema crea un registro permanente del reporte
   - Estado inicial: "pendiente"
   - Se pueden hacer múltiples reportes para el mismo proyecto/período

3. **Usuario exporta reporte**
   - Endpoint: `GET /reportes/{id}/excel` o `/reportes/{id}/pdf`
   - El sistema genera el archivo con formato profesional
   - Incluye todos los detalles y totales

4. **Usuario marca como pagado**
   - Endpoint: `PUT /reportes/{id}/estado`
   - Cambia estado a "pagado"
   - Registra número de factura y fecha de pago

---

## ✅ Testing

### Verificar Instalación

```bash
# 1. Verificar que la tabla existe
psql -d tu_base_de_datos -c "\d reportes_cuenta_corriente"

# 2. Verificar endpoints
curl http://localhost:8000/api/v1/cuenta-corriente/aridos/precios

# 3. Verificar en Swagger UI
# Ir a http://localhost:8000/docs
# Buscar sección "Cuenta Corriente"
```

### Test Completo de Flujo

```python
# Ver archivo de test (si lo necesitas, puedo crearlo)
# test_cuenta_corriente.py
```

---

## 📝 Notas Importantes

1. **Autenticación**: Todos los endpoints requieren autenticación JWT (excepto si se modifica el código)

2. **Cálculos**: Los importes se calculan automáticamente al crear el reporte, basados en:
   - Entregas de áridos registradas en `entrega_arido`
   - Horas de máquinas registradas en `reporte_laboral`

3. **Períodos**: Asegúrate de que las fechas de entregas y reportes laborales estén dentro del período del reporte

4. **Exportación**: Los archivos PDF y Excel se generan en memoria (no se guardan en disco)

5. **Precios históricos**: Los precios actuales se aplican al momento de generar el reporte. Si se cambian los precios, no afectará reportes ya generados.

---

## 🔮 Mejoras Futuras Sugeridas

1. **Tabla de Configuración de Precios**
   - Crear tabla `configuracion_precios` con vigencia por fecha
   - Historial de cambios de precios
   - API para actualizar precios desde el frontend

2. **Reportes Recurrentes**
   - Generación automática de reportes mensuales
   - Notificaciones por email

3. **Dashboard de Cuenta Corriente**
   - Vista general de reportes pendientes/pagados
   - Gráficos de importes por proyecto/mes

4. **Validaciones Adicionales**
   - Validar que no se solapen períodos de reportes para el mismo proyecto
   - Alertas de reportes pendientes de pago

5. **Exportación a Otros Formatos**
   - CSV
   - Google Sheets
   - Sistema de facturación externo

---

## 🆘 Troubleshooting

### Error: "Tabla no existe"
```bash
# Ejecutar migración
python migrate_reportes_cuenta_corriente.py
```

### Error: "ModuleNotFoundError: No module named 'reportlab'"
```bash
# Instalar dependencias
pip install -r requirements.txt
```

### Error: "No se pueden calcular importes"
- Verificar que existan entregas de áridos y reportes laborales en el período
- Verificar que los tipos de áridos coincidan con los configurados en `PRECIOS_ARIDOS`
- Verificar que las máquinas tengan nombres configurados en `TARIFAS_MAQUINAS` (o usar tarifa default)

### Error 404 en endpoints
- Verificar que el router esté registrado en `main.py`
- Reiniciar el servidor
- Verificar el prefijo correcto: `/api/v1/cuenta-corriente/...`

---

## 📞 Contacto y Soporte

Para dudas o problemas con el sistema de Cuenta Corriente, contactar al equipo de desarrollo.

---

**Versión:** 1.0.0
**Fecha:** 27 de Enero de 2025
**Autor:** Sistema generado con Claude Code
