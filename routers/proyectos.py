from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from main import get_db
from models import Proyecto
from app.schemas.schemas import ProyectoSchema

router = APIRouter()

# Endpoints Proyectos
@router.get("/proyectos", tags=["Proyectos"], response_model=List[ProyectoSchema])
def get_proyectos(session = Depends(get_db)):
    proyectos = session.query(Proyecto).all()
    return proyectos

@router.get("/proyectos/{id}", tags=["Proyectos"], response_model=ProyectoSchema)
def get_proyecto(id: int, session = Depends(get_db)):
    proyecto = session.query(Proyecto).filter(Proyecto.id == id).first()
    if proyecto:
        return proyecto
    else:
        return JSONResponse(content={"error": "Proyecto no encontrado"}, status_code=404)

@router.post("/proyectos", tags=["Proyectos"], response_model=ProyectoSchema, status_code=201)
def create_proyecto(proyecto: ProyectoSchema, session = Depends(get_db)):
    nuevo_proyecto = Proyecto(**proyecto.model_dump())
    session.add(nuevo_proyecto)
    session.commit()
    session.refresh(nuevo_proyecto)
    return nuevo_proyecto

@router.put("/proyectos/{id}", tags=["Proyectos"], response_model=ProyectoSchema)
def update_proyecto(id: int, proyecto: ProyectoSchema, session = Depends(get_db)):
    existing_proyecto = session.query(Proyecto).filter(Proyecto.id == id).first()
    if existing_proyecto:
        for field, value in proyecto.model_dump().items():
            setattr(existing_proyecto, field, value)
        session.commit()
        session.refresh(existing_proyecto)
        return existing_proyecto
    else:
        return JSONResponse(content={"error": "Proyecto no encontrado"}, status_code=404)

@router.delete("/proyectos/{id}", tags=["Proyectos"])
def delete_proyecto(id: int, session = Depends(get_db)):
    proyecto = session.query(Proyecto).filter(Proyecto.id == id).first()
    if proyecto:
        session.delete(proyecto)
        session.commit()
        return {"message": "Proyecto eliminado"}
    else:
        return JSONResponse(content={"error": "Proyecto no encontrado"}, status_code=404)