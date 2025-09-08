from sqlalchemy.orm import Session
from app.db.models.mantenimiento import Mantenimiento
from app.db.models.maquina import Maquina
from app.schemas.schemas import MantenimientoCreate, MantenimientoSchema, MantenimientoOut
from typing import List, Optional
from fastapi import HTTPException

def get_all_mantenimientos_paginated(db: Session, skip: int = 0, limit: int = 15) -> List[MantenimientoOut]:
    mantenimientos = db.query(Mantenimiento).offset(skip).limit(limit).all()
    return [MantenimientoOut(
        id=m.id,
        maquina_id=m.maquina_id,
        tipo_mantenimiento=m.tipo_mantenimiento,
        descripcion=m.descripcion,
        fecha_mantenimiento=m.fecha_mantenimiento,
        horas_maquina=m.horas_maquina,
        costo=m.costo,
        responsable=m.responsable,
        observaciones=m.observaciones,
        created=m.created,
        updated=m.updated
    ) for m in mantenimientos]

def get_mantenimientos(db: Session) -> List[MantenimientoOut]:
    mantenimientos = db.query(Mantenimiento).all()
    return [MantenimientoOut(
        id=m.id,
        maquina_id=m.maquina_id,
        tipo_mantenimiento=m.tipo_mantenimiento,
        descripcion=m.descripcion,
        fecha_mantenimiento=m.fecha_mantenimiento,
        horas_maquina=m.horas_maquina,
        costo=m.costo,
        responsable=m.responsable,
        observaciones=m.observaciones,
        created=m.created,
        updated=m.updated
    ) for m in mantenimientos]

def get_mantenimientos_maquina(session: Session, maquina_id: int) -> List[MantenimientoSchema]:
    """Obtiene todos los mantenimientos de una máquina específica"""
    # Verificar que la máquina existe
    maquina = session.query(Maquina).filter(Maquina.id == maquina_id).first()
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")
    
    mantenimientos = session.query(Mantenimiento).filter(
        Mantenimiento.maquina_id == maquina_id
    ).order_by(Mantenimiento.fecha_mantenimiento.desc()).all()
    
    return [MantenimientoSchema.from_orm(m) for m in mantenimientos]

def create_mantenimiento(session: Session, mantenimiento: MantenimientoCreate) -> MantenimientoSchema:
    """Crea un nuevo mantenimiento"""
    # Verificar que la máquina existe
    maquina = session.query(Maquina).filter(Maquina.id == mantenimiento.maquina_id).first()
    if not maquina:
        raise HTTPException(status_code=404, detail="Máquina no encontrada")
    
    # Crear el mantenimiento
    db_mantenimiento = Mantenimiento(**mantenimiento.dict())
    session.add(db_mantenimiento)
    session.commit()
    session.refresh(db_mantenimiento)
    
    if maquina.horas_maquina is None:
        maquina.horas_maquina = 0
        
    # Actualizar las horas de máquina
    maquina.horas_maquina += mantenimiento.horas_maquina
    session.commit()
    
    return MantenimientoSchema.from_orm(db_mantenimiento)

def get_mantenimiento(session: Session, mantenimiento_id: int) -> Optional[MantenimientoSchema]:
    """Obtiene un mantenimiento por ID"""
    mantenimiento = session.query(Mantenimiento).filter(
        Mantenimiento.id == mantenimiento_id
    ).first()
    
    if mantenimiento:
        return MantenimientoSchema.from_orm(mantenimiento)
    return None

def update_mantenimiento(session: Session, mantenimiento_id: int, mantenimiento_update: MantenimientoCreate) -> Optional[MantenimientoSchema]:
    """Actualiza un mantenimiento existente"""
    db_mantenimiento = session.query(Mantenimiento).filter(
        Mantenimiento.id == mantenimiento_id
    ).first()
    
    if not db_mantenimiento:
        return None
    
    # Guardar las horas anteriores para ajustar en la máquina
    horas_anteriores = db_mantenimiento.horas_maquina
    
    # Actualizar los campos
    for field, value in mantenimiento_update.dict().items():
        setattr(db_mantenimiento, field, value)
    
    session.commit()
    session.refresh(db_mantenimiento)
    
    # Ajustar las horas de máquina
    maquina = session.query(Maquina).filter(Maquina.id == db_mantenimiento.maquina_id).first()
    if maquina:
         if maquina.horas_maquina is None:
        maquina.horas_maquina = 0

        maquina.horas_maquina = maquina.horas_maquina - horas_anteriores + mantenimiento_update.horas_maquina
        session.commit()
    
    return MantenimientoSchema.from_orm(db_mantenimiento)

def delete_mantenimiento(session: Session, mantenimiento_id: int) -> bool:
    """Elimina un mantenimiento"""
    db_mantenimiento = session.query(Mantenimiento).filter(
        Mantenimiento.id == mantenimiento_id
    ).first()
    
    if not db_mantenimiento:
        return False
    
    # Ajustar las horas de máquina antes de eliminar
    maquina = session.query(Maquina).filter(Maquina.id == db_mantenimiento.maquina_id).first()
    if maquina:
        
         if maquina.horas_maquina is None:
        maquina.horas_maquina = 0

        maquina.horas_maquina -= db_mantenimiento.horas_maquina
        session.commit()
    
    session.delete(db_mantenimiento)
    session.commit()
    return True
