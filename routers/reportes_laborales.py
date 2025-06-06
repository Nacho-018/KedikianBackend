from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import List
from main import get_db
from models import ReporteLaboral
from app.schemas.schemas import ReporteLaboralSchema

router = APIRouter()

# Endpoints Reportes Laborales
@router.get("/reportes-laborales", tags=["Reportes Laborales"], response_model=List[ReporteLaboralSchema])
def get_reportes_laborales(session = Depends(get_db)):
    reportes = session.query(ReporteLaboral).all()
    return reportes

@router.get("/reportes-laborales/{id}", tags=["Reportes Laborales"], response_model=ReporteLaboralSchema)
def get_reporte_laboral(id: int, session = Depends(get_db)):
    reporte = session.query(ReporteLaboral).filter(ReporteLaboral.id == id).first()
    if reporte:
        return reporte
    else:
        return JSONResponse(content={"error": "Reporte laboral no encontrado"}, status_code=404)

@router.post("/reportes-laborales", tags=["Reportes Laborales"], response_model=ReporteLaboralSchema, status_code=201)
def create_reporte_laboral(reporte_laboral: ReporteLaboralSchema, session = Depends(get_db)):
    nuevo_reporte = ReporteLaboral(**reporte_laboral.model_dump())
    session.add(nuevo_reporte)
    session.commit()
    session.refresh(nuevo_reporte)
    return nuevo_reporte

@router.put("/reportes-laborales/{id}", tags=["Reportes Laborales"], response_model=ReporteLaboralSchema)
def update_reporte_laboral(id: int, reporte_laboral: ReporteLaboralSchema, session = Depends(get_db)):
    existing_reporte = session.query(ReporteLaboral).filter(ReporteLaboral.id == id).first()
    if existing_reporte:
        for field, value in reporte_laboral.model_dump().items():
            setattr(existing_reporte, field, value)
        session.commit()
        session.refresh(existing_reporte)
        return existing_reporte
    else:
        return JSONResponse(content={"error": "Reporte laboral no encontrado"}, status_code=404)

@router.delete("/reportes-laborales/{id}", tags=["Reportes Laborales"])
def delete_reporte_laboral(id: int, session = Depends(get_db)):
    reporte = session.query(ReporteLaboral).filter(ReporteLaboral.id == id).first()
    if reporte:
        session.delete(reporte)
        session.commit()
        return {"message": "Reporte laboral eliminado"}
    else:
        return JSONResponse(content={"error": "Reporte laboral no encontrado"}, status_code=404)