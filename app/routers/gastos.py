from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from app.db.dependencies import get_db
from app.schemas.schemas import GastoSchema
from sqlalchemy.orm import Session
from services.gasto_service import (
    get_gastos as service_get_gastos,
    get_gasto as service_get_gasto,
    create_gasto as service_create_gasto,
    update_gasto as service_update_gasto,
    delete_gasto as service_delete_gasto,
)

router = APIRouter()

# Endpoints Gastos
@router.get("/gastos", tags=["Gastos"], response_model=List[GastoSchema])
def get_gastos(session: Session = Depends(get_db)):
    return service_get_gastos(session)

@router.get("/gastos/{id}", tags=["Gastos"], response_model=GastoSchema)
def get_gasto(id: int, session: Session = Depends(get_db)):
    gasto = service_get_gasto(session, id)
    if gasto:
        return gasto
    else:
        return JSONResponse(content={"error": "Gasto no encontrado"}, status_code=404)

@router.post("/gastos", tags=["Gastos"], response_model=GastoSchema, status_code=201)
def create_gasto(gasto: GastoSchema, session: Session = Depends(get_db)):
    return service_create_gasto(session, gasto)

@router.put("/gastos/{id}", tags=["Gastos"], response_model=GastoSchema)
def update_gasto(id: int, gasto: GastoSchema, session: Session = Depends(get_db)):
    updated = service_update_gasto(session, id, gasto)
    if updated:
        return updated
    else:
        return JSONResponse(content={"error": "Gasto no encontrado"}, status_code=404)

@router.delete("/gastos/{id}", tags=["Gastos"])
def delete_gasto(id: int, session: Session = Depends(get_db)):
    deleted = service_delete_gasto(session, id)
    if deleted:
        return {"message": "Gasto eliminado"}
    else:
        return JSONResponse(content={"error": "Gasto no encontrado"}, status_code=404)