# Servicio para operaciones de Gasto

from app.db.models import Gasto
from app.schemas.schemas import GastoSchema
from sqlalchemy.orm import Session
from typing import List, Optional

def get_gastos(db: Session) -> List[Gasto]:
    return db.query(Gasto).all()

def get_gasto(db: Session, gasto_id: int) -> Optional[Gasto]:
    return db.query(Gasto).filter(Gasto.id == gasto_id).first()

def create_gasto(db: Session, gasto: GastoSchema) -> Gasto:
    nuevo_gasto = Gasto(**gasto.model_dump())
    db.add(nuevo_gasto)
    db.commit()
    db.refresh(nuevo_gasto)
    return nuevo_gasto

def update_gasto(db: Session, gasto_id: int, gasto: GastoSchema) -> Optional[Gasto]:
    existing_gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if existing_gasto:
        for field, value in gasto.model_dump().items():
            setattr(existing_gasto, field, value)
        db.commit()
        db.refresh(existing_gasto)
        return existing_gasto
    return None

def delete_gasto(db: Session, gasto_id: int) -> bool:
    gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if gasto:
        db.delete(gasto)
        db.commit()
        return True
    return False
