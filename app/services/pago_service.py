# servicio para operaciones de Pago
from app.db.models import Pago
from app.schemas.schemas import PagoSchema, PagoCreate, PagoOut
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError

def get_pagos(db: Session) -> List[PagoOut]:
    try:
        pagos = db.query(Pago).all()
        return [
            PagoOut(
                id=p.id,
                proyecto_id=p.proyecto_id,
                importe_total=p.importe_total,
                fecha=p.fecha,
                descripcion=p.descripcion
            ) for p in pagos
        ]
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error al obtener pagos: {str(e)}")

def get_pago(db: Session, pago_id: int) -> Optional[PagoOut]:
    try:
        p = db.query(Pago).filter(Pago.id == pago_id).first()
        if p:
            return PagoOut(
                id=p.id,
                proyecto_id=p.proyecto_id,
                importe_total=p.importe_total,
                fecha=p.fecha,
                descripcion=p.descripcion
            )
        return None
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error al obtener pago: {str(e)}")

def create_pago(db: Session, pago: PagoCreate) -> PagoOut:
    try:
        pago_data = pago.model_dump()
        pago_data = {k: v for k, v in pago_data.items() if v is not None}

        nuevo_pago = Pago(**pago_data)
        db.add(nuevo_pago)
        db.commit()
        db.refresh(nuevo_pago)

        return PagoOut(
            id=nuevo_pago.id,
            proyecto_id=nuevo_pago.proyecto_id,
            importe_total=nuevo_pago.importe_total,
            fecha=nuevo_pago.fecha,
            descripcion=nuevo_pago.descripcion
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error al crear pago: {str(e)}")

def update_pago(db: Session, pago_id: int, pago: PagoSchema) -> Optional[PagoOut]:
    try:
        existing_pago = db.query(Pago).filter(Pago.id == pago_id).first()
        if existing_pago:
            pago_data = pago.model_dump()
            pago_data = {k: v for k, v in pago_data.items() if v is not None and k != 'id'}

            for field, value in pago_data.items():
                setattr(existing_pago, field, value)

            db.commit()
            db.refresh(existing_pago)

            return PagoOut(
                id=existing_pago.id,
                proyecto_id=existing_pago.proyecto_id,
                importe_total=existing_pago.importe_total,
                fecha=existing_pago.fecha,
                descripcion=existing_pago.descripcion
            )
        return None
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error al actualizar pago: {str(e)}")

def get_pagos_filtrados(db: Session, fecha_inicio: Optional[datetime] = None, fecha_fin: Optional[datetime] = None) -> List[PagoOut]:
    query = db.query(Pago)
    if fecha_inicio:
        query = query.filter(Pago.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(Pago.fecha <= fecha_fin)
    pagos = query.all()
    return [
        PagoOut(
            id=p.id,
            proyecto_id=p.proyecto_id,
            importe_total=p.importe_total,
            fecha=p.fecha,
            descripcion=p.descripcion
        )
        for p in pagos
    ]
    
def delete_pago(db: Session, pago_id: int) -> bool:
    try:
        pago = db.query(Pago).filter(Pago.id == pago_id).first()
        if pago:
            db.delete(pago)
            db.commit()
            return True
        return False
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error al eliminar pago: {str(e)}")

def get_all_pagos_paginated(db: Session, skip: int = 0, limit: int = 15) -> List[PagoOut]:
    pagos = db.query(Pago).offset(skip).limit(limit).all()
    return [
        PagoOut(
            id=p.id,
            proyecto_id=p.proyecto_id,
            importe_total=p.importe_total,
            fecha=p.fecha,
            descripcion=p.descripcion
        ) for p in pagos
    ]
