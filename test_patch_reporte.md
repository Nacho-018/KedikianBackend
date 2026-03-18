# Test del Endpoint PATCH /api/cuenta-corriente/reportes/{id}

## Descripción
Endpoint para editar campos específicos de un reporte de cuenta corriente.

## Requisitos
- Usuario autenticado con rol de **administrador**
- Token JWT válido en el header Authorization

## Endpoint
```
PATCH /api/cuenta-corriente/reportes/{id}
```

## Headers
```
Authorization: Bearer {token}
Content-Type: application/json
```

## Request Body (todos los campos opcionales)
```json
{
  "observaciones": "Texto opcional de observaciones",
  "numero_factura": "FC-0001234",
  "fecha_pago": "2024-02-15"
}
```

## Validaciones

### 1. Autenticación y Autorización
- ✅ Token JWT válido requerido
- ✅ Usuario debe tener rol "administrador"
- ❌ HTTP 401 si no está autenticado
- ❌ HTTP 403 si no es administrador

### 2. Existencia del Reporte
- ✅ El reporte debe existir
- ❌ HTTP 404 si no existe

### 3. Validación de fecha_pago
- ✅ Formato YYYY-MM-DD
- ✅ Debe ser >= fecha_generacion del reporte
- ❌ HTTP 400 si el formato es inválido
- ❌ HTTP 400 si fecha_pago < fecha_generacion

### 4. Actualización Parcial
- ✅ Solo se actualizan los campos enviados
- ✅ Campos no enviados mantienen su valor actual
- ✅ Se puede enviar null para limpiar campos opcionales

## Response (HTTP 200)
```json
{
  "id": 123,
  "proyecto_id": 45,
  "periodo_inicio": "2024-01-01",
  "periodo_fin": "2024-01-31",
  "total_aridos": 150.5,
  "total_horas": 80.0,
  "importe_aridos": 450000.00,
  "importe_horas": 320000.00,
  "importe_total": 770000.00,
  "estado": "pendiente",
  "fecha_generacion": "2024-02-01T10:30:00",
  "observaciones": "Actualizado desde frontend",
  "numero_factura": "FC-0001234",
  "fecha_pago": "2024-02-15",
  "created": "2024-02-01T10:30:00",
  "updated": "2024-02-20T14:00:00"
}
```

## Errores

### HTTP 400 - Bad Request
```json
{
  "detail": "La fecha de pago no puede ser anterior a la fecha de generación del reporte"
}
```

### HTTP 401 - Unauthorized
```json
{
  "detail": "No se pudo validar las credenciales"
}
```

### HTTP 403 - Forbidden
```json
{
  "detail": "No tiene permisos de administrador para realizar esta acción"
}
```

### HTTP 404 - Not Found
```json
{
  "detail": "Reporte no encontrado"
}
```

## Ejemplos de Uso

### 1. Actualizar solo observaciones
```bash
curl -X PATCH http://localhost:8000/api/cuenta-corriente/reportes/123 \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"observaciones": "Nueva observación"}'
```

### 2. Actualizar número de factura
```bash
curl -X PATCH http://localhost:8000/api/cuenta-corriente/reportes/123 \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"numero_factura": "FC-0001234"}'
```

### 3. Actualizar fecha de pago
```bash
curl -X PATCH http://localhost:8000/api/cuenta-corriente/reportes/123 \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"fecha_pago": "2024-02-15"}'
```

### 4. Actualizar múltiples campos
```bash
curl -X PATCH http://localhost:8000/api/cuenta-corriente/reportes/123 \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "observaciones": "Reporte actualizado",
    "numero_factura": "FC-0001234",
    "fecha_pago": "2024-02-15"
  }'
```

### 5. Limpiar un campo (enviar valor vacío)
```bash
curl -X PATCH http://localhost:8000/api/cuenta-corriente/reportes/123 \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"observaciones": ""}'
```

## Notas Importantes

1. **No cambia el estado**: Este endpoint NO modifica el campo `estado`. Para cambiar el estado usar:
   ```
   PUT /api/cuenta-corriente/reportes/{id}/estado
   ```

2. **No modifica importes**: Este endpoint NO modifica importes ni totales:
   - ❌ importe_total
   - ❌ importe_aridos
   - ❌ importe_horas
   - ❌ total_aridos
   - ❌ total_horas

3. **Actualiza timestamp**: El campo `updated` se actualiza automáticamente.

4. **Permite editar reportes PAGADOS**: Aunque el frontend muestra advertencia, el backend permite la edición.

## Testing

### Test Case 1: Actualización exitosa
```
PATCH /api/cuenta-corriente/reportes/1
Body: {"observaciones": "Test"}
Expected: HTTP 200, reporte actualizado
```

### Test Case 2: Usuario no administrador
```
PATCH /api/cuenta-corriente/reportes/1
Body: {"observaciones": "Test"}
User: sin rol administrador
Expected: HTTP 403 Forbidden
```

### Test Case 3: Fecha inválida
```
PATCH /api/cuenta-corriente/reportes/1
Body: {"fecha_pago": "2020-01-01"}
Expected: HTTP 400 (si fecha_generacion > 2020-01-01)
```

### Test Case 4: Reporte inexistente
```
PATCH /api/cuenta-corriente/reportes/99999
Body: {"observaciones": "Test"}
Expected: HTTP 404 Not Found
```

### Test Case 5: Body vacío
```
PATCH /api/cuenta-corriente/reportes/1
Body: {}
Expected: HTTP 200 (solo actualiza timestamp)
```
