# Servicio para operaciones de Arrendamiento

from app.db.models import Arrendamiento
from app.schemas.schemas import ArrendamientoSchema
from sqlalchemy.orm import Session
from typing import List, Optional

def get_arrendamientos(db: Session) -> List[Arrendamiento]:
    return db.query(Arrendamiento).all()

def get_arrendamiento(db: Session, arrendamiento_id: int) -> Optional[Arrendamiento]:
    return db.query(Arrendamiento).filter(Arrendamiento.id == arrendamiento_id).first()

def create_arrendamiento(db: Session, arrendamiento: ArrendamientoSchema) -> Arrendamiento:
    nuevo_arrendamiento = Arrendamiento(**arrendamiento.model_dump())
    db.add(nuevo_arrendamiento)
    db.commit()
    db.refresh(nuevo_arrendamiento)
    return nuevo_arrendamiento

def update_arrendamiento(db: Session, arrendamiento_id: int, arrendamiento: ArrendamientoSchema) -> Optional[Arrendamiento]:
    existing_arrendamiento = db.query(Arrendamiento).filter(Arrendamiento.id == arrendamiento_id).first()
    if existing_arrendamiento:
        for field, value in arrendamiento.model_dump().items():
            setattr(existing_arrendamiento, field, value)
        db.commit()
        db.refresh(existing_arrendamiento)
        return existing_arrendamiento
    return None

def delete_arrendamiento(db: Session, arrendamiento_id: int) -> bool:
    arrendamiento = db.query(Arrendamiento).filter(Arrendamiento.id == arrendamiento_id).first()
    if arrendamiento:
        db.delete(arrendamiento)
        db.commit()
        return True
    return False
