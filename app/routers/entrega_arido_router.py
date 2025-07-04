from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.dependencies import get_db
from app.schemas.schemas import EntregaAridoCreate, EntregaAridoOut
from app.services.entrega_arido_service import (
    create_entrega_arido,
    get_entrega_arido,
    get_all_entregas_arido,
    update_entrega_arido,
    delete_entrega_arido,
)

router = APIRouter(prefix="/entregas-arido", tags=["Entregas de Arido"])

@router.post("/", response_model=EntregaAridoOut)
def create(entrega: EntregaAridoCreate, db: Session = Depends(get_db)):
    return create_entrega_arido(db, entrega)

@router.get("/", response_model=List[EntregaAridoOut])
def read_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_all_entregas_arido(db, skip=skip, limit=limit)

@router.get("/{entrega_id}", response_model=EntregaAridoOut)
def read_one(entrega_id: int, db: Session = Depends(get_db)):
    entrega = get_entrega_arido(db, entrega_id)
    if not entrega:
        raise HTTPException(status_code=404, detail="Entrega de árido no encontrada")
    return entrega

@router.put("/{entrega_id}", response_model=EntregaAridoOut)
def update(entrega_id: int, entrega: EntregaAridoCreate, db: Session = Depends(get_db)):
    updated = update_entrega_arido(db, entrega_id, entrega)
    if not updated:
        raise HTTPException(status_code=404, detail="Entrega de árido no encontrada")
    return updated

@router.delete("/{entrega_id}", response_model=bool)
def delete(entrega_id: int, db: Session = Depends(get_db)):
    deleted = delete_entrega_arido(db, entrega_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entrega de árido no encontrada")
    return deleted
