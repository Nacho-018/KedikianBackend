from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from app.db.dependencies import get_db
from app.schemas.schemas import PagoSchema
from sqlalchemy.orm import Session
from services.pago_service import (
    get_pagos as service_get_pagos,
    get_pago as service_get_pago,
    create_pago as service_create_pago,
    update_pago as service_update_pago,
    delete_pago as service_delete_pago,
)

router = APIRouter()

# Endpoints Pagos
@router.get("/pagos", tags=["Pagos"], response_model=List[PagoSchema])
def get_pagos(session: Session = Depends(get_db)):
    return service_get_pagos(session)

@router.get("/pagos/{id}", tags=["Pagos"], response_model=PagoSchema)
def get_pago(id: int, session: Session = Depends(get_db)):
    pago = service_get_pago(session, id)
    if pago:
        return pago
    else:
        return JSONResponse(content={"error": "Pago no encontrado"}, status_code=404)

@router.post("/pagos", tags=["Pagos"], response_model=PagoSchema, status_code=201)
def create_pago(pago: PagoSchema, session: Session = Depends(get_db)):
    return service_create_pago(session, pago)

@router.put("/pagos/{id}", tags=["Pagos"], response_model=PagoSchema)
def update_pago(id: int, pago: PagoSchema, session: Session = Depends(get_db)):
    updated = service_update_pago(session, id, pago)
    if updated:
        return updated
    else:
        return JSONResponse(content={"error": "Pago no encontrado"}, status_code=404)

@router.delete("/pagos/{id}", tags=["Pagos"])
def delete_pago(id: int, session: Session = Depends(get_db)):
    deleted = service_delete_pago(session, id)
    if deleted:
        return {"message": "Pago eliminado"}
    else:
        return JSONResponse(content={"error": "Pago no encontrado"}, status_code=404)