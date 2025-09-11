from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from app.db.dependencies import get_db
from app.schemas.schemas import (
    MaquinaSchema, RegistroHorasMaquinaCreate, 
    HistorialProyectoOut, CambiarProyectoRequest, CambiarProyectoResponse
)
from sqlalchemy.orm import Session
from app.services.maquina_service import (
    get_maquinas as service_get_maquinas,
    get_maquina as service_get_maquina,
    create_maquina as service_create_maquina,
    update_maquina as service_update_maquina,
    delete_maquina as service_delete_maquina,
    get_all_maquinas_paginated,
    registrar_horas_maquina_proyecto,
    obtener_historial_proyectos_maquina,
    cambiar_proyecto_maquina
)
from app.db.models import ReporteLaboral  # <-- agregado para actualizar/eliminar registros
from app.security.auth import get_current_user

router = APIRouter(prefix="/maquinas", tags=["Maquinas"], dependencies=[Depends(get_current_user)])

# ==================== CRUD MÁQUINAS ====================

@router.get("/", response_model=List[MaquinaSchema])
def get_maquinas(session: Session = Depends(get_db)):
    return service_get_maquinas(session)

@router.get("/{id}", response_model=MaquinaSchema)
def get_maquina(id: int, session: Session = Depends(get_db)):
    maquina = service_get_maquina(session, id)
    if maquina:
        return maquina
    else:
        return JSONResponse(content={"error": "Maquina no encontrada"}, status_code=404)

@router.post("/", response_model=MaquinaSchema, status_code=201)
def create_maquina(maquina: MaquinaSchema, session: Session = Depends(get_db)):
    return service_create_maquina(session, maquina)

@router.put("/{id}", response_model=MaquinaSchema)
def update_maquina(id: int, maquina: MaquinaSchema, session: Session = Depends(get_db)):
    updated = service_update_maquina(session, id, maquina)
    if updated:
        return updated
    else:
        return JSONResponse(content={"error": "Maquina no encontrada"}, status_code=404)

@router.delete("/{id}")
def delete_maquina(id: int, session: Session = Depends(get_db)):
    deleted = service_delete_maquina(session, id)
    if deleted:
        return {"message": "Maquina eliminada"}
    else:
        return JSONResponse(content={"error": "Maquina no encontrada"}, status_code=404)

@router.get("/paginado")
def maquinas_paginado(skip: int = 0, limit: int = 15, session: Session = Depends(get_db)):
    return get_all_maquinas_paginated(session, skip=skip, limit=limit)

# ==================== HORAS EN PROYECTOS ====================

@router.post("/{id}/proyectos/{proyecto_id}/horas", status_code=201)
def registrar_horas_maquina_proyecto_endpoint(
    id: int, 
    proyecto_id: int, 
    registro: RegistroHorasMaquinaCreate, 
    session: Session = Depends(get_db)
):
    """
    Registra horas de uso de una máquina en un proyecto específico
    """
    resultado = registrar_horas_maquina_proyecto(session, id, proyecto_id, registro)
    if resultado:
        return resultado
    else:
        return JSONResponse(
            content={"error": "Máquina, proyecto no encontrados o máquina no asignada al proyecto"}, 
            status_code=404
        )

@router.get("/{id}/proyectos/{proyecto_id}/horas", response_model=List[HistorialProyectoOut])
def obtener_horas_maquina_en_proyecto(
    id: int,
    proyecto_id: int,
    session: Session = Depends(get_db)
):
    """
    Obtiene todas las horas trabajadas de una máquina en un proyecto específico
    """
    historial = obtener_historial_proyectos_maquina(session, id)

    if historial is None:
        return JSONResponse(content={"error": "Máquina no encontrada"}, status_code=404)

    historial_filtrado = [h for h in historial if h.proyecto_id == proyecto_id]

    if not historial_filtrado:
        return JSONResponse(
            content={"error": "No se encontraron registros de horas para este proyecto"},
            status_code=404
        )

    return historial_filtrado

# ==================== HISTORIAL DE PROYECTOS ====================

@router.get("/{id}/historial-proyectos", response_model=List[HistorialProyectoOut])
def obtener_historial_proyectos_maquina_endpoint(
    id: int, 
    session: Session = Depends(get_db)
):
    """
    Obtiene el historial de proyectos de una máquina
    """
    historial = obtener_historial_proyectos_maquina(session, id)
    if historial is not None:
        return historial
    else:
        return JSONResponse(content={"error": "Máquina no encontrada"}, status_code=404)

# ==================== CAMBIAR PROYECTO ====================

@router.put("/{id}/cambiar-proyecto", response_model=CambiarProyectoResponse)
def cambiar_proyecto_maquina_endpoint(
    id: int, 
    cambio: CambiarProyectoRequest, 
    session: Session = Depends(get_db)
):
    """
    Cambia el proyecto asignado a una máquina
    """
    resultado = cambiar_proyecto_maquina(session, id, cambio)
    if resultado:
        return resultado
    else:
        return JSONResponse(
            content={"error": "Máquina o proyecto no encontrados"}, 
            status_code=404
        )

# ==================== REGISTROS DE HORAS (CRUD) ====================

@router.put("/{id}/horas/{registro_id}")
def actualizar_registro_horas(
    id: int,
    registro_id: int,
    datos: RegistroHorasMaquinaCreate,
    session: Session = Depends(get_db)
):
    """
    Actualiza un registro específico de horas de una máquina
    """
    registro = session.query(ReporteLaboral).filter(
        ReporteLaboral.id == registro_id,
        ReporteLaboral.maquina_id == id
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

@router.delete("/{id}/horas/{registro_id}")
def eliminar_registro_horas(
    id: int,
    registro_id: int,
    session: Session = Depends(get_db)
):
    """
    Elimina un registro específico de horas de una máquina
    """
    registro = session.query(ReporteLaboral).filter(
        ReporteLaboral.id == registro_id,
        ReporteLaboral.maquina_id == id
    ).first()

    if not registro:
        return JSONResponse(content={"error": "Registro no encontrado"}, status_code=404)

    session.delete(registro)
    session.commit()

    return {"message": f"Registro {registro_id} eliminado correctamente"}
