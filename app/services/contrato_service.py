# Servicio para operaciones de Contrato
from app.db.models import Contrato
from app.schemas.schemas import ContratoSchema
from sqlalchemy.orm import Session
from typing import List, Optional

def get_contratos(db: Session) -> List[Contrato]:
    return db.query(Contrato).all()

def get_contrato(db: Session, contrato_id: int) -> Optional[Contrato]:
    return db.query(Contrato).filter(Contrato.id == contrato_id).first()

def create_contrato(db: Session, contrato: ContratoSchema) -> Contrato:
    nuevo_contrato = Contrato(**contrato.model_dump())
    db.add(nuevo_contrato)
    db.commit()
    db.refresh(nuevo_contrato)
    return nuevo_contrato

def update_contrato(db: Session, contrato_id: int, contrato: ContratoSchema) -> Optional[Contrato]:
    existing_contrato = db.query(Contrato).filter(Contrato.id == contrato_id).first()
    if existing_contrato:
        for field, value in contrato.model_dump().items():
            setattr(existing_contrato, field, value)
        db.commit()
        db.refresh(existing_contrato)
        return existing_contrato
    return None

def delete_contrato(db: Session, contrato_id: int) -> bool:
    contrato = db.query(Contrato).filter(Contrato.id == contrato_id).first()
    if contrato:
        db.delete(contrato)
        db.commit()
        return True
    return False
