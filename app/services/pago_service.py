# Servicio para operaciones de Pago
from app.db.models import Pago
from app.schemas.schemas import PagoSchema
from sqlalchemy.orm import Session
from typing import List, Optional

def get_pagos(db: Session) -> List[Pago]:
    return db.query(Pago).all()

def get_pago(db: Session, pago_id: int) -> Optional[Pago]:
    return db.query(Pago).filter(Pago.id == pago_id).first()

def create_pago(db: Session, pago: PagoSchema) -> Pago:
    nuevo_pago = Pago(**pago.model_dump())
    db.add(nuevo_pago)
    db.commit()
    db.refresh(nuevo_pago)
    return nuevo_pago

def update_pago(db: Session, pago_id: int, pago: PagoSchema) -> Optional[Pago]:
    existing_pago = db.query(Pago).filter(Pago.id == pago_id).first()
    if existing_pago:
        for field, value in pago.model_dump().items():
            setattr(existing_pago, field, value)
        db.commit()
        db.refresh(existing_pago)
        return existing_pago
    return None

def delete_pago(db: Session, pago_id: int) -> bool:
    pago = db.query(Pago).filter(Pago.id == pago_id).first()
    if pago:
        db.delete(pago)
        db.commit()
        return True
    return False
