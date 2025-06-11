from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from app.db.dependencies import get_db
from app.db.models import Pago
from app.schemas.schemas import PagoSchema

router = APIRouter()

# Endpoints Pagos
@router.get("/pagos", tags=["Pagos"], response_model=List[PagoSchema])
def get_pagos(session = Depends(get_db)):
    pagos = session.query(Pago).all()
    return pagos

@router.get("/pagos/{id}", tags=["Pagos"], response_model=PagoSchema)
def get_pago(id: int, session = Depends(get_db)):
    pago = session.query(Pago).filter(Pago.id == id).first()
    if pago:
        return pago
    else:
        return JSONResponse(content={"error": "Pago no encontrado"}, status_code=404)

@router.post("/pagos", tags=["Pagos"], response_model=PagoSchema, status_code=201)
def create_pago(pago: PagoSchema, session = Depends(get_db)):
    nuevo_pago = Pago(**pago.model_dump())
    session.add(nuevo_pago)
    session.commit()
    session.refresh(nuevo_pago)
    return nuevo_pago

@router.put("/pagos/{id}", tags=["Pagos"], response_model=PagoSchema)
def update_pago(id: int, pago: PagoSchema, session = Depends(get_db)):
    existing_pago = session.query(Pago).filter(Pago.id == id).first()
    if existing_pago:
        for field, value in pago.model_dump().items():
            setattr(existing_pago, field, value)
        session.commit()
        session.refresh(existing_pago)
        return existing_pago
    else:
        return JSONResponse(content={"error": "Pago no encontrado"}, status_code=404)

@router.delete("/pagos/{id}", tags=["Pagos"])
def delete_pago(id: int, session = Depends(get_db)):
    pago = session.query(Pago).filter(Pago.id == id).first()
    if pago:
        session.delete(pago)
        session.commit()
        return {"message": "Pago eliminado"}
    else:
        return JSONResponse(content={"error": "Pago no encontrado"}, status_code=404)