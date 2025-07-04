# Servicio para operaciones de Gasto

from app.db.models import Gasto
from app.schemas.schemas import GastoSchema, GastoCreate, GastoOut
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError

def get_gastos(db: Session) -> List[GastoOut]:
    try:
        gastos = db.query(Gasto).all()
        return [GastoOut(
            id=g.id,
            usuario_id=g.usuario_id,
            maquina_id=g.maquina_id,
            tipo=g.tipo,
            importe_total=g.importe_total,
            fecha=g.fecha,
            descripcion=g.descripcion,
            imagen=g.imagen
        ) for g in gastos]
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error al obtener gastos: {str(e)}")

def get_gasto(db: Session, gasto_id: int) -> Optional[GastoOut]:
    try:
        g = db.query(Gasto).filter(Gasto.id == gasto_id).first()
        if g:
            return GastoOut(
                id=g.id,
                usuario_id=g.usuario_id,
                maquina_id=g.maquina_id,
                tipo=g.tipo,
                importe_total=g.importe_total,
                fecha=g.fecha,
                descripcion=g.descripcion,
                imagen=g.imagen
            )
        return None
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error al obtener gasto: {str(e)}")

def create_gasto(db: Session, gasto: GastoCreate) -> GastoOut:
    try:
        # Filtrar campos None para evitar problemas con la base de datos
        gasto_data = gasto.model_dump()
        gasto_data = {k: v for k, v in gasto_data.items() if v is not None}
        
        nuevo_gasto = Gasto(**gasto_data)
        db.add(nuevo_gasto)
        db.commit()
        db.refresh(nuevo_gasto)
        return GastoOut(
            id=nuevo_gasto.id,
            usuario_id=nuevo_gasto.usuario_id,
            maquina_id=nuevo_gasto.maquina_id,
            tipo=nuevo_gasto.tipo,
            importe_total=nuevo_gasto.importe_total,
            fecha=nuevo_gasto.fecha,
            descripcion=nuevo_gasto.descripcion,
            imagen=nuevo_gasto.imagen
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error al crear gasto: {str(e)}")

def update_gasto(db: Session, gasto_id: int, gasto: GastoSchema) -> Optional[GastoOut]:
    try:
        existing_gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
        if existing_gasto:
            # Filtrar campos None y el campo id para evitar problemas
            gasto_data = gasto.model_dump()
            gasto_data = {k: v for k, v in gasto_data.items() if v is not None and k != 'id'}
            
            for field, value in gasto_data.items():
                setattr(existing_gasto, field, value)
            
            db.commit()
            db.refresh(existing_gasto)
            return GastoOut(
                id=existing_gasto.id,
                usuario_id=existing_gasto.usuario_id,
                maquina_id=existing_gasto.maquina_id,
                tipo=existing_gasto.tipo,
                importe_total=existing_gasto.importe_total,
                fecha=existing_gasto.fecha,
                descripcion=existing_gasto.descripcion,
                imagen=existing_gasto.imagen
            )
        return None
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error al actualizar gasto: {str(e)}")

def delete_gasto(db: Session, gasto_id: int) -> bool:
    try:
        gasto = db.query(Gasto).filter(Gasto.id == gasto_id).first()
        if gasto:
            db.delete(gasto)
            db.commit()
            return True
        return False
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error al eliminar gasto: {str(e)}")
