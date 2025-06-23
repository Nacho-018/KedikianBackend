from app.db.models import ReporteLaboral
from app.schemas.schemas import ReporteLaboralSchema, ReporteLaboralCreate, ReporteLaboralOut
from sqlalchemy.orm import Session
from typing import List, Optional

# Servicio para operaciones de Reporte Laboral

def get_reportes_laborales(db: Session) -> List[ReporteLaboralOut]:
    reportes = db.query(ReporteLaboral).all()
    return [ReporteLaboralOut(
        id=r.id,
        maquina_id=r.maquina_id,
        usuario_id=r.usuario_id,
        fecha_asignacion=r.fecha_asignacion,
        horas_turno=r.horas_turno
    ) for r in reportes]

def get_reporte_laboral(db: Session, reporte_id: int) -> Optional[ReporteLaboralOut]:
    r = db.query(ReporteLaboral).filter(ReporteLaboral.id == reporte_id).first()
    if r:
        return ReporteLaboralOut(
            id=r.id,
            maquina_id=r.maquina_id,
            usuario_id=r.usuario_id,
            fecha_asignacion=r.fecha_asignacion,
            horas_turno=r.horas_turno
        )
    return None

def create_reporte_laboral(db: Session, reporte: ReporteLaboralCreate) -> ReporteLaboralOut:
    nuevo_reporte = ReporteLaboral(**reporte.model_dump())
    db.add(nuevo_reporte)
    db.commit()
    db.refresh(nuevo_reporte)
    return ReporteLaboralOut(
        id=nuevo_reporte.id,
        maquina_id=nuevo_reporte.maquina_id,
        usuario_id=nuevo_reporte.usuario_id,
        fecha_asignacion=nuevo_reporte.fecha_asignacion,
        horas_turno=nuevo_reporte.horas_turno
    )

def update_reporte_laboral(db: Session, reporte_id: int, reporte: ReporteLaboralSchema) -> Optional[ReporteLaboralOut]:
    existing_reporte = db.query(ReporteLaboral).filter(ReporteLaboral.id == reporte_id).first()
    if existing_reporte:
        for field, value in reporte.model_dump().items():
            setattr(existing_reporte, field, value)
        db.commit()
        db.refresh(existing_reporte)
        return ReporteLaboralOut(
            id=existing_reporte.id,
            maquina_id=existing_reporte.maquina_id,
            usuario_id=existing_reporte.usuario_id,
            fecha_asignacion=existing_reporte.fecha_asignacion,
            horas_turno=existing_reporte.horas_turno
        )
    return None

def delete_reporte_laboral(db: Session, reporte_id: int) -> bool:
    reporte = db.query(ReporteLaboral).filter(ReporteLaboral.id == reporte_id).first()
    if reporte:
        db.delete(reporte)
        db.commit()
        return True
    return False
