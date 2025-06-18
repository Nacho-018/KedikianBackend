from app.db.models import ReporteLaboral
from app.schemas.schemas import ReporteLaboralSchema
from sqlalchemy.orm import Session
from typing import List, Optional

# Servicio para operaciones de Reporte Laboral

def get_reportes_laborales(db: Session) -> List[ReporteLaboral]:
    return db.query(ReporteLaboral).all()

def get_reporte_laboral(db: Session, reporte_id: int) -> Optional[ReporteLaboral]:
    return db.query(ReporteLaboral).filter(ReporteLaboral.id == reporte_id).first()

def create_reporte_laboral(db: Session, reporte: ReporteLaboralSchema) -> ReporteLaboral:
    nuevo_reporte = ReporteLaboral(**reporte.model_dump())
    db.add(nuevo_reporte)
    db.commit()
    db.refresh(nuevo_reporte)
    return nuevo_reporte

def update_reporte_laboral(db: Session, reporte_id: int, reporte: ReporteLaboralSchema) -> Optional[ReporteLaboral]:
    existing_reporte = db.query(ReporteLaboral).filter(ReporteLaboral.id == reporte_id).first()
    if existing_reporte:
        for field, value in reporte.model_dump().items():
            setattr(existing_reporte, field, value)
        db.commit()
        db.refresh(existing_reporte)
        return existing_reporte
    return None

def delete_reporte_laboral(db: Session, reporte_id: int) -> bool:
    reporte = db.query(ReporteLaboral).filter(ReporteLaboral.id == reporte_id).first()
    if reporte:
        db.delete(reporte)
        db.commit()
        return True
    return False
