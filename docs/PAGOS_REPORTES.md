# Sistema de Pagos de Reportes de Cuenta Corriente

## Descripción

Sistema para registrar y gestionar pagos de reportes de cuenta corriente. Permite:
- Registrar pagos parciales o totales
- Actualización automática del estado del reporte
- Consultar historial de pagos por reporte

## Tabla de Base de Datos

### `pagos_reportes`

```sql
CREATE TABLE pagos_reportes (
    id SERIAL PRIMARY KEY,
    reporte_id INTEGER REFERENCES reportes_cuenta_corriente(id) ON DELETE CASCADE,
    monto DECIMAL(12,2) NOT NULL,
    fecha DATE NOT NULL,
    observaciones TEXT,
    fecha_registro TIMESTAMP DEFAULT NOW()
);
```

## Estados del Reporte

El sistema actualiza automáticamente el estado del reporte al registrar pagos:

| Estado | Condición |
|--------|-----------|
| `PENDIENTE` | total_pagado = 0 |
| `PARCIAL` | 0 < total_pagado < importe_total |
| `PAGADO` | total_pagado >= importe_total |

## Endpoints

### POST `/cuenta-corriente/reportes/{reporte_id}/pagos`

Registra un nuevo pago para un reporte.

**Request Body:**
```json
{
  "monto": 50000.00,
  "fecha": "2026-02-26",
  "observaciones": "Pago inicial - 50% del total"
}
```

**Response (201 Created):**
```json
{
  "pago": {
    "id": 1,
    "reporte_id": 5,
    "monto": 50000.00,
    "fecha": "2026-02-26",
    "observaciones": "Pago inicial - 50% del total",
    "fecha_registro": "2026-02-26T10:30:00"
  },
  "reporte_actualizado": {
    "id": 5,
    "proyecto_id": 10,
    "estado": "parcial",
    "importe_total": 100000.00,
    ...
  },
  "total_pagado": 50000.00,
  "saldo_pendiente": 50000.00
}
```

**Lógica de actualización:**
1. Inserta el pago en `pagos_reportes`
2. Suma todos los pagos del reporte → `total_pagado`
3. Actualiza el estado del reporte:
   - Si `total_pagado >= importe_total` → `estado = PAGADO`
   - Si `total_pagado > 0` → `estado = PARCIAL`
   - Si `total_pagado = 0` → `estado = PENDIENTE`
4. Si el reporte pasa a PAGADO y no tiene `fecha_pago`, la asigna

### GET `/cuenta-corriente/reportes/{reporte_id}/pagos`

Lista todos los pagos de un reporte (ordenados por fecha de registro descendente).

**Response (200 OK):**
```json
[
  {
    "id": 2,
    "reporte_id": 5,
    "monto": 50000.00,
    "fecha": "2026-02-28",
    "observaciones": "Pago final",
    "fecha_registro": "2026-02-28T15:00:00"
  },
  {
    "id": 1,
    "reporte_id": 5,
    "monto": 50000.00,
    "fecha": "2026-02-26",
    "observaciones": "Pago inicial - 50% del total",
    "fecha_registro": "2026-02-26T10:30:00"
  }
]
```

## Ejemplo de Uso

### Flujo completo de pagos

```python
# 1. Crear un reporte de cuenta corriente
# POST /cuenta-corriente/reportes
{
  "proyecto_id": 10,
  "periodo_inicio": "2026-02-01",
  "periodo_fin": "2026-02-28",
  "observaciones": "Reporte febrero 2026"
}
# Response: reporte con id=5, importe_total=100000.00, estado="pendiente"

# 2. Registrar primer pago (50%)
# POST /cuenta-corriente/reportes/5/pagos
{
  "monto": 50000.00,
  "fecha": "2026-02-26",
  "observaciones": "Anticipo 50%"
}
# Response: total_pagado=50000, saldo_pendiente=50000, estado="parcial"

# 3. Registrar segundo pago (50% restante)
# POST /cuenta-corriente/reportes/5/pagos
{
  "monto": 50000.00,
  "fecha": "2026-02-28",
  "observaciones": "Pago final"
}
# Response: total_pagado=100000, saldo_pendiente=0, estado="pagado"

# 4. Consultar historial de pagos
# GET /cuenta-corriente/reportes/5/pagos
# Response: Lista con 2 pagos
```

## Migración de Base de Datos

Para crear la tabla en PostgreSQL:

```bash
# Opción 1: Ejecutar el script Python
python migrations/run_pagos_migration.py

# Opción 2: Ejecutar SQL directamente
psql -U postgres -d nombre_bd -f migrations/create_pagos_reportes.sql
```

## Validaciones

- ✅ El monto del pago debe ser mayor a 0
- ✅ La fecha del pago es obligatoria
- ✅ El reporte debe existir (HTTP 404 si no existe)
- ✅ Los pagos se eliminan automáticamente si se elimina el reporte (CASCADE)

## Características Técnicas

- **Modelo ORM:** SQLAlchemy con relación bidireccional `ReporteCuentaCorriente.pagos`
- **Schemas:** Pydantic con validación automática
- **Transacciones:** Garantiza consistencia (pago + actualización de estado en una transacción)
- **Índices:** Optimizados para consultas por `reporte_id`, `fecha` y `fecha_registro`
- **Precisión:** Tipo `DECIMAL(12,2)` para evitar errores de redondeo
