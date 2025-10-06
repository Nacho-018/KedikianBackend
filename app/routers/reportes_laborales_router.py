from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from app.db.dependencies import get_db
from app.schemas.schemas import (
    ReporteLaboralSchema,
    ReporteLaboralCreate,
    ReporteLaboralOut
)
from sqlalchemy.orm import Session
from app.services.reporte_laboral_service import (
    get_reportes_laborales as service_get_reportes_laborales,
    get_reporte_laboral as service_get_reporte_laboral,
    create_reporte_laboral as service_create_reporte_laboral,
    update_reporte_laboral as service_update_reporte_laboral,
    delete_reporte_laboral as service_delete_reporte_laboral,
    get_total_horas_mes_actual,
    get_all_reportes_laborales_paginated
)
from app.security.auth import get_current_user

router = APIRouter(
    prefix="/reportes-laborales",
    tags=["Reportes Laborales"],
    dependencies=[Depends(get_current_user)]
)

# --------- RUTAS ESPECIALES PRIMERO ---------

@router.get("/horas-mes-actual")
def total_horas_mes_actual(session: Session = Depends(get_db)):
    total = get_total_horas_mes_actual(session)
    return {"total_horas_mes_actual": total}

@router.get("/paginado", response_model=List[ReporteLaboralOut])
def reportes_laborales_paginado(skip: int = 0, limit: int = 15, session: Session = Depends(get_db)):
    return get_all_reportes_laborales_paginated(session, skip=skip, limit=limit)

# --------- CRUD CON FILTROS ---------

@router.get("/", response_model=List[ReporteLaboralOut])
def get_reportes_laborales(
    busqueda: Optional[str] = Query(None, description="Buscar por nombre de máquina"),
    maquina_id: Optional[int] = Query(None, description="Filtrar por ID de máquina"),
    proyecto_id: Optional[int] = Query(None, description="Filtrar por ID de proyecto"),
    usuario_id: Optional[int] = Query(None, description="Filtrar por ID de usuario"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    session: Session = Depends(get_db)
):
    """
    Obtiene reportes laborales con filtros opcionales
    """
    # Construir diccionario de filtros
    filtros = {}
    if busqueda:
        filtros['busqueda'] = busqueda
    if maquina_id is not None:
        filtros['maquina_id'] = maquina_id
    if proyecto_id is not None:
        filtros['proyecto_id'] = proyecto_id
    if usuario_id is not None:
        filtros['usuario_id'] = usuario_id
    if fecha_desde:
        filtros['fecha_desde'] = fecha_desde
    if fecha_hasta:
        filtros['fecha_hasta'] = fecha_hasta
    
    # Debug (puedes quitarlo después)
    print(f"🔍 Filtros recibidos en backend: {filtros}")
    
    return service_get_reportes_laborales(session, filtros=filtros)

@router.get("/{id}", response_model=ReporteLaboralOut)
def get_reporte_laboral(id: int, session: Session = Depends(get_db)):
    reporte = service_get_reporte_laboral(session, id)
    if reporte:
        return reporte
    return JSONResponse(content={"error": "Reporte laboral no encontrado"}, status_code=404)

@router.post("/", response_model=ReporteLaboralOut, status_code=201)
def create_reporte_laboral(reporte_laboral: ReporteLaboralCreate, session: Session = Depends(get_db)):
    return service_create_reporte_laboral(session, reporte_laboral)

@router.put("/{id}", response_model=ReporteLaboralOut)
def update_reporte_laboral(id: int, reporte_laboral: ReporteLaboralSchema, session: Session = Depends(get_db)):
    updated = service_update_reporte_laboral(session, id, reporte_laboral)
    if updated:
        return updated
    return JSONResponse(content={"error": "Reporte laboral no encontrado"}, status_code=404)

@router.delete("/{id}")
def delete_reporte_laboral(id: int, session: Session = Depends(get_db)):
    deleted = service_delete_reporte_laboral(session, id)
    if deleted:
        return {"message": "Reporte laboral eliminado"}
    return JSONResponse(content={"error": "Reporte laboral no encontrado"}, status_code=404)