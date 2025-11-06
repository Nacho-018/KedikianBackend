from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.dependencies import get_db
from app.db.models import Gasto
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

# GET todos los gastos CON FILTRO DE FECHAS (igual que pagos)
@router.get("/", response_model=List[GastoSchema])
def get_gastos(
    fechaInicio: Optional[datetime] = Query(None),
    fechaFin: Optional[datetime] = Query(None),
    session: Session = Depends(get_db)
):
    """
    Obtener gastos con filtro opcional de fechas.
    Funciona exactamente igual que el endpoint de pagos.
    """
    try:
        query = session.query(Gasto)
        if fechaInicio:
            query = query.filter(Gasto.fecha >= fechaInicio)
        if fechaFin:
            query = query.filter(Gasto.fecha <= fechaFin)
        gastos = query.order_by(Gasto.fecha.desc()).all()
        return [GastoSchema.from_orm(g) for g in gastos]
    except Exception as e:
        print(f"❌ Error al obtener gastos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener gastos: {str(e)}")


# GET gasto por id
@router.get("/{id}", response_model=GastoSchema)
def get_gasto(id: int, session: Session = Depends(get_db)):
    gasto = service_get_gasto(session, id)
    if gasto:
        return gasto
    raise HTTPException(status_code=404, detail="Gasto no encontrado")


# CREATE gasto desde JSON (Angular / frontend)
@router.post("/json", response_model=GastoSchema, status_code=201)
async def create_gasto_json(
    gasto_data: GastoCreateJSON,
    session: Session = Depends(get_db)
):
    """Crear gasto desde JSON (usado por Angular)"""
    try:
        # Parsear fecha correctamente
        fecha_str = gasto_data.fecha.replace('Z', '+00:00')
        try:
            fecha_parsed = datetime.fromisoformat(fecha_str)
        except ValueError:
            fecha_parsed = datetime.strptime(gasto_data.fecha.split('T')[0], '%Y-%m-%d')
        
        # Crear gasto
        nuevo_gasto = Gasto(
            usuario_id=gasto_data.usuario_id,
            maquina_id=gasto_data.maquina_id,
            tipo=gasto_data.tipo,
            importe_total=gasto_data.importe_total,
            fecha=fecha_parsed,
            descripcion=gasto_data.descripcion,
            imagen=None
        )
        
        session.add(nuevo_gasto)
        session.commit()
        session.refresh(nuevo_gasto)
        
        return GastoSchema.from_orm(nuevo_gasto)
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error creando gasto: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al crear gasto: {str(e)}")


# CREATE gasto desde FormData (con imagen)
@router.post("/", response_model=GastoSchema, status_code=201)
async def create_gasto_form(
    usuario_id: int = Form(...),
    tipo: str = Form(...),
    importe_total: float = Form(...),
    fecha: str = Form(...),
    maquina_id: Optional[int] = Form(None),
    descripcion: str = Form(""),
    imagen: Optional[UploadFile] = File(None),
    session: Session = Depends(get_db)
):
    try:
        return service_create_gasto(
            session,
            usuario_id,
            maquina_id,
            tipo,
            importe_total,
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
    usuario_id: int = Form(...),
    tipo: str = Form(...),
    importe_total: float = Form(...),
    fecha: str = Form(...),
    maquina_id: Optional[int] = Form(None),
    descripcion: str = Form(""),
    imagen: Optional[UploadFile] = File(None),
    session: Session = Depends(get_db)
):
    try:
        return service_update_gasto(
            session,
            id,
            usuario_id,
            maquina_id,
            tipo,
            importe_total,
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
@router.get("/estadisticas/combustible-mes-actual")
def total_combustible_mes_actual(session: Session = Depends(get_db)):
    total = get_total_combustible_mes_actual(session)
    return {"total_combustible_mes_actual": total}


# GASTOS paginados
@router.get("/paginado/lista")
def gastos_paginado(skip: int = 0, limit: int = 15, session: Session = Depends(get_db)):
    return get_all_gastos_paginated(session, skip=skip, limit=limit)