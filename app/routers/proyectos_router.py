from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from app.db.dependencies import get_db
from app.schemas.schemas import ProyectoSchema
from sqlalchemy.orm import Session
from app.services.proyecto_service import (
    get_proyectos as service_get_proyectos,
    get_proyecto as service_get_proyecto,
    create_proyecto as service_create_proyecto,
    update_proyecto as service_update_proyecto,
    delete_proyecto as service_delete_proyecto,
)

router = APIRouter()

# Endpoints Proyectos
@router.get("/proyectos", tags=["Proyectos"], response_model=List[ProyectoSchema])
def get_proyectos(session: Session = Depends(get_db)):
    return service_get_proyectos(session)

@router.get("/proyectos/{id}", tags=["Proyectos"], response_model=ProyectoSchema)
def get_proyecto(id: int, session: Session = Depends(get_db)):
    proyecto = service_get_proyecto(session, id)
    if proyecto:
        return proyecto
    else:
        return JSONResponse(content={"error": "Proyecto no encontrado"}, status_code=404)

@router.post("/proyectos", tags=["Proyectos"], response_model=ProyectoSchema, status_code=201)
def create_proyecto(proyecto: ProyectoSchema, session: Session = Depends(get_db)):
    return service_create_proyecto(session, proyecto)

@router.put("/proyectos/{id}", tags=["Proyectos"], response_model=ProyectoSchema)
def update_proyecto(id: int, proyecto: ProyectoSchema, session: Session = Depends(get_db)):
    updated = service_update_proyecto(session, id, proyecto)
    if updated:
        return updated
    else:
        return JSONResponse(content={"error": "Proyecto no encontrado"}, status_code=404)

@router.delete("/proyectos/{id}", tags=["Proyectos"])
def delete_proyecto(id: int, session: Session = Depends(get_db)):
    deleted = service_delete_proyecto(session, id)
    if deleted:
        return {"message": "Proyecto eliminado"}
    else:
        return JSONResponse(content={"error": "Proyecto no encontrado"}, status_code=404)