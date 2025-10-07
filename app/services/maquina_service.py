# servicio_maquinas.py

from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from app.db.models import Maquina, ReporteLaboral
from app.schemas.schemas import (
    MaquinaSchema, MaquinaCreate, MaquinaOut,
    RegistroHorasMaquinaCreate, HistorialHorasOut
)

# ========== CRUD BÁSICO ==========

def get_maquinas(db: Session) -> List[MaquinaOut]:
    maquinas = db.query(Maquina).all()
    return [MaquinaOut.model_validate(m) for m in maquinas]

def get_maquina(db: Session, maquina_id: int) -> Optional[MaquinaOut]:
    maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()
    return MaquinaOut.model_validate(maquina) if maquina else None

def create_maquina(db: Session, maquina: MaquinaCreate) -> MaquinaOut:
    # Crear máquina con estado=True por defecto
    maquina_data = maquina.model_dump()
    maquina_data['estado'] = True  # Agregar estado por defecto
    
    nueva_maquina = Maquina(**maquina_data)
    db.add(nueva_maquina)
    db.commit()
    db.refresh(nueva_maquina)
    return MaquinaOut.model_validate(nueva_maquina)

def update_maquina(db: Session, maquina_id: int, maquina: MaquinaSchema) -> Optional[MaquinaOut]:
    existing = db.query(Maquina).filter(Maquina.id == maquina_id).first()
    if not existing:
        return None
    
    # Actualizar solo los campos que vienen en el request
    maquina_data = maquina.model_dump(exclude_unset=True)
    
    for field, value in maquina_data.items():
        setattr(existing, field, value)
    
    db.commit()
    db.refresh(existing)
    return MaquinaOut.model_validate(existing)

def delete_maquina(db: Session, maquina_id: int) -> bool:
    maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()
    if not maquina:
        return False
    db.delete(maquina)
    db.commit()
    return True

def get_all_maquinas_paginated(db: Session, skip: int = 0, limit: int = 15):
    """
    Obtener máquinas con paginación
    """
    maquinas = db.query(Maquina).offset(skip).limit(limit).all()
    total = db.query(Maquina).count()
    
    return {
        "items": [MaquinaOut.model_validate(m) for m in maquinas],
        "total": total,
        "skip": skip,
        "limit": limit
    }

# ========== HORAS DE USO ==========

def registrar_horas_maquina(
    db: Session,
    maquina_id: int,
    registro: RegistroHorasMaquinaCreate,
    usuario_id: int
) -> dict:
    """
    Registra horas trabajadas para una máquina y actualiza horas acumuladas
    """
    maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()
    if not maquina:
        raise Exception(f"Máquina con ID {maquina_id} no encontrada")

    # Convertir fecha si viene como string
    fecha = registro.fecha
    if isinstance(fecha, str):
        if 'T' not in fecha:
            fecha = f"{fecha}T00:00:00"
        fecha = datetime.fromisoformat(fecha)

    # Crear registro laboral
    reporte = ReporteLaboral(
        maquina_id=maquina_id,
        usuario_id=usuario_id,
        fecha_asignacion=fecha,
        horas_turno=registro.horas
    )
    db.add(reporte)

    # Acumular horas en la máquina
    if maquina.horas_uso is None:
        maquina.horas_uso = 0
    maquina.horas_uso += registro.horas

    db.commit()
    db.refresh(reporte)

    return {
        "mensaje": f"Se registraron {registro.horas} horas para la máquina {maquina.nombre}",
        "horas_totales": maquina.horas_uso,
        "fecha_registro": fecha
    }

def obtener_historial_horas_maquina(db: Session, maquina_id: int) -> List[HistorialHorasOut]:
    """
    Historial completo de horas de una máquina
    """
    maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()
    if not maquina:
        return []

    reportes = db.query(ReporteLaboral).filter(
        ReporteLaboral.maquina_id == maquina_id
    ).order_by(desc(ReporteLaboral.fecha_asignacion)).all()

    return [
        HistorialHorasOut(
            id=r.id,
            maquina_id=r.maquina_id,
            horas_trabajadas=r.horas_turno or 0,
            fecha=r.fecha_asignacion,
            usuario_id=r.usuario_id,
            created_at=r.created,
            updated_at=r.updated
        )
        for r in reportes
    ]

def obtener_estadisticas_horas_maquina(
    db: Session,
    maquina_id: int,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None
) -> dict:
    """
    Obtener estadísticas de horas de una máquina
    """
    from sqlalchemy import func
    
    query = db.query(
        func.sum(ReporteLaboral.horas_turno).label('total_horas'),
        func.count(ReporteLaboral.id).label('total_registros'),
        func.avg(ReporteLaboral.horas_turno).label('promedio_horas'),
        func.min(ReporteLaboral.fecha_asignacion).label('fecha_primer_registro'),
        func.max(ReporteLaboral.fecha_asignacion).label('fecha_ultimo_registro')
    ).filter(ReporteLaboral.maquina_id == maquina_id)
    
    if fecha_inicio:
        query = query.filter(ReporteLaboral.fecha_asignacion >= fecha_inicio)
    if fecha_fin:
        query = query.filter(ReporteLaboral.fecha_asignacion <= fecha_fin)
    
    resultado = query.first()
    
    return {
        "total_horas": float(resultado.total_horas or 0),
        "total_registros": int(resultado.total_registros or 0),
        "promedio_horas": float(resultado.promedio_horas or 0),
        "fecha_primer_registro": resultado.fecha_primer_registro,
        "fecha_ultimo_registro": resultado.fecha_ultimo_registro
    }