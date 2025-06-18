from app.db.models import MovimientoInventario
from app.schemas.schemas import MovimientoInventarioSchema
from sqlalchemy.orm import Session
from typing import List, Optional

# Servicio para operaciones de Movimiento de Inventario

def get_movimientos_inventario(db: Session) -> List[MovimientoInventario]:
    return db.query(MovimientoInventario).all()

def get_movimiento_inventario(db: Session, movimiento_id: int) -> Optional[MovimientoInventario]:
    return db.query(MovimientoInventario).filter(MovimientoInventario.id == movimiento_id).first()

def create_movimiento_inventario(db: Session, movimiento: MovimientoInventarioSchema) -> MovimientoInventario:
    nuevo_movimiento = MovimientoInventario(**movimiento.model_dump())
    db.add(nuevo_movimiento)
    db.commit()
    db.refresh(nuevo_movimiento)
    return nuevo_movimiento

def update_movimiento_inventario(db: Session, movimiento_id: int, movimiento: MovimientoInventarioSchema) -> Optional[MovimientoInventario]:
    existing_movimiento = db.query(MovimientoInventario).filter(MovimientoInventario.id == movimiento_id).first()
    if existing_movimiento:
        for field, value in movimiento.model_dump().items():
            setattr(existing_movimiento, field, value)
        db.commit()
        db.refresh(existing_movimiento)
        return existing_movimiento
    return None

def delete_movimiento_inventario(db: Session, movimiento_id: int) -> bool:
    movimiento = db.query(MovimientoInventario).filter(MovimientoInventario.id == movimiento_id).first()
    if movimiento:
        db.delete(movimiento)
        db.commit()
        return True
    return False
