from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from main import get_db
from models import Arrendamiento
from app.schemas.schemas import ArrendamientoSchema

router = APIRouter()

# Endpoints Arrendamientos
@router.get("/arrendamientos", tags=["Arrendamientos"], response_model=List[ArrendamientoSchema])
def get_arrendamientos(session = Depends(get_db)):
    arrendamientos = session.query(Arrendamiento).all()
    return arrendamientos

@router.get("/arrendamientos/{id}", tags=["Arrendamientos"], response_model=ArrendamientoSchema)
def get_arrendamiento(id: int, session = Depends(get_db)):
    arrendamiento = session.query(Arrendamiento).filter(Arrendamiento.id == id).first()
    if arrendamiento:
        return arrendamiento
    else:
        return JSONResponse(content={"error": "Arrendamiento no encontrado"}, status_code=404)

@router.post("/arrendamientos", tags=["Arrendamientos"], response_model=ArrendamientoSchema, status_code=201)
def create_arrendamiento(arrendamiento: ArrendamientoSchema, session = Depends(get_db)):
    nuevo_arrendamiento = Arrendamiento(**arrendamiento.model_dump())
    session.add(nuevo_arrendamiento)
    session.commit()
    session.refresh(nuevo_arrendamiento)
    return nuevo_arrendamiento

@router.put("/arrendamientos/{id}", tags=["Arrendamientos"], response_model=ArrendamientoSchema)
def update_arrendamiento(id: int, arrendamiento: ArrendamientoSchema, session = Depends(get_db)):
    existing_arrendamiento = session.query(Arrendamiento).filter(Arrendamiento.id == id).first()
    if existing_arrendamiento:
        for field, value in arrendamiento.model_dump().items():
            setattr(existing_arrendamiento, field, value)
        session.commit()
        session.refresh(existing_arrendamiento)
        return existing_arrendamiento
    else:
        return JSONResponse(content={"error": "Arrendamiento no encontrado"}, status_code=404)

@router.delete("/arrendamientos/{id}", tags=["Arrendamientos"])
def delete_arrendamiento(id: int, session = Depends(get_db)):
    arrendamiento = session.query(Arrendamiento).filter(Arrendamiento.id == id).first()
    if arrendamiento:
        session.delete(arrendamiento)
        session.commit()
        return {"message": "Arrendamiento eliminado"}
    else:
        return JSONResponse(content={"error": "Arrendamiento no encontrado"}, status_code=404)