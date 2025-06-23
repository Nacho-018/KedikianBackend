# Servicio para operaciones de Gasto

from app.db.models import Gasto
from app.schemas.schemas import GastoSchema, GastoCreate, GastoOut
from sqlalchemy.orm import Session
from typing import List, Optional

def get_gastos(db: Session) -> List[GastoOut]:
    gastos = db.query(Gasto).all()
    return [GastoOut(
        id=g.id,
        usuario_id=g.usuario_id,
        maquina_id=g.maquina_id,
        tipo=g.tipo,
        importe_total=g.importe_total,
        fecha=g.fecha,
        descripcion=g.descripcion,
        imagen=g.imagen
    ) for g in gastos]

def get_gasto(db: Session, gasto_id: int) -> Optional[GastoOut]:
    g = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if g:
        return GastoOut(
            id=g.id,
            usuario_id=g.usuario_id,
            maquina_id=g.maquina_id,
            tipo=g.tipo,
            importe_total=g.importe_total,
            fecha=g.fecha,
            descripcion=g.descripcion,
            imagen=g.imagen
        )
    return None

def create_gasto(db: Session, gasto: GastoCreate) -> GastoOut:
    nuevo_gasto = Gasto(**gasto.model_dump())
    db.add(nuevo_gasto)
    db.commit()
    db.refresh(nuevo_gasto)
    return GastoOut(
        id=nuevo_gasto.id,
        usuario_id=nuevo_gasto.usuario_id,
        maquina_id=nuevo_gasto.maquina_id,
        tipo=nuevo_gasto.tipo,
        importe_total=nuevo_gasto.importe_total,
        fecha=nuevo_gasto.fecha,
        descripcion=nuevo_gasto.descripcion,
        imagen=nuevo_gasto.imagen
    )

def update_gasto(db: Session, gasto_id: int, gasto: GastoSchema) -> Optional[GastoOut]:
    existing_gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if existing_gasto:
        for field, value in gasto.model_dump().items():
            setattr(existing_gasto, field, value)
        db.commit()
        db.refresh(existing_gasto)
        return GastoOut(
            id=existing_gasto.id,
            usuario_id=existing_gasto.usuario_id,
            maquina_id=existing_gasto.maquina_id,
            tipo=existing_gasto.tipo,
            importe_total=existing_gasto.importe_total,
            fecha=existing_gasto.fecha,
            descripcion=existing_gasto.descripcion,
            imagen=existing_gasto.imagen
        )
    return None

def delete_gasto(db: Session, gasto_id: int) -> bool:
    gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if gasto:
        db.delete(gasto)
        db.commit()
        return True
    return False
