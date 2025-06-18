from app.db.models import Proyecto
from app.schemas.schemas import ProyectoSchema
from sqlalchemy.orm import Session
from typing import List, Optional

# Servicio para operaciones de Proyecto

def get_proyectos(db: Session) -> List[Proyecto]:
    return db.query(Proyecto).all()

def get_proyecto(db: Session, proyecto_id: int) -> Optional[Proyecto]:
    return db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()

def create_proyecto(db: Session, proyecto: ProyectoSchema) -> Proyecto:
    nuevo_proyecto = Proyecto(**proyecto.model_dump())
    db.add(nuevo_proyecto)
    db.commit()
    db.refresh(nuevo_proyecto)
    return nuevo_proyecto

def update_proyecto(db: Session, proyecto_id: int, proyecto: ProyectoSchema) -> Optional[Proyecto]:
    existing_proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if existing_proyecto:
        for field, value in proyecto.model_dump().items():
            setattr(existing_proyecto, field, value)
        db.commit()
        db.refresh(existing_proyecto)
        return existing_proyecto
    return None

def delete_proyecto(db: Session, proyecto_id: int) -> bool:
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if proyecto:
        db.delete(proyecto)
        db.commit()
        return True
    return False
