"""
Router de API Externa
Endpoints REST para integración con sistemas externos (TerraSoft, etc.)
Requiere autenticación JWT mediante token Bearer
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.schemas.external_api import APIResponse, GenericRequest, TokenData
from app.security.jwt_auth import verify_token
from app.db.dependencies import get_db

# Importar servicios
from app.services import (
    maquina_service,
    proyecto_service,
    contrato_service,
    gasto_service,
    pago_service,
    producto_service,
    arrendamiento_service,
    movimiento_inventario_service,
    reporte_laboral_service,
    entrega_arido_service,
    usuario_service,
    mantenimiento_service,
    jornada_laboral_service,
    cuenta_corriente_service,
    cotizacion_service
)

router = APIRouter(
    prefix="/v1/external",
    tags=["API Externa"]
)

# Mapeo de recursos a funciones de servicio
RESOURCE_GET_MAP = {
    "maquinas": maquina_service.get_maquinas,
    "proyectos": proyecto_service.get_proyectos,
    "contratos": contrato_service.get_contratos,
    "gastos": gasto_service.get_gastos,
    "pagos": pago_service.get_pagos,
    "productos": producto_service.get_productos,
    "arrendamientos": arrendamiento_service.get_arrendamientos,
    "movimientos_inventario": movimiento_inventario_service.get_movimientos,
    "reportes_laborales": reporte_laboral_service.get_reportes,
    "entregas_arido": entrega_arido_service.get_entregas_aridos,
    "usuarios": usuario_service.get_usuarios,
    "mantenimientos": mantenimiento_service.get_mantenimientos,
    "jornadas_laborales": jornada_laboral_service.get_jornadas_laborales,
    "reportes_cuenta_corriente": cuenta_corriente_service.get_reportes,
    "cotizaciones": cotizacion_service.get_cotizaciones,
}

RESOURCE_GET_ONE_MAP = {
    "maquinas": maquina_service.get_maquina,
    "proyectos": proyecto_service.get_proyecto,
    "contratos": contrato_service.get_contrato,
    "gastos": gasto_service.get_gasto,
    "pagos": pago_service.get_pago,
    "productos": producto_service.get_producto,
    "arrendamientos": arrendamiento_service.get_arrendamiento,
    "movimientos_inventario": movimiento_inventario_service.get_movimiento,
    "reportes_laborales": reporte_laboral_service.get_reporte,
    "entregas_arido": entrega_arido_service.get_entrega_arido,
    "usuarios": usuario_service.get_usuario,
    "mantenimientos": mantenimiento_service.get_mantenimiento,
    "jornadas_laborales": jornada_laboral_service.get_jornada_laboral,
    "reportes_cuenta_corriente": cuenta_corriente_service.get_reporte_by_id,
    "cotizaciones": cotizacion_service.get_cotizacion,
}

RESOURCE_CREATE_MAP = {
    "maquinas": maquina_service.create_maquina,
    "proyectos": proyecto_service.create_proyecto,
    "contratos": contrato_service.create_contrato,
    "gastos": gasto_service.create_gasto,
    "pagos": pago_service.create_pago,
    "productos": producto_service.create_producto,
    "arrendamientos": arrendamiento_service.create_arrendamiento,
    "movimientos_inventario": movimiento_inventario_service.create_movimiento,
    "reportes_laborales": reporte_laboral_service.create_reporte,
    "entregas_arido": entrega_arido_service.create_entrega_arido,
    "mantenimientos": mantenimiento_service.create_mantenimiento,
    "cotizaciones": cotizacion_service.create_cotizacion,
}


@router.get("/recursos", response_model=APIResponse)
async def get_recursos(
    resource: str,
    id: Optional[int] = None,
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Obtiene recursos del sistema según el tipo solicitado

    Este endpoint permite consultar cualquier recurso disponible en el sistema.
    Si se proporciona un ID, retorna solo ese recurso específico.

    Args:
        resource: Tipo de recurso a consultar (ej: "maquinas", "proyectos", "contratos")
        id: ID específico del recurso (opcional)
        token: Token JWT validado (inyectado automáticamente)
        db: Sesión de base de datos (inyectada automáticamente)

    Returns:
        APIResponse con los datos solicitados

    Recursos disponibles:
        - maquinas
        - proyectos
        - contratos
        - gastos
        - pagos
        - productos
        - arrendamientos
        - movimientos_inventario
        - reportes_laborales
        - entregas_arido
        - usuarios
        - mantenimientos
        - jornadas_laborales
        - reportes_cuenta_corriente
        - cotizaciones

    Example:
        GET /api/v1/recursos?resource=maquinas
        GET /api/v1/recursos?resource=proyectos&id=5

        Response:
        {
            "success": true,
            "message": "Recursos obtenidos exitosamente",
            "data": [...],
            "total": 10
        }
    """
    try:
        # Si se solicita un recurso específico por ID
        if id is not None:
            if resource not in RESOURCE_GET_ONE_MAP:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Recurso '{resource}' no soportado"
                )

            get_one_func = RESOURCE_GET_ONE_MAP[resource]
            data = get_one_func(db, id)

            if data is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{resource} con ID {id} no encontrado"
                )

            return APIResponse(
                success=True,
                message=f"{resource} obtenido exitosamente",
                data=data,
                total=1
            )

        # Si se solicitan todos los recursos
        else:
            if resource not in RESOURCE_GET_MAP:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Recurso '{resource}' no soportado"
                )

            get_all_func = RESOURCE_GET_MAP[resource]
            data = get_all_func(db)

            return APIResponse(
                success=True,
                message=f"{resource} obtenidos exitosamente",
                data=data,
                total=len(data) if isinstance(data, list) else 1
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener {resource}: {str(e)}"
        )


@router.post("/recursos", response_model=APIResponse)
async def create_recurso(
    request: GenericRequest,
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Crea o actualiza un recurso en el sistema

    Este endpoint permite crear nuevos recursos de cualquier tipo soportado.
    Los datos deben enviarse en el payload según el schema del recurso.

    Args:
        request: Objeto GenericRequest con resource y payload
        token: Token JWT validado (inyectado automáticamente)
        db: Sesión de base de datos (inyectada automáticamente)

    Returns:
        APIResponse con el recurso creado

    Example:
        POST /api/v1/recursos
        Body:
        {
            "resource": "maquinas",
            "payload": {
                "nombre": "Excavadora CAT 320",
                "tipo": "Excavadora",
                "modelo": "CAT 320D",
                "horometro_inicial": 1000
            }
        }

        Response:
        {
            "success": true,
            "message": "maquinas creado exitosamente",
            "data": { ... }
        }
    """
    try:
        resource = request.resource

        if resource not in RESOURCE_CREATE_MAP:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Recurso '{resource}' no soporta creación o no existe"
            )

        create_func = RESOURCE_CREATE_MAP[resource]

        # Intentar crear el recurso con los datos del payload
        # Nota: esto asume que los servicios aceptan diccionarios o modelos Pydantic
        data = create_func(db, request.payload)

        return APIResponse(
            success=True,
            message=f"{resource} creado exitosamente",
            data=data
        )

    except HTTPException:
        raise
    except Exception as e:
        # Rollback en caso de error
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear {request.resource}: {str(e)}"
        )
