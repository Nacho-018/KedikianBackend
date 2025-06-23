from app.db.models import Proyecto
from app.schemas.schemas import ProyectoSchema, ProyectoCreate, ProyectoOut
from sqlalchemy.orm import Session
from typing import List, Optional

# Servicio para operaciones de Proyecto

def get_proyectos(db: Session) -> List[ProyectoOut]:
    proyectos = db.query(Proyecto).all()
    return [ProyectoOut(
        id=p.id,
        nombre=p.nombre,
        estado=p.estado,
        fecha_creacion=p.fecha_creacion,
        contrato_id=p.contrato_id,
        ubicacion=p.ubicacion
    ) for p in proyectos]

def get_proyecto(db: Session, proyecto_id: int) -> Optional[ProyectoOut]:
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if p:
        return ProyectoOut(
            id=p.id,
            nombre=p.nombre,
            estado=p.estado,
            fecha_creacion=p.fecha_creacion,
            contrato_id=p.contrato_id,
            ubicacion=p.ubicacion
        )
    return None

def create_proyecto(db: Session, proyecto: ProyectoCreate) -> ProyectoOut:
    nuevo_proyecto = Proyecto(**proyecto.model_dump())
    db.add(nuevo_proyecto)
    db.commit()
    db.refresh(nuevo_proyecto)
    return ProyectoOut(
        id=nuevo_proyecto.id,
        nombre=nuevo_proyecto.nombre,
        estado=nuevo_proyecto.estado,
        fecha_creacion=nuevo_proyecto.fecha_creacion,
        contrato_id=nuevo_proyecto.contrato_id,
        ubicacion=nuevo_proyecto.ubicacion
    )

def update_proyecto(db: Session, proyecto_id: int, proyecto: ProyectoSchema) -> Optional[ProyectoOut]:
    existing_proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if existing_proyecto:
        for field, value in proyecto.model_dump().items():
            setattr(existing_proyecto, field, value)
        db.commit()
        db.refresh(existing_proyecto)
        return ProyectoOut(
            id=existing_proyecto.id,
            nombre=existing_proyecto.nombre,
            estado=existing_proyecto.estado,
            fecha_creacion=existing_proyecto.fecha_creacion,
            contrato_id=existing_proyecto.contrato_id,
            ubicacion=existing_proyecto.ubicacion
        )
    return None

def delete_proyecto(db: Session, proyecto_id: int) -> bool:
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if proyecto:
        db.delete(proyecto)
        db.commit()
        return True
    return False
