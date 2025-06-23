from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from app.db.dependencies import get_db
from app.schemas.schemas import MovimientoInventarioSchema
from sqlalchemy.orm import Session
from app.services.movimiento_inventario_service import (
    get_movimientos_inventario as service_get_movimientos_inventario,
    get_movimiento_inventario as service_get_movimiento_inventario,
    create_movimiento_inventario as service_create_movimiento_inventario,
    update_movimiento_inventario as service_update_movimiento_inventario,
    delete_movimiento_inventario as service_delete_movimiento_inventario,
)

router = APIRouter()

# Endpoints Movimientos de Inventario
@router.get("/movimientos-inventario", tags=["Movimientos de Inventario"], response_model=List[MovimientoInventarioSchema])
def get_movimientos_inventario(session: Session = Depends(get_db)):
    return service_get_movimientos_inventario(session)

@router.get("/movimientos-inventario/{id}", tags=["Movimientos de Inventario"], response_model=MovimientoInventarioSchema)
def get_movimiento_inventario(id: int, session: Session = Depends(get_db)):
    movimiento = service_get_movimiento_inventario(session, id)
    if movimiento:
        return movimiento
    else:
        return JSONResponse(content={"error": "Movimiento de inventario no encontrado"}, status_code=404)

@router.post("/movimientos-inventario", tags=["Movimientos de Inventario"], response_model=MovimientoInventarioSchema, status_code=201)
def create_movimiento_inventario(movimiento_inventario: MovimientoInventarioSchema, session: Session = Depends(get_db)):
    return service_create_movimiento_inventario(session, movimiento_inventario)

@router.put("/movimientos-inventario/{id}", tags=["Movimientos de Inventario"], response_model=MovimientoInventarioSchema)
def update_movimiento_inventario(id: int, movimiento_inventario: MovimientoInventarioSchema, session: Session = Depends(get_db)):
    updated = service_update_movimiento_inventario(session, id, movimiento_inventario)
    if updated:
        return updated
    else:
        return JSONResponse(content={"error": "Movimiento de inventario no encontrado"}, status_code=404)

@router.delete("/movimientos-inventario/{id}", tags=["Movimientos de Inventario"])
def delete_movimiento_inventario(id: int, session: Session = Depends(get_db)):
    deleted = service_delete_movimiento_inventario(session, id)
    if deleted:
        return {"message": "Movimiento de inventario eliminado"}
    else:
        return JSONResponse(content={"error": "Movimiento de inventario no encontrado"}, status_code=404)