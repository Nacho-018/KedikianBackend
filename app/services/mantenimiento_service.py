from app.db.models import Mantenimiento
from app.schemas.schemas import MantenimientoSchema, MantenimientoCreate, MantenimientoOut
from sqlalchemy.orm import Session
from typing import List, Optional

def get_mantenimientos(db: Session) -> List[MantenimientoOut]:
    mantenimientos = db.query(Mantenimiento).all()
    return [MantenimientoOut(
        id=m.id,
        maquina_id=m.maquina_id,
        tipo=m.tipo,
        fecha=m.fecha,
        descripcion=m.descripcion,
        created=m.created,
        updated=m.updated
    ) for m in mantenimientos]

def get_mantenimiento(db: Session, mantenimiento_id: int) -> Optional[MantenimientoOut]:
    m = db.query(Mantenimiento).filter(Mantenimiento.id == mantenimiento_id).first()
    if m:
        return MantenimientoOut(
            id=m.id,
            maquina_id=m.maquina_id,
            tipo=m.tipo,
            fecha=m.fecha,
            descripcion=m.descripcion,
            created=m.created,
            updated=m.updated
        )
    return None

def create_mantenimiento(db: Session, mantenimiento: MantenimientoCreate) -> MantenimientoOut:
    nuevo_mantenimiento = Mantenimiento(**mantenimiento.model_dump())
    db.add(nuevo_mantenimiento)
    db.commit()
    db.refresh(nuevo_mantenimiento)
    return MantenimientoOut(
        id=nuevo_mantenimiento.id,
        maquina_id=nuevo_mantenimiento.maquina_id,
        tipo=nuevo_mantenimiento.tipo,
        fecha=nuevo_mantenimiento.fecha,
        descripcion=nuevo_mantenimiento.descripcion,
        created=nuevo_mantenimiento.created,
        updated=nuevo_mantenimiento.updated
    )

def update_mantenimiento(db: Session, mantenimiento_id: int, mantenimiento: MantenimientoSchema) -> Optional[MantenimientoOut]:
    existing_mantenimiento = db.query(Mantenimiento).filter(Mantenimiento.id == mantenimiento_id).first()
    if existing_mantenimiento:
        for field, value in mantenimiento.model_dump().items():
            setattr(existing_mantenimiento, field, value)
        db.commit()
        db.refresh(existing_mantenimiento)
        return MantenimientoOut(
            id=existing_mantenimiento.id,
            maquina_id=existing_mantenimiento.maquina_id,
            tipo=existing_mantenimiento.tipo,
            fecha=existing_mantenimiento.fecha,
            descripcion=existing_mantenimiento.descripcion,
            created=existing_mantenimiento.created,
            updated=existing_mantenimiento.updated
        )
    return None

def delete_mantenimiento(db: Session, mantenimiento_id: int) -> bool:
    mantenimiento = db.query(Mantenimiento).filter(Mantenimiento.id == mantenimiento_id).first()
    if mantenimiento:
        db.delete(mantenimiento)
        db.commit()
        return True
    return False

def get_all_mantenimientos_paginated(db: Session, skip: int = 0, limit: int = 15) -> List[MantenimientoOut]:
    mantenimientos = db.query(Mantenimiento).offset(skip).limit(limit).all()
    return [MantenimientoOut(
        id=m.id,
        maquina_id=m.maquina_id,
        tipo=m.tipo,
        fecha=m.fecha,
        descripcion=m.descripcion,
        created=m.created,
        updated=m.updated
    ) for m in mantenimientos]
