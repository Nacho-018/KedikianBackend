from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from app.db.dependencies import get_db
from app.db.models import Gasto
from app.schemas.schemas import GastoSchema

router = APIRouter()

# Endpoints Gastos
@router.get("/gastos", tags=["Gastos"], response_model=List[GastoSchema])
def get_gastos(session = Depends(get_db)):
    gastos = session.query(Gasto).all()
    return gastos

@router.get("/gastos/{id}", tags=["Gastos"], response_model=GastoSchema)
def get_gasto(id: int, session = Depends(get_db)):
    gasto = session.query(Gasto).filter(Gasto.id == id).first()
    if gasto:
        return gasto
    else:
        return JSONResponse(content={"error": "Gasto no encontrado"}, status_code=404)

@router.post("/gastos", tags=["Gastos"], response_model=GastoSchema, status_code=201)
def create_gasto(gasto: GastoSchema, session = Depends(get_db)):
    nuevo_gasto = Gasto(**gasto.model_dump())
    session.add(nuevo_gasto)
    session.commit()
    session.refresh(nuevo_gasto)
    return nuevo_gasto

@router.put("/gastos/{id}", tags=["Gastos"], response_model=GastoSchema)
def update_gasto(id: int, gasto: GastoSchema, session = Depends(get_db)):
    existing_gasto = session.query(Gasto).filter(Gasto.id == id).first()
    if existing_gasto:
        for field, value in gasto.model_dump().items():
            setattr(existing_gasto, field, value)
        session.commit()
        session.refresh(existing_gasto)
        return existing_gasto
    else:
        return JSONResponse(content={"error": "Gasto no encontrado"}, status_code=404)

@router.delete("/gastos/{id}", tags=["Gastos"])
def delete_gasto(id: int, session = Depends(get_db)):
    gasto = session.query(Gasto).filter(Gasto.id == id).first()
    if gasto:
        session.delete(gasto)
        session.commit()
        return {"message": "Gasto eliminado"}
    else:
        return JSONResponse(content={"error": "Gasto no encontrado"}, status_code=404)