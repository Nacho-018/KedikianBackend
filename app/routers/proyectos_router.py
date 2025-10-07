from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from app.db.dependencies import get_db
from app.schemas.schemas import ProyectoSchema, ProyectoCreate
from sqlalchemy.orm import Session
from app.services.proyecto_service import (
    get_proyectos as service_get_proyectos,
    get_proyecto as service_get_proyecto,
    create_proyecto as service_create_proyecto,
    update_proyecto as service_update_proyecto,
    delete_proyecto as service_delete_proyecto,
    get_maquinas_by_proyecto,
    get_aridos_by_proyecto,
    get_cantidad_proyectos_activos,
    get_all_proyectos_paginated
)
from app.security.auth import get_current_user
from app.db.models import ReporteLaboral  # 👈 AGREGAR ESTE IMPORT

router = APIRouter(prefix="/proyectos", tags=["Proyectos"], dependencies=[Depends(get_current_user)])

# Endpoints Proyectos
@router.get("/", response_model=List[ProyectoSchema])
def get_proyectos(session: Session = Depends(get_db)):
    return service_get_proyectos(session)

@router.get("/{id}", response_model=ProyectoSchema)
def get_proyecto(id: int, session: Session = Depends(get_db)):
    proyecto = service_get_proyecto(session, id)
    if proyecto:
        return proyecto
    else:
        return JSONResponse(content={"error": "Proyecto no encontrado"}, status_code=404)

@router.post("/", response_model=ProyectoSchema, status_code=201)
def create_proyecto(proyecto: ProyectoCreate, session: Session = Depends(get_db)):
    return service_create_proyecto(session, proyecto)

@router.put("/{id}", response_model=ProyectoSchema)
def update_proyecto(id: int, proyecto: ProyectoSchema, session: Session = Depends(get_db)):
    try:
        updated = service_update_proyecto(session, id, proyecto)
        if updated:
            return updated
        else:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar proyecto: {str(e)}")

@router.delete("/{id}")
def delete_proyecto(id: int, session: Session = Depends(get_db)):
    deleted = service_delete_proyecto(session, id)
    if deleted:
        return {"message": "Proyecto eliminado"}
    else:
        return JSONResponse(content={"error": "Proyecto no encontrado"}, status_code=404)

@router.get("/{id}/maquinas")
def get_maquinas_proyecto(id: int, session: Session = Depends(get_db)):
    from app.services.proyecto_service import get_maquinas_by_proyecto
    try:
        return get_maquinas_by_proyecto(session, id)
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@router.get("/{id}/aridos")
def get_aridos_proyecto(id: int, session: Session = Depends(get_db)):
    from app.services.proyecto_service import get_aridos_by_proyecto
    try:
        return get_aridos_by_proyecto(session, id)
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

# 👇 AGREGAR ESTE NUEVO ENDPOINT
@router.get("/{id}/reportes-laborales")
def get_reportes_laborales_proyecto(id: int, session: Session = Depends(get_db)):
    """
    Obtiene todos los reportes laborales de un proyecto específico
    """
    try:
        reportes = session.query(ReporteLaboral).filter(
            ReporteLaboral.proyecto_id == id
        ).all()
        
        return [
            {
                "id": r.id,
                "maquina_id": r.maquina_id,
                "usuario_id": r.usuario_id,
                "proyecto_id": r.proyecto_id,
                "fecha_asignacion": r.fecha_asignacion,
                "horas_turno": r.horas_turno,
                "horometro_inicial": r.horometro_inicial,
                "created": r.created,
                "updated": r.updated
            }
            for r in reportes
        ]
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

# Endpoint para cantidad de proyectos activos
@router.get("/activos/cantidad")
def cantidad_proyectos_activos(session: Session = Depends(get_db)):
    cantidad = get_cantidad_proyectos_activos(session)
    return {"cantidad_activos": cantidad}

@router.get("/paginado")
def proyectos_paginado(skip: int = 0, limit: int = 15, session: Session = Depends(get_db)):
    return get_all_proyectos_paginated(session, skip=skip, limit=limit)