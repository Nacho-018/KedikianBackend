from sqlalchemy.orm import Session
from app.db.models.entrega_arido import EntregaArido
from app.schemas.schemas import EntregaAridoCreate, EntregaAridoOut
from typing import List, Optional

def create_entrega_arido(db: Session, entrega_data: EntregaAridoCreate) -> EntregaAridoOut:
    entrega = EntregaArido(**entrega_data.dict())
    db.add(entrega)
    db.commit()
    db.refresh(entrega)
    return EntregaAridoOut.model_validate(entrega)

def get_entrega_arido(db: Session, entrega_id: int) -> Optional[EntregaAridoOut]:
    entrega = db.query(EntregaArido).filter(EntregaArido.id == entrega_id).first()
    if entrega:
        return EntregaAridoOut.model_validate(entrega)
    return None

def get_all_entregas_arido(db: Session, skip: int = 0, limit: int = 100) -> List[EntregaAridoOut]:
    entregas = db.query(EntregaArido).offset(skip).limit(limit).all()
    return [EntregaAridoOut.model_validate(e) for e in entregas]

def update_entrega_arido(db: Session, entrega_id: int, entrega_data: EntregaAridoCreate) -> Optional[EntregaAridoOut]:
    entrega = db.query(EntregaArido).filter(EntregaArido.id == entrega_id).first()
    if not entrega:
        return None
    for key, value in entrega_data.dict().items():
        setattr(entrega, key, value)
    db.commit()
    db.refresh(entrega)
    return EntregaAridoOut.model_validate(entrega)

def delete_entrega_arido(db: Session, entrega_id: int) -> bool:
    entrega = db.query(EntregaArido).filter(EntregaArido.id == entrega_id).first()
    if not entrega:
        return False
    db.delete(entrega)
    db.commit()
    return True
