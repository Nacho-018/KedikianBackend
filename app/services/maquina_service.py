# Servicio para operaciones de Maquina

from app.db.models import Maquina
from app.schemas.schemas import MaquinaSchema
from sqlalchemy.orm import Session
from typing import List, Optional

def get_maquinas(db: Session) -> List[Maquina]:
    return db.query(Maquina).all()

def get_maquina(db: Session, maquina_id: int) -> Optional[Maquina]:
    return db.query(Maquina).filter(Maquina.id == maquina_id).first()

def create_maquina(db: Session, maquina: MaquinaSchema) -> Maquina:
    nueva_maquina = Maquina(**maquina.model_dump())
    db.add(nueva_maquina)
    db.commit()
    db.refresh(nueva_maquina)
    return nueva_maquina

def update_maquina(db: Session, maquina_id: int, maquina: MaquinaSchema) -> Optional[Maquina]:
    existing_maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()
    if existing_maquina:
        for field, value in maquina.model_dump().items():
            setattr(existing_maquina, field, value)
        db.commit()
        db.refresh(existing_maquina)
        return existing_maquina
    return None

def delete_maquina(db: Session, maquina_id: int) -> bool:
    maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()
    if maquina:
        db.delete(maquina)
        db.commit()
        return True
    return False
