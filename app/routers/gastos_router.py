from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List, Optional, Union
from pydantic import BaseModel, ValidationError
from app.db.dependencies import get_db
from app.schemas.schemas import GastoSchema, GastoCreate
from sqlalchemy.orm import Session
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

# ✅ DEFINIR MODELOS PRIMERO
class GastoCreateJSON(BaseModel):
    usuario_id: int
    maquina_id: Optional[int] = None
    tipo: str
    importe_total: float
    fecha: str
    descripcion: str = ""

# Función auxiliar para convertir strings a tipos correctos
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
        # Convertir usuario_id
        usuario_id_int = int(usuario_id)
        
        # Convertir importe_total
        importe_total_float = float(importe_total)
        
        # Convertir maquina_id si existe
        maquina_id_int = None
        if maquina_id is not None and maquina_id != "" and maquina_id != "null":
            maquina_id_int = int(maquina_id)
        
        # Descripción por defecto si está vacía
        descripcion_final = descripcion if descripcion else ""
        
        return {
            "usuario_id": usuario_id_int,
            "tipo": tipo,
            "importe_total": importe_total_float,
            "fecha": fecha,
            "maquina_id": maquina_id_int,
            "descripcion": descripcion_final
        }
    except ValueError as e:
        raise HTTPException(
            status_code=422, 
            detail=f"Error de conversión de datos: {str(e)}"
        )

# Endpoints Gastos

@router.get("/", response_model=List[GastoSchema])
def get_gastos(session: Session = Depends(get_db)):
    return service_get_gastos(session)

@router.get("/{id}", response_model=GastoSchema)
def get_gasto(id: int, session: Session = Depends(get_db)):
    gasto = service_get_gasto(session, id)
    if gasto:
        return gasto
    else:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")

# ✅ ENDPOINT JSON PARA FRONTEND ANGULAR
@router.post("/json", response_model=GastoSchema, status_code=201)
def create_gasto_json(gasto_data: GastoCreateJSON, session: Session = Depends(get_db)):
    """Crear gasto desde JSON (para frontend Angular)"""
    try:
        print("🔍 === DEBUG GASTO JSON ===")
        print(f"usuario_id: {gasto_data.usuario_id}")
        print(f"maquina_id: {gasto_data.maquina_id}")
        print(f"tipo: {gasto_data.tipo}")
        print(f"importe_total: {gasto_data.importe_total}")
        print(f"fecha: {gasto_data.fecha}")
        print(f"descripcion: {gasto_data.descripcion}")
        print("=============================")
        
        return service_create_gasto(
            session,
            gasto_data.usuario_id,
            gasto_data.maquina_id,
            gasto_data.tipo,
            gasto_data.importe_total,
            gasto_data.fecha,
            gasto_data.descripcion,
            None  # Sin imagen para JSON
        )
    except Exception as e:
        print(f"❌ Error al crear gasto JSON: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al crear gasto: {str(e)}")

# ✅ ENDPOINT FORMDATA CORREGIDO - RECIBE TODO COMO STRING Y CONVIERTE
@router.post("/", response_model=GastoSchema, status_code=201)
def create_gasto(
    usuario_id: str = Form(...),  # ✅ Recibir como string
    tipo: str = Form(...),
    importe_total: str = Form(...),  # ✅ Recibir como string
    fecha: str = Form(...),
    maquina_id: Optional[str] = Form(None),  # ✅ Recibir como string opcional
    descripcion: str = Form(""),
    imagen: Optional[UploadFile] = File(None),
    session: Session = Depends(get_db)
):
    try:
        print("🔍 === DEBUG FORMDATA GASTO (RAW) ===")
        print(f"usuario_id: '{usuario_id}' (tipo: {type(usuario_id)})")
        print(f"maquina_id: '{maquina_id}' (tipo: {type(maquina_id)})")
        print(f"tipo: '{tipo}'")
        print(f"importe_total: '{importe_total}' (tipo: {type(importe_total)})")
        print(f"fecha: '{fecha}'")
        print(f"descripcion: '{descripcion}'")
        print(f"imagen: {imagen}")
        print("====================================")
        
        # ✅ Convertir datos usando función auxiliar
        converted_data = convert_form_data(
            usuario_id, tipo, importe_total, fecha, maquina_id, descripcion
        )
        
        print("🔍 === DATOS CONVERTIDOS ===")
        for key, value in converted_data.items():
            print(f"{key}: {value} (tipo: {type(value)})")
        print("============================")
        
        return service_create_gasto(
            session,
            converted_data["usuario_id"],
            converted_data["maquina_id"],
            converted_data["tipo"],
            converted_data["importe_total"],
            converted_data["fecha"],
            converted_data["descripcion"],
            imagen
        )
        
    except HTTPException:
        raise  # Re-raise HTTPExceptions
    except ValidationError as e:
        print(f"❌ Error de validación: {str(e)}")
        raise HTTPException(status_code=422, detail=f"Error de validación: {str(e)}")
    except Exception as e:
        print(f"❌ Error al crear gasto: {str(e)}")
        print(f"❌ Tipo de error: {type(e)}")
        raise HTTPException(status_code=500, detail=f"Error al crear gasto: {str(e)}")

# ✅ ENDPOINT PUT CORREGIDO
@router.put("/{id}", response_model=GastoSchema)
def update_gasto(
    id: int,
    usuario_id: str = Form(...),  # ✅ Recibir como string
    tipo: str = Form(...),
    importe_total: str = Form(...),  # ✅ Recibir como string
    fecha: str = Form(...),
    maquina_id: Optional[str] = Form(None),  # ✅ Recibir como string opcional
    descripcion: str = Form(""),
    imagen: Optional[UploadFile] = File(None),
    session: Session = Depends(get_db)
):
    try:
        print("🔍 === DEBUG UPDATE GASTO ===")
        print(f"id: {id}")
        print(f"usuario_id: '{usuario_id}'")
        print(f"maquina_id: '{maquina_id}'")
        print(f"tipo: '{tipo}'")
        print(f"importe_total: '{importe_total}'")
        print(f"fecha: '{fecha}'")
        print(f"descripcion: '{descripcion}'")
        print("=============================")
        
        # ✅ Convertir datos
        converted_data = convert_form_data(
            usuario_id, tipo, importe_total, fecha, maquina_id, descripcion
        )
        
        return service_update_gasto(
            session,
            id,
            converted_data["usuario_id"],
            converted_data["maquina_id"],
            converted_data["tipo"],
            converted_data["importe_total"],
            converted_data["fecha"],
            converted_data["descripcion"],
            imagen
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al actualizar gasto: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar gasto: {str(e)}")

@router.delete("/{id}")
def delete_gasto(id: int, session: Session = Depends(get_db)):
    try:
        deleted = service_delete_gasto(session, id)
        if deleted:
            return {"message": "Gasto eliminado"}
        else:
            raise HTTPException(status_code=404, detail="Gasto no encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar gasto: {str(e)}")

# Endpoint para total de gasto en combustible en el mes actual
@router.get("/combustible-mes-actual")
def total_combustible_mes_actual(session: Session = Depends(get_db)):
    total = get_total_combustible_mes_actual(session)
    return {"total_combustible_mes_actual": total}

@router.get("/paginado")
def gastos_paginado(skip: int = 0, limit: int = 15, session: Session = Depends(get_db)):
    return get_all_gastos_paginated(session, skip=skip, limit=limit)