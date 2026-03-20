"""
Router de API de Clientes
Endpoints REST para que los clientes consulten información de sus proyectos
Requiere autenticación JWT mediante token Bearer
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.schemas.client_api import (
    ClientAPIResponse,
    ClientProjectView,
    ClientMaquinaView,
    ClientAridoView
)
from app.schemas.external_api import TokenData
from app.security.jwt_auth import verify_token
from app.db.dependencies import get_db
from app.db.models.proyecto import Proyecto
from app.db.models.reporte_laboral import ReporteLaboral
from app.db.models.entrega_arido import EntregaArido
from app.db.models.maquina import Maquina

router = APIRouter(
    prefix="/v1/client",
    tags=["API de Clientes"]
)


def _get_maquinas_asignadas(db: Session, proyecto_id: int) -> tuple[List[ClientMaquinaView], float]:
    """
    Obtiene las máquinas asignadas a un proyecto con sus horas trabajadas

    Args:
        db: Sesión de base de datos
        proyecto_id: ID del proyecto

    Returns:
        Tupla con (lista de máquinas, total de horas)
    """
    # Query con JOIN entre ReporteLaboral y Maquina
    maquinas_data = db.query(
        Maquina.nombre,
        func.sum(ReporteLaboral.horas_turno).label('horas_trabajadas')
    ).join(
        ReporteLaboral, ReporteLaboral.maquina_id == Maquina.id
    ).filter(
        ReporteLaboral.proyecto_id == proyecto_id
    ).group_by(
        Maquina.id, Maquina.nombre
    ).all()

    # Convertir a lista de objetos ClientMaquinaView
    maquinas_list = [
        ClientMaquinaView(
            nombre=m.nombre,
            horas_trabajadas=float(m.horas_trabajadas or 0)
        )
        for m in maquinas_data
    ]

    # Calcular total de horas
    total_horas = sum(m.horas_trabajadas for m in maquinas_list)

    return maquinas_list, total_horas


def _get_aridos_utilizados(db: Session, proyecto_id: int) -> tuple[List[ClientAridoView], float]:
    """
    Obtiene los áridos utilizados en un proyecto agrupados por tipo

    Args:
        db: Sesión de base de datos
        proyecto_id: ID del proyecto

    Returns:
        Tupla con (lista de áridos, total de cantidad)
    """
    # Query agrupando por tipo_arido
    aridos_data = db.query(
        EntregaArido.tipo_arido,
        func.sum(EntregaArido.cantidad).label('cantidad'),
        func.count(EntregaArido.id).label('cantidad_registros')
    ).filter(
        EntregaArido.proyecto_id == proyecto_id
    ).group_by(
        EntregaArido.tipo_arido
    ).all()

    # Convertir a lista de objetos ClientAridoView
    aridos_list = [
        ClientAridoView(
            tipo=a.tipo_arido,
            cantidad=float(a.cantidad or 0),
            unidad="m³",  # Unidad estándar (puede ajustarse según necesidad)
            cantidad_registros=int(a.cantidad_registros)
        )
        for a in aridos_data
    ]

    # Calcular total de áridos
    total_aridos = sum(a.cantidad for a in aridos_list)

    return aridos_list, total_aridos


def _build_project_view(db: Session, proyecto: Proyecto) -> ClientProjectView:
    """
    Construye la vista completa de un proyecto con todos sus datos agregados

    Args:
        db: Sesión de base de datos
        proyecto: Instancia del modelo Proyecto

    Returns:
        Vista completa del proyecto para clientes
    """
    # Obtener máquinas asignadas con horas
    maquinas_list, total_horas = _get_maquinas_asignadas(db, proyecto.id)

    # Obtener áridos utilizados
    aridos_list, total_aridos = _get_aridos_utilizados(db, proyecto.id)

    # Mapear estado booleano a texto legible
    estado_texto = "EN PROGRESO" if proyecto.estado else "COMPLETADO"

    # Formatear fecha
    fecha_inicio_str = proyecto.fecha_inicio.strftime("%Y-%m-%d") if proyecto.fecha_inicio else None

    # Construir vista del proyecto
    return ClientProjectView(
        id=proyecto.id,
        nombre=proyecto.nombre,
        estado=estado_texto,
        descripcion=proyecto.descripcion or "",
        fecha_inicio=fecha_inicio_str,
        ubicacion=proyecto.ubicacion or "",
        maquinas_asignadas=maquinas_list,
        total_horas_maquinas=total_horas,
        aridos_utilizados=aridos_list,
        total_aridos=total_aridos
    )


@router.get("/proyectos", response_model=ClientAPIResponse)
async def get_client_proyectos(
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los proyectos activos con información agregada

    Este endpoint retorna todos los proyectos en estado activo (EN PROGRESO)
    con sus máquinas asignadas, horas trabajadas y áridos utilizados.

    Args:
        token: Token JWT validado (inyectado automáticamente)
        db: Sesión de base de datos (inyectada automáticamente)

    Returns:
        ClientAPIResponse con lista de proyectos

    Example:
        GET /api/v1/client/proyectos

        Response:
        {
            "success": true,
            "message": "Proyectos obtenidos exitosamente",
            "data": [
                {
                    "id": 1,
                    "nombre": "La Quinta Livetti",
                    "estado": "EN PROGRESO",
                    ...
                }
            ],
            "total": 1
        }
    """
    try:
        # Obtener todos los proyectos activos
        proyectos = db.query(Proyecto).filter(
            Proyecto.estado == True
        ).all()

        # Construir lista de vistas de proyectos
        proyectos_view = [
            _build_project_view(db, proyecto)
            for proyecto in proyectos
        ]

        return ClientAPIResponse(
            success=True,
            message="Proyectos obtenidos exitosamente",
            data=proyectos_view,
            total=len(proyectos_view)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener proyectos: {str(e)}"
        )


@router.get("/proyectos/{proyecto_id}", response_model=ClientAPIResponse)
async def get_client_proyecto(
    proyecto_id: int,
    token: TokenData = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Obtiene un proyecto específico por ID con información agregada

    Este endpoint retorna un proyecto específico (si está activo) con sus
    máquinas asignadas, horas trabajadas y áridos utilizados.

    Args:
        proyecto_id: ID del proyecto a consultar
        token: Token JWT validado (inyectado automáticamente)
        db: Sesión de base de datos (inyectada automáticamente)

    Returns:
        ClientAPIResponse con el proyecto solicitado

    Raises:
        HTTPException 404: Si el proyecto no existe o no está activo

    Example:
        GET /api/v1/client/proyectos/1

        Response:
        {
            "success": true,
            "message": "Proyecto obtenido exitosamente",
            "data": {
                "id": 1,
                "nombre": "La Quinta Livetti",
                "estado": "EN PROGRESO",
                ...
            }
        }
    """
    try:
        # Buscar proyecto activo por ID
        proyecto = db.query(Proyecto).filter(
            Proyecto.id == proyecto_id,
            Proyecto.estado == True
        ).first()

        # Validar que el proyecto existe
        if not proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Proyecto con ID {proyecto_id} no encontrado o no está activo"
            )

        # Construir vista del proyecto
        proyecto_view = _build_project_view(db, proyecto)

        return ClientAPIResponse(
            success=True,
            message="Proyecto obtenido exitosamente",
            data=proyecto_view,
            total=1
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener proyecto: {str(e)}"
        )
