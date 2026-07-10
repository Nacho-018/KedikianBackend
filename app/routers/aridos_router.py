from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.db.dependencies import get_db
from app.schemas.schemas import EntregaAridoCreate, EntregaAridoOut
from app.db.models.entrega_arido import EntregaArido
from app.services.entrega_arido_service import (
    create_entrega_arido,
    get_entrega_arido,
    get_all_entregas_arido,
    update_entrega_arido,
    delete_entrega_arido,
    normalizar_tipo_arido,
)

router = APIRouter(prefix="/aridos", tags=["Áridos"])

class TipoArido(BaseModel):
    id: int
    nombre: str
    tipo: str
    unidadMedida: str

@router.get("/tipos")
async def get_tipos_aridos():
    try:
        tipos = [
            { "id": 1, "nombre": "Arena Fina", "tipo": "árido", "unidadMedida": "m3" },
            { "id": 2, "nombre": "Granza", "tipo": "árido", "unidadMedida": "m3" },
            { "id": 3, "nombre": "Arena Comun", "tipo": "árido", "unidadMedida": "m3" },
            { "id": 4, "nombre": "Relleno", "tipo": "árido", "unidadMedida": "m3" },
            { "id": 5, "nombre": "Tierra Negra", "tipo": "árido", "unidadMedida": "m3" },
            { "id": 6, "nombre": "Piedra", "tipo": "árido", "unidadMedida": "m3" },
            { "id": 7, "nombre": "0.20", "tipo": "árido", "unidadMedida": "m3" },
            { "id": 8, "nombre": "Blinder", "tipo": "árido", "unidadMedida": "m3" },
            { "id": 9, "nombre": "Arena Lavada", "tipo": "árido", "unidadMedida": "m3" },
            { "id": 10, "nombre": "Poda/Ramas", "tipo": "árido", "unidadMedida": "m3" }
        ]
        return tipos
    except Exception as e:
        return {"error": str(e)}

@router.get("/registros", response_model=List[EntregaAridoOut])
async def get_registros_aridos(db: Session = Depends(get_db)):
    """Obtiene todos los registros de entrega de áridos"""
    try:
        registros = get_all_entregas_arido(db)
        return registros
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener registros: {str(e)}")

@router.post("/registros", response_model=EntregaAridoOut)
async def crear_registro_arido(
    registro: EntregaAridoCreate,
    db: Session = Depends(get_db)
):
    """Crea un nuevo registro de entrega de áridos"""
    try:
        return create_entrega_arido(db, registro)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear registro: {str(e)}")

@router.get("/registros/{id}", response_model=EntregaAridoOut)
async def get_registro_arido(id: int, db: Session = Depends(get_db)):
    """Obtiene un registro específico de entrega de áridos"""
    try:
        registro = get_entrega_arido(db, id)
        if not registro:
            raise HTTPException(status_code=404, detail="Registro no encontrado")
        return registro
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener registro: {str(e)}")

@router.put("/registros/{id}", response_model=EntregaAridoOut)
async def actualizar_registro_arido(
    id: int,
    registro: EntregaAridoCreate,
    db: Session = Depends(get_db)
):
    """Actualiza un registro de entrega de áridos"""
    try:
        registro_actualizado = update_entrega_arido(db, id, registro)
        if not registro_actualizado:
            raise HTTPException(status_code=404, detail="Registro no encontrado")
        return registro_actualizado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar registro: {str(e)}")

@router.delete("/registros/{id}")
async def eliminar_registro_arido(id: int, db: Session = Depends(get_db)):
    """Elimina un registro de entrega de áridos"""
    try:
        eliminado = delete_entrega_arido(db, id)
        if not eliminado:
            raise HTTPException(status_code=404, detail="Registro no encontrado")
        return {"message": "Registro eliminado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar registro: {str(e)}")


@router.post("/normalizar-tipos")
async def normalizar_tipos_aridos(db: Session = Depends(get_db)):
    """
    Consolida los tipos de árido de registros existentes: quita '(m3)'/'(m³)' y
    espacios extra para que el panel operario y el panel admin queden alineados.
    Retorna cuántos registros se renombraron por tipo.
    """
    try:
        registros = db.query(EntregaArido).all()
        cambios: dict[str, dict] = {}
        actualizados = 0
        for r in registros:
            original = r.tipo_arido
            if original is None:
                continue
            normalizado = normalizar_tipo_arido(original)
            if normalizado != original:
                r.tipo_arido = normalizado
                actualizados += 1
                key = f"{original} -> {normalizado}"
                cambios.setdefault(key, {"cantidad": 0})
                cambios[key]["cantidad"] += 1
        db.commit()
        return {"registros_actualizados": actualizados, "detalle": cambios}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al normalizar tipos: {str(e)}")
