from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from app.db.dependencies import get_db
from app.schemas.schemas import ReporteLaboralSchema
from sqlalchemy.orm import Session
from app.services.reporte_laboral_service import (
    get_reportes_laborales as service_get_reportes_laborales,
    get_reporte_laboral as service_get_reporte_laboral,
    create_reporte_laboral as service_create_reporte_laboral,
    update_reporte_laboral as service_update_reporte_laboral,
    delete_reporte_laboral as service_delete_reporte_laboral,
)

router = APIRouter(prefix="/reportes-laborales", tags=["Reportes Laborales"])

# Endpoints Reportes Laborales
@router.get("/", response_model=List[ReporteLaboralSchema])
def get_reportes_laborales(session: Session = Depends(get_db)):
    return service_get_reportes_laborales(session)

@router.get("/{id}", response_model=ReporteLaboralSchema)
def get_reporte_laboral(id: int, session: Session = Depends(get_db)):
    reporte = service_get_reporte_laboral(session, id)
    if reporte:
        return reporte
    else:
        return JSONResponse(content={"error": "Reporte laboral no encontrado"}, status_code=404)

@router.post("/", response_model=ReporteLaboralSchema, status_code=201)
def create_reporte_laboral(reporte_laboral: ReporteLaboralSchema, session: Session = Depends(get_db)):
    return service_create_reporte_laboral(session, reporte_laboral)

@router.put("/{id}", response_model=ReporteLaboralSchema)
def update_reporte_laboral(id: int, reporte_laboral: ReporteLaboralSchema, session: Session = Depends(get_db)):
    updated = service_update_reporte_laboral(session, id, reporte_laboral)
    if updated:
        return updated
    else:
        return JSONResponse(content={"error": "Reporte laboral no encontrado"}, status_code=404)

@router.delete("/{id}")
def delete_reporte_laboral(id: int, session: Session = Depends(get_db)):
    deleted = service_delete_reporte_laboral(session, id)
    if deleted:
        return {"message": "Reporte laboral eliminado"}
    else:
        return JSONResponse(content={"error": "Reporte laboral no encontrado"}, status_code=404)