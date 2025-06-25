from app.db.models import Proyecto, Contrato
from app.schemas.schemas import ProyectoSchema, ProyectoCreate, ProyectoOut
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

# Servicio para operaciones de Proyecto

def get_proyectos(db: Session) -> List[ProyectoOut]:
    proyectos = db.query(Proyecto).all()
    return [ProyectoOut(
        id=p.id,
        nombre=p.nombre,
        descripcion=p.descripcion,
        estado=p.estado,
        fecha_creacion=p.fecha_creacion,
        fecha_inicio=p.fecha_inicio,
        fecha_fin=p.fecha_fin,
        progreso=p.progreso,
        gerente=p.gerente,
        contrato_id=p.contrato_id,
        ubicacion=p.ubicacion
    ) for p in proyectos]

def get_proyecto(db: Session, proyecto_id: int) -> Optional[ProyectoOut]:
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if p:
        return ProyectoOut(
            id=p.id,
            nombre=p.nombre,
            descripcion=p.descripcion,
            estado=p.estado,
            fecha_creacion=p.fecha_creacion,
            fecha_inicio=p.fecha_inicio,
            fecha_fin=p.fecha_fin,
            progreso=p.progreso,
            gerente=p.gerente,
            contrato_id=p.contrato_id,
            ubicacion=p.ubicacion
        )
    return None

def create_proyecto(db: Session, proyecto: ProyectoCreate) -> ProyectoOut:
    # Asignar fecha_creacion automáticamente si no se proporciona
    proyecto_data = proyecto.model_dump()
    if proyecto_data.get('fecha_creacion') is None:
        proyecto_data['fecha_creacion'] = datetime.now()
    
    # Validar que el contrato_id existe, si no existe, establecerlo como None
    if proyecto_data.get('contrato_id') is not None:
        contrato = db.query(Contrato).filter(Contrato.id == proyecto_data['contrato_id']).first()
        if contrato is None:
            proyecto_data['contrato_id'] = None
    
    nuevo_proyecto = Proyecto(**proyecto_data)
    db.add(nuevo_proyecto)
    db.commit()
    db.refresh(nuevo_proyecto)
    return ProyectoOut(
        id=nuevo_proyecto.id,
        nombre=nuevo_proyecto.nombre,
        descripcion=nuevo_proyecto.descripcion,
        estado=nuevo_proyecto.estado,
        fecha_creacion=nuevo_proyecto.fecha_creacion,
        fecha_inicio=nuevo_proyecto.fecha_inicio,
        fecha_fin=nuevo_proyecto.fecha_fin,
        progreso=nuevo_proyecto.progreso,
        gerente=nuevo_proyecto.gerente,
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
            descripcion=existing_proyecto.descripcion,
            estado=existing_proyecto.estado,
            fecha_creacion=existing_proyecto.fecha_creacion,
            fecha_inicio=existing_proyecto.fecha_inicio,
            fecha_fin=existing_proyecto.fecha_fin,
            progreso=existing_proyecto.progreso,
            gerente=existing_proyecto.gerente,
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
