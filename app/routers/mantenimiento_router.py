from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from app.db.dependencies import get_db
from app.schemas.schemas import MantenimientoSchema, MantenimientoCreate
from sqlalchemy.orm import Session
from app.services.mantenimiento_service import (
    get_mantenimientos as service_get_mantenimientos,
    get_mantenimiento as service_get_mantenimiento,
    create_mantenimiento as service_create_mantenimiento,
    update_mantenimiento as service_update_mantenimiento,
    delete_mantenimiento as service_delete_mantenimiento,
    get_all_mantenimientos_paginated
)
from app.security.auth import get_current_user

router = APIRouter(prefix="/mantenimientos", tags=["Mantenimientos"], dependencies=[Depends(get_current_user)])

@router.get("/", response_model=List[MantenimientoSchema])
def get_mantenimientos(session: Session = Depends(get_db)):
    return service_get_mantenimientos(session)

@router.get("/{id}", response_model=MantenimientoSchema)
def get_mantenimiento(id: int, session: Session = Depends(get_db)):
    mantenimiento = service_get_mantenimiento(session, id)
    if mantenimiento:
        return mantenimiento
    else:
        return JSONResponse(content={"error": "Mantenimiento no encontrado"}, status_code=404)

@router.post("/", response_model=MantenimientoSchema, status_code=201)
def create_mantenimiento(mantenimiento: MantenimientoCreate, session: Session = Depends(get_db)):
    return service_create_mantenimiento(session, mantenimiento)

@router.put("/{id}", response_model=MantenimientoSchema)
def update_mantenimiento(id: int, mantenimiento: MantenimientoSchema, session: Session = Depends(get_db)):
    updated = service_update_mantenimiento(session, id, mantenimiento)
    if updated:
        return updated
    else:
        return JSONResponse(content={"error": "Mantenimiento no encontrado"}, status_code=404)

@router.delete("/{id}")
def delete_mantenimiento(id: int, session: Session = Depends(get_db)):
    deleted = service_delete_mantenimiento(session, id)
    if deleted:
        return {"message": "Mantenimiento eliminado"}
    else:
        return JSONResponse(content={"error": "Mantenimiento no encontrado"}, status_code=404)

@router.get("/paginado")
def mantenimientos_paginado(skip: int = 0, limit: int = 15, session: Session = Depends(get_db)):
    return get_all_mantenimientos_paginated(session, skip=skip, limit=limit)
