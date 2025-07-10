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
)

router = APIRouter(prefix="/proyectos", tags=["Proyectos"])

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