from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from app.db.dependencies import get_db
from app.schemas.schemas import ArrendamientoSchema
from sqlalchemy.orm import Session
from app.services.arrendamiento_service import (
    get_arrendamientos as service_get_arrendamientos,
    get_arrendamiento as service_get_arrendamiento,
    create_arrendamiento as service_create_arrendamiento,
    update_arrendamiento as service_update_arrendamiento,
    delete_arrendamiento as service_delete_arrendamiento,
)

router = APIRouter(prefix="/arrendamientos", tags=["Arrendamientos"])

# Endpoints Arrendamientos
@router.get("/", response_model=List[ArrendamientoSchema])
def get_arrendamientos(session: Session = Depends(get_db)):
    return service_get_arrendamientos(session)

@router.get("/{id}", response_model=ArrendamientoSchema)
def get_arrendamiento(id: int, session: Session = Depends(get_db)):
    arrendamiento = service_get_arrendamiento(session, id)
    if arrendamiento:
        return arrendamiento
    else:
        return JSONResponse(content={"error": "Arrendamiento no encontrado"}, status_code=404)

@router.post("/", response_model=ArrendamientoSchema, status_code=201)
def create_arrendamiento(arrendamiento: ArrendamientoSchema, session: Session = Depends(get_db)):
    return service_create_arrendamiento(session, arrendamiento)

@router.put("/{id}", response_model=ArrendamientoSchema)
def update_arrendamiento(id: int, arrendamiento: ArrendamientoSchema, session: Session = Depends(get_db)):
    updated = service_update_arrendamiento(session, id, arrendamiento)
    if updated:
        return updated
    else:
        return JSONResponse(content={"error": "Arrendamiento no encontrado"}, status_code=404)

@router.delete("/{id}")
def delete_arrendamiento(id: int, session: Session = Depends(get_db)):
    deleted = service_delete_arrendamiento(session, id)
    if deleted:
        return {"message": "Arrendamiento eliminado"}
    else:
        return JSONResponse(content={"error": "Arrendamiento no encontrado"}, status_code=404)