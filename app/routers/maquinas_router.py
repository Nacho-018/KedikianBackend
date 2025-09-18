from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.schemas.schemas import (
    MaquinaSchema, MaquinaCreate, RegistroHorasMaquinaCreate,
    HistorialHorasOut, EstadisticasHorasOut, UsuarioOut
)
from app.services.maquina_service import (
    get_maquinas as service_get_maquinas,
    get_maquina as service_get_maquina,
    create_maquina as service_create_maquina,
    update_maquina as service_update_maquina,
    delete_maquina as service_delete_maquina,
    get_all_maquinas_paginated,
    registrar_horas_maquina,
    obtener_historial_horas_maquina,
    obtener_estadisticas_horas_maquina
)
from app.db.models import ReporteLaboral
from app.security.auth import get_current_user

router = APIRouter(prefix="/maquinas", tags=["Maquinas"])

# ==================== CRUD MÁQUINAS ====================

@router.get("/", response_model=List[MaquinaSchema])
def get_maquinas(session: Session = Depends(get_db)):
    return service_get_maquinas(session)

@router.get("/{id}", response_model=MaquinaSchema)
def get_maquina(id: int, session: Session = Depends(get_db)):
    maquina = service_get_maquina(session, id)
    if maquina:
        return maquina
    return JSONResponse(content={"error": "Maquina no encontrada"}, status_code=404)

@router.post("/", response_model=MaquinaSchema, status_code=201)
def create_maquina(maquina: MaquinaCreate, session: Session = Depends(get_db)):
    return service_create_maquina(session, maquina)

@router.put("/{id}", response_model=MaquinaSchema)
def update_maquina(id: int, maquina: MaquinaSchema, session: Session = Depends(get_db)):
    updated = service_update_maquina(session, id, maquina)
    if updated:
        return updated
    return JSONResponse(content={"error": "Maquina no encontrada"}, status_code=404)

@router.delete("/{id}")
def delete_maquina(id: int, session: Session = Depends(get_db)):
    deleted = service_delete_maquina(session, id)
    if deleted:
        return {"message": "Maquina eliminada"}
    return JSONResponse(content={"error": "Maquina no encontrada"}, status_code=404)

@router.get("/paginado")
def maquinas_paginado(skip: int = 0, limit: int = 15, session: Session = Depends(get_db)):
    return get_all_maquinas_paginated(session, skip=skip, limit=limit)

# ==================== HORAS ====================

@router.post("/{maquina_id}/horas", status_code=201)
def registrar_horas(
    maquina_id: int,
    registro: RegistroHorasMaquinaCreate,
    session: Session = Depends(get_db),
    current_user: UsuarioOut = Depends(get_current_user)
):
    """
    Registrar horas de uso de una máquina
    """
    try:
        return registrar_horas_maquina(
            db=session,
            maquina_id=maquina_id,
            registro=registro,
            usuario_id=current_user.id
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

@router.get("/{maquina_id}/horas/historial", response_model=List[HistorialHorasOut])
def historial_horas(maquina_id: int, session: Session = Depends(get_db)):
    """
    Historial completo de horas de una máquina
    """
    return obtener_historial_horas_maquina(session, maquina_id)

@router.get("/{maquina_id}/horas/estadisticas", response_model=Optional[EstadisticasHorasOut])
def estadisticas_horas(
    maquina_id: int,
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    session: Session = Depends(get_db)
):
    """
    Estadísticas de horas trabajadas de una máquina
    """
    return obtener_estadisticas_horas_maquina(session, maquina_id, fecha_inicio, fecha_fin)

# ==================== CRUD DE REGISTROS DE HORAS ====================

@router.put("/{maquina_id}/horas/{registro_id}")
def actualizar_registro_horas(
    maquina_id: int,
    registro_id: int,
    datos: RegistroHorasMaquinaCreate,
    session: Session = Depends(get_db)
):
    registro = session.query(ReporteLaboral).filter(
        ReporteLaboral.id == registro_id,
        ReporteLaboral.maquina_id == maquina_id
    ).first()

    if not registro:
        return JSONResponse(content={"error": "Registro no encontrado"}, status_code=404)

    registro.horas_turno = datos.horas
    registro.fecha_asignacion = datos.fecha
    session.commit()
    session.refresh(registro)

    return {
        "message": f"Registro {registro_id} actualizado correctamente",
        "registro": {
            "id": registro.id,
            "maquina_id": registro.maquina_id,
            "horas": registro.horas_turno,
            "fecha": registro.fecha_asignacion
        }
    }

@router.delete("/{maquina_id}/horas/{registro_id}")
def eliminar_registro_horas(
    maquina_id: int,
    registro_id: int,
    session: Session = Depends(get_db)
):
    registro = session.query(ReporteLaboral).filter(
        ReporteLaboral.id == registro_id,
        ReporteLaboral.maquina_id == maquina_id
    ).first()

    if not registro:
        return JSONResponse(content={"error": "Registro no encontrado"}, status_code=404)

    session.delete(registro)
    session.commit()
    return {"message": f"Registro {registro_id} eliminado correctamente"}
