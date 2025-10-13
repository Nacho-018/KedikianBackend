from sqlalchemy.orm import Session
from app.db.models.entrega_arido import EntregaArido
from app.schemas.schemas import EntregaAridoCreate, EntregaAridoOut
from typing import List, Optional
from datetime import datetime
from sqlalchemy import extract, func
from fastapi import HTTPException
import traceback

def create_entrega_arido(db: Session, entrega_data: EntregaAridoCreate) -> EntregaAridoOut:
    try:
        entrega = EntregaArido(**entrega_data.dict())
        db.add(entrega)
        db.commit()
        db.refresh(entrega)
        return EntregaAridoOut.model_validate(entrega)
    except Exception as e:
        db.rollback()
        print(f"Error creando entrega: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al crear entrega: {str(e)}")

def get_entrega_arido(db: Session, entrega_id: int) -> Optional[EntregaAridoOut]:
    try:
        entrega = db.query(EntregaArido).filter(EntregaArido.id == entrega_id).first()
        if entrega:
            return EntregaAridoOut.model_validate(entrega)
        return None
    except Exception as e:
        print(f"Error obteniendo entrega {entrega_id}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener entrega: {str(e)}")

def get_all_entregas_arido(db: Session, skip: int = 0, limit: int = 100) -> List[EntregaAridoOut]:
    try:
        # Eager loading de las relaciones para evitar errores
        entregas = db.query(EntregaArido).offset(skip).limit(limit).all()
        
        # Validar cada entrega
        result = []
        for entrega in entregas:
            try:
                validated = EntregaAridoOut.model_validate(entrega)
                result.append(validated)
            except Exception as e:
                print(f"Error validando entrega {entrega.id}: {str(e)}")
                # Continuar con las demás
                continue
        
        return result
    except Exception as e:
        print(f"Error en get_all_entregas_arido: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener entregas: {str(e)}")

def update_entrega_arido(db: Session, entrega_id: int, entrega_data: EntregaAridoCreate) -> Optional[EntregaAridoOut]:
    try:
        entrega = db.query(EntregaArido).filter(EntregaArido.id == entrega_id).first()
        if not entrega:
            return None
        
        for key, value in entrega_data.dict(exclude_unset=True).items():
            setattr(entrega, key, value)
        
        db.commit()
        db.refresh(entrega)
        return EntregaAridoOut.model_validate(entrega)
    except Exception as e:
        db.rollback()
        print(f"Error actualizando entrega {entrega_id}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")

def delete_entrega_arido(db: Session, entrega_id: int) -> bool:
    try:
        entrega = db.query(EntregaArido).filter(EntregaArido.id == entrega_id).first()
        if not entrega:
            return False
        db.delete(entrega)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error eliminando entrega {entrega_id}: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")

def get_suma_material_mes_actual(db: Session) -> float:
    try:
        now = datetime.now()
        suma = db.query(func.sum(EntregaArido.cantidad)).filter(
            extract('year', EntregaArido.fecha_entrega) == now.year,
            extract('month', EntregaArido.fecha_entrega) == now.month
        ).scalar()
        return float(suma) if suma else 0.0
    except Exception as e:
        print(f"Error calculando suma mes actual: {str(e)}")
        traceback.print_exc()
        return 0.0

def get_all_entregas_arido_paginated(db: Session, skip: int = 0, limit: int = 15) -> dict:
    try:
        total = db.query(EntregaArido).count()
        entregas = db.query(EntregaArido).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": [EntregaAridoOut.model_validate(e) for e in entregas]
        }
    except Exception as e:
        print(f"Error en paginación: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al paginar: {str(e)}")