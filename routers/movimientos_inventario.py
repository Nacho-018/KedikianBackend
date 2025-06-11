from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from app.db.dependencies import get_db
from app.db.models import MovimientoInventario
from app.schemas.schemas import MovimientoInventarioSchema

router = APIRouter()

# Endpoints Movimientos de Inventario
@router.get("/movimientos-inventario", tags=["Movimientos de Inventario"], response_model=List[MovimientoInventarioSchema])
def get_movimientos_inventario(session = Depends(get_db)):
    movimientos = session.query(MovimientoInventario).all()
    return movimientos

@router.get("/movimientos-inventario/{id}", tags=["Movimientos de Inventario"], response_model=MovimientoInventarioSchema)
def get_movimiento_inventario(id: int, session = Depends(get_db)):
    movimiento = session.query(MovimientoInventario).filter(MovimientoInventario.id == id).first()
    if movimiento:
        return movimiento
    else:
        return JSONResponse(content={"error": "Movimiento de inventario no encontrado"}, status_code=404)

@router.post("/movimientos-inventario", tags=["Movimientos de Inventario"], response_model=MovimientoInventarioSchema, status_code=201)
def create_movimiento_inventario(movimiento_inventario: MovimientoInventarioSchema, session = Depends(get_db)):
    nuevo_movimiento = MovimientoInventario(**movimiento_inventario.model_dump())
    session.add(nuevo_movimiento)
    session.commit()
    session.refresh(nuevo_movimiento)
    return nuevo_movimiento

@router.put("/movimientos-inventario/{id}", tags=["Movimientos de Inventario"], response_model=MovimientoInventarioSchema)
def update_movimiento_inventario(id: int, movimiento_inventario: MovimientoInventarioSchema, session = Depends(get_db)):
    existing_movimiento = session.query(MovimientoInventario).filter(MovimientoInventario.id == id).first()
    if existing_movimiento:
        for field, value in movimiento_inventario.model_dump().items():
            setattr(existing_movimiento, field, value)
        session.commit()
        session.refresh(existing_movimiento)
        return existing_movimiento
    else:
        return JSONResponse(content={"error": "Movimiento de inventario no encontrado"}, status_code=404)

@router.delete("/movimientos-inventario/{id}", tags=["Movimientos de Inventario"])
def delete_movimiento_inventario(id: int, session = Depends(get_db)):
    movimiento = session.query(MovimientoInventario).filter(MovimientoInventario.id == id).first()
    if movimiento:
        session.delete(movimiento)
        session.commit()
        return {"message": "Movimiento de inventario eliminado"}
    else:
        return JSONResponse(content={"error": "Movimiento de inventario no encontrado"}, status_code=404)