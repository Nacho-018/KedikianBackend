from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.schemas.schemas import GastoSchema
from app.services.gasto_service import (
    get_gastos as service_get_gastos,
    get_gasto as service_get_gasto,
    create_gasto as service_create_gasto,
    update_gasto as service_update_gasto,
    delete_gasto as service_delete_gasto,
    get_total_combustible_mes_actual,
    get_all_gastos_paginated
)
from app.security.auth import get_current_user

router = APIRouter(prefix="/gastos", tags=["Gastos"], dependencies=[Depends(get_current_user)])

# ================================
# MODELOS
# ================================
class GastoCreateJSON(BaseModel):
    usuario_id: int
    maquina_id: Optional[int] = None
    tipo: str
    importe_total: float
    fecha: str
    descripcion: str = ""

# ================================
# FUNCIONES AUXILIARES
# ================================
def convert_form_data(
    usuario_id: str,
    tipo: str,
    importe_total: str,
    fecha: str,
    maquina_id: Optional[str] = None,
    descripcion: str = ""
):
    """Convierte los datos de FormData a los tipos correctos"""
    try:
        usuario_id_int = int(usuario_id)
        importe_total_float = float(importe_total)
        maquina_id_int = None
        if maquina_id is not None and maquina_id not in ["", "null"]:
            maquina_id_int = int(maquina_id)
        return {
            "usuario_id": usuario_id_int,
            "tipo": tipo,
            "importe_total": importe_total_float,
            "fecha": fecha,
            "maquina_id": maquina_id_int,
            "descripcion": descripcion or ""
        }
    except ValueError as e:
        raise HTTPException(
            status_code=422, 
            detail=f"Error de conversión de datos: {str(e)}"
        )

# ================================
# ENDPOINTS
# ================================

# GET todos los gastos
@router.get("/", response_model=List[GastoSchema])
def get_gastos(session: Session = Depends(get_db)):
    return service_get_gastos(session)

# GET gasto por id
@router.get("/{id}", response_model=GastoSchema)
def get_gasto(id: int, session: Session = Depends(get_db)):
    gasto = service_get_gasto(session, id)
    if gasto:
        return gasto
    raise HTTPException(status_code=404, detail="Gasto no encontrado")

# CREATE gasto desde JSON (Angular / frontend)
@router.post("/json", response_model=GastoSchema, status_code=201)
def create_gasto_json(gasto_data: GastoCreateJSON, session: Session = Depends(get_db)):
    try:
        converted_data = convert_form_data(
            str(gasto_data.usuario_id),
            gasto_data.tipo,
            str(gasto_data.importe_total),
            gasto_data.fecha,
            str(gasto_data.maquina_id) if gasto_data.maquina_id is not None else None,
            gasto_data.descripcion
        )
        return service_create_gasto(
            session,
            converted_data["usuario_id"],
            converted_data["maquina_id"],
            converted_data["tipo"],
            converted_data["importe_total"],
            converted_data["fecha"],
            converted_data["descripcion"],
            None  # JSON no incluye imagen
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear gasto JSON: {str(e)}")

# CREATE gasto desde FormData (con imagen)
@router.post("/", response_model=GastoSchema, status_code=201)
async def create_gasto_form(
    usuario_id: int = Form(...),  # ← Cambiar de str a int
    tipo: str = Form(...),
    importe_total: float = Form(...),  # ← Cambiar de str a float
    fecha: str = Form(...),
    maquina_id: Optional[int] = Form(None),  # ← Cambiar de str a int
    descripcion: str = Form(""),
    imagen: Optional[UploadFile] = File(None),
    session: Session = Depends(get_db)
):
    try:
        return service_create_gasto(
            session,
            usuario_id,  # Ya es int
            maquina_id,  # Ya es int o None
            tipo,
            importe_total,  # Ya es float
            fecha,
            descripcion,
            imagen
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear gasto FormData: {str(e)}")

# UPDATE gasto
@router.put("/{id}", response_model=GastoSchema)
async def update_gasto(
    id: int,
    usuario_id: int = Form(...),  # ← Cambiar de str a int
    tipo: str = Form(...),
    importe_total: float = Form(...),  # ← Cambiar de str a float
    fecha: str = Form(...),
    maquina_id: Optional[int] = Form(None),  # ← Cambiar de str a int
    descripcion: str = Form(""),
    imagen: Optional[UploadFile] = File(None),
    session: Session = Depends(get_db)
):
    try:
        return service_update_gasto(
            session,
            id,
            usuario_id,  # Ya es int
            maquina_id,  # Ya es int o None
            tipo,
            importe_total,  # Ya es float
            fecha,
            descripcion,
            imagen
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar gasto: {str(e)}")

# DELETE gasto
@router.delete("/{id}")
def delete_gasto(id: int, session: Session = Depends(get_db)):
    try:
        deleted = service_delete_gasto(session, id)
        if deleted:
            return {"message": "Gasto eliminado"}
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar gasto: {str(e)}")

# TOTAL combustible mes actual
@router.get("/combustible-mes-actual")
def total_combustible_mes_actual(session: Session = Depends(get_db)):
    total = get_total_combustible_mes_actual(session)
    return {"total_combustible_mes_actual": total}

# GASTOS paginados
@router.get("/paginado")
def gastos_paginado(skip: int = 0, limit: int = 15, session: Session = Depends(get_db)):
    return get_all_gastos_paginated(session, skip=skip, limit=limit)
