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
    get_suma_material_mes_actual,
    get_all_entregas_arido_paginated
)
from app.security.auth import get_current_user

# ← CORREGIDO: Agregada la ruta /aridos/registros para compatibilidad
router = APIRouter(prefix="/aridos", tags=["Entregas de Arido"], dependencies=[Depends(get_current_user)])

# IMPORTANTE: Las rutas con query params van PRIMERO
@router.get("/registros/suma-mes-actual")
def suma_material_mes_actual(db: Session = Depends(get_db)):
    """Suma de material entregado en el mes actual"""
    suma = get_suma_material_mes_actual(db)
    return {"suma_material_mes_actual": suma}

@router.get("/registros/paginado")
def entregas_arido_paginado(skip: int = 0, limit: int = 15, db: Session = Depends(get_db)):
    """Lista paginada de entregas de áridos"""
    return get_all_entregas_arido_paginated(db, skip=skip, limit=limit)

# ← RUTA PRINCIPAL QUE ESTABA FALTANDO
@router.get("/registros", response_model=List[EntregaAridoOut])
def read_all_registros(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Obtiene todos los registros de áridos - RUTA QUE LLAMA EL FRONTEND"""
    try:
        return get_all_entregas_arido(db, skip=skip, limit=limit)
    except Exception as e:
        print(f"Error en /registros: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al obtener registros: {str(e)}")

@router.post("/registros", response_model=EntregaAridoOut)
def create_registro(entrega: EntregaAridoCreate, db: Session = Depends(get_db)):
    """Crea un nuevo registro de árido"""
    try:
        return create_entrega_arido(db, entrega)
    except Exception as e:
        print(f"Error al crear registro: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al crear registro: {str(e)}")

@router.get("/registros/{entrega_id}", response_model=EntregaAridoOut)
def read_one_registro(entrega_id: int, db: Session = Depends(get_db)):
    """Obtiene un registro específico"""
    entrega = get_entrega_arido(db, entrega_id)
    if not entrega:
        raise HTTPException(status_code=404, detail="Entrega de árido no encontrada")
    return entrega

@router.put("/registros/{entrega_id}", response_model=EntregaAridoOut)
def update_registro(entrega_id: int, entrega: EntregaAridoCreate, db: Session = Depends(get_db)):
    """Actualiza un registro existente"""
    try:
        updated = update_entrega_arido(db, entrega_id, entrega)
        if not updated:
            raise HTTPException(status_code=404, detail="Entrega de árido no encontrada")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al actualizar: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {str(e)}")

@router.delete("/registros/{entrega_id}", response_model=bool)
def delete_registro(entrega_id: int, db: Session = Depends(get_db)):
    """Elimina un registro"""
    try:
        deleted = delete_entrega_arido(db, entrega_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Entrega de árido no encontrada")
        return deleted
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al eliminar: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar: {str(e)}")
