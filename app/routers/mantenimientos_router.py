from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from app.db.dependencies import get_db
from app.schemas.schemas import (
    MantenimientoSchema, MantenimientoCreate, MantenimientoOut
)
from sqlalchemy.orm import Session
from app.services.mantenimiento_service import (
    get_mantenimientos_maquina,
    create_mantenimiento,
    get_mantenimiento,
    update_mantenimiento,
    delete_mantenimiento
)
from app.security.auth import get_current_user

router = APIRouter(prefix="/mantenimientos", tags=["Mantenimientos"], dependencies=[Depends(get_current_user)])

# Endpoint específico para obtener mantenimientos de una máquina
@router.get("/maquina/{maquina_id}", response_model=List[MantenimientoOut])
def get_mantenimientos_por_maquina(maquina_id: int, session: Session = Depends(get_db)):
    """
    Obtiene todos los mantenimientos de una máquina específica
    """
    try:
        mantenimientos = get_mantenimientos_maquina(session, maquina_id)
        return mantenimientos
    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(
            content={"error": f"Error interno del servidor: {str(e)}"}, 
            status_code=500
        )

# Endpoints generales para mantenimientos
@router.get("/", response_model=List[MantenimientoOut])
def get_all_mantenimientos(session: Session = Depends(get_db)):
    """
    Obtiene todos los mantenimientos
    """
    from app.db.models.mantenimiento import Mantenimiento
    mantenimientos = session.query(Mantenimiento).order_by(Mantenimiento.fecha_mantenimiento.desc()).all()
    return [MantenimientoOut.from_orm(m) for m in mantenimientos]

@router.get("/{mantenimiento_id}", response_model=MantenimientoOut)
def get_mantenimiento_by_id(mantenimiento_id: int, session: Session = Depends(get_db)):
    """
    Obtiene un mantenimiento por ID
    """
    mantenimiento = get_mantenimiento(session, mantenimiento_id)
    if mantenimiento:
        return mantenimiento
    else:
        return JSONResponse(content={"error": "Mantenimiento no encontrado"}, status_code=404)

@router.post("/", response_model=MantenimientoOut, status_code=201)
def create_new_mantenimiento(mantenimiento: MantenimientoCreate, session: Session = Depends(get_db)):
    """
    Crea un nuevo mantenimiento
    """
    try:
        return create_mantenimiento(session, mantenimiento)
    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(
            content={"error": f"Error interno del servidor: {str(e)}"}, 
            status_code=500
        )

@router.put("/{mantenimiento_id}", response_model=MantenimientoOut)
def update_mantenimiento_by_id(mantenimiento_id: int, mantenimiento: MantenimientoCreate, session: Session = Depends(get_db)):
    """
    Actualiza un mantenimiento existente
    """
    try:
        updated = update_mantenimiento(session, mantenimiento_id, mantenimiento)
        if updated:
            return updated
        else:
            return JSONResponse(content={"error": "Mantenimiento no encontrado"}, status_code=404)
    except HTTPException as e:
        raise e
    except Exception as e:
        return JSONResponse(
            content={"error": f"Error interno del servidor: {str(e)}"}, 
            status_code=500
        )

@router.delete("/{mantenimiento_id}")
def delete_mantenimiento_by_id(mantenimiento_id: int, session: Session = Depends(get_db)):
    """
    Elimina un mantenimiento
    """
    try:
        deleted = delete_mantenimiento(session, mantenimiento_id)
        if deleted:
            return {"message": "Mantenimiento eliminado correctamente"}
        else:
            return JSONResponse(content={"error": "Mantenimiento no encontrado"}, status_code=404)
    except Exception as e:
        return JSONResponse(
            content={"error": f"Error interno del servidor: {str(e)}"}, 
            status_code=500
        )
