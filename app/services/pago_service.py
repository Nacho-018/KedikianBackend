# Servicio para operaciones de Pago
from app.db.models import Pago
from app.schemas.schemas import PagoSchema, PagoCreate, PagoOut
from sqlalchemy.orm import Session
from typing import List, Optional

def get_pagos(db: Session) -> List[PagoOut]:
    pagos = db.query(Pago).all()
    return [PagoOut(
        id=p.id,
        proyecto_id=p.proyecto_id,
        producto_id=p.producto_id,
        importe_total=p.importe_total,
        fecha=p.fecha,
        descripcion=p.descripcion
    ) for p in pagos]

def get_pago(db: Session, pago_id: int) -> Optional[PagoOut]:
    p = db.query(Pago).filter(Pago.id == pago_id).first()
    if p:
        return PagoOut(
            id=p.id,
            proyecto_id=p.proyecto_id,
            producto_id=p.producto_id,
            importe_total=p.importe_total,
            fecha=p.fecha,
            descripcion=p.descripcion
        )
    return None

def create_pago(db: Session, pago: PagoCreate) -> PagoOut:
    nuevo_pago = Pago(**pago.model_dump())
    db.add(nuevo_pago)
    db.commit()
    db.refresh(nuevo_pago)
    return PagoOut(
        id=nuevo_pago.id,
        proyecto_id=nuevo_pago.proyecto_id,
        producto_id=nuevo_pago.producto_id,
        importe_total=nuevo_pago.importe_total,
        fecha=nuevo_pago.fecha,
        descripcion=nuevo_pago.descripcion
    )

def update_pago(db: Session, pago_id: int, pago: PagoSchema) -> Optional[PagoOut]:
    existing_pago = db.query(Pago).filter(Pago.id == pago_id).first()
    if existing_pago:
        for field, value in pago.model_dump().items():
            setattr(existing_pago, field, value)
        db.commit()
        db.refresh(existing_pago)
        return PagoOut(
            id=existing_pago.id,
            proyecto_id=existing_pago.proyecto_id,
            producto_id=existing_pago.producto_id,
            importe_total=existing_pago.importe_total,
            fecha=existing_pago.fecha,
            descripcion=existing_pago.descripcion
        )
    return None

def delete_pago(db: Session, pago_id: int) -> bool:
    pago = db.query(Pago).filter(Pago.id == pago_id).first()
    if pago:
        db.delete(pago)
        db.commit()
        return True
    return False
