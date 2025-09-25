from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.db.dependencies import get_db
from datetime import datetime
from app.db.models import Pago
from app.schemas.schemas import PagoSchema, PagoCreate
from sqlalchemy.orm import Session
from app.services.pago_service import (
    get_pagos as service_get_pagos,
    get_pago as service_get_pago,
    create_pago as service_create_pago,
    update_pago as service_update_pago,
    delete_pago as service_delete_pago,
    get_all_pagos_paginated
)
from app.security.auth import get_current_user

router = APIRouter(prefix="/pagos", tags=["Pagos"], dependencies=[Depends(get_current_user)])

# Obtener todos los pagos
@router.get("/", response_model=List[PagoOut])
def get_pagos(
    fechaInicio: Optional[datetime] = Query(None),
    fechaFin: Optional[datetime] = Query(None),
    session: Session = Depends(get_db)
):
    try:
        query = session.query(Pago)
        if fechaInicio:
            query = query.filter(Pago.fecha >= fechaInicio)
        if fechaFin:
            query = query.filter(Pago.fecha <= fechaFin)
        pagos = query.all()
        return [PagoOut.from_orm(p) for p in pagos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener pagos: {str(e)}")

# Obtener pago por ID
@router.get("/{id}", response_model=PagoOut)
def get_pago(id: int, session: Session = Depends(get_db)):
    pago = session.query(Pago).filter(Pago.id == id).first()
    if pago:
        return PagoOut.from_orm(pago)
    else:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

@router.post("/", response_model=PagoSchema, status_code=201)
def create_pago(pago: PagoCreate, session: Session = Depends(get_db)):
    try:
        return service_create_pago(session, pago)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear pago: {str(e)}")

@router.put("/{id}", response_model=PagoSchema)
def update_pago(id: int, pago: PagoSchema, session: Session = Depends(get_db)):
    try:
        updated = service_update_pago(session, id, pago)
        if updated:
            return updated
        else:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar pago: {str(e)}")

@router.delete("/{id}")
def delete_pago(id: int, session: Session = Depends(get_db)):
    try:
        deleted = service_delete_pago(session, id)
        if deleted:
            return {"message": "Pago eliminado"}
        else:
            raise HTTPException(status_code=404, detail="Pago no encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar pago: {str(e)}")

@router.get("/paginado")
def pagos_paginado(skip: int = 0, limit: int = 15, session: Session = Depends(get_db)):
    return get_all_pagos_paginated(session, skip=skip, limit=limit)