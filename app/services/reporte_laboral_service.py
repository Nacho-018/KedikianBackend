from app.db.models import ReporteLaboral, Maquina, HorometroHistorial
from app.schemas.schemas import ReporteLaboralSchema, ReporteLaboralCreate, ReporteLaboralOut
from sqlalchemy.orm import Session
from sqlalchemy import extract, func, and_
from typing import List, Optional, Dict
from datetime import datetime

# Servicio para operaciones de Reporte Laboral

def get_reportes_laborales(db: Session, filtros: Optional[Dict] = None) -> List[ReporteLaboralOut]:
    """
    Obtiene reportes laborales con filtros opcionales
    """
    query = db.query(ReporteLaboral)
    
    # Aplicar filtros si existen
    if filtros:
        conditions = []
        
        # Filtro por búsqueda en nombre de máquina
        if filtros.get('busqueda'):
            busqueda = f"%{filtros['busqueda']}%"
            query = query.join(Maquina, ReporteLaboral.maquina_id == Maquina.id)
            conditions.append(Maquina.nombre.ilike(busqueda))
        
        # Filtro por máquina
        if filtros.get('maquina_id'):
            conditions.append(ReporteLaboral.maquina_id == int(filtros['maquina_id']))
        
        # Filtro por proyecto
        if filtros.get('proyecto_id'):
            conditions.append(ReporteLaboral.proyecto_id == int(filtros['proyecto_id']))
        
        # Filtro por usuario
        if filtros.get('usuario_id'):
            conditions.append(ReporteLaboral.usuario_id == int(filtros['usuario_id']))
        
        # Filtro por fecha desde
        if filtros.get('fecha_desde'):
            try:
                fecha_desde = datetime.strptime(filtros['fecha_desde'], '%Y-%m-%d').date()
                conditions.append(ReporteLaboral.fecha_asignacion >= fecha_desde)
            except ValueError:
                pass
        
        # Filtro por fecha hasta
        if filtros.get('fecha_hasta'):
            try:
                fecha_hasta = datetime.strptime(filtros['fecha_hasta'], '%Y-%m-%d').date()
                conditions.append(ReporteLaboral.fecha_asignacion <= fecha_hasta)
            except ValueError:
                pass
        
        # Aplicar todas las condiciones
        if conditions:
            query = query.filter(and_(*conditions))
    
    # Ordenar por fecha descendente
    reportes = query.order_by(ReporteLaboral.fecha_asignacion.desc()).all()
    
    print(f"✅ Backend - Reportes encontrados: {len(reportes)}")  # Debug
    
    return [ReporteLaboralOut(
        id=r.id,
        maquina_id=r.maquina_id,
        usuario_id=r.usuario_id,
        proyecto_id=r.proyecto_id,
        fecha_asignacion=r.fecha_asignacion,
        horas_turno=r.horas_turno,
        horometro_inicial=r.horometro_inicial
    ) for r in reportes]


def get_reporte_laboral(db: Session, reporte_id: int) -> Optional[ReporteLaboralOut]:
    r = db.query(ReporteLaboral).filter(ReporteLaboral.id == reporte_id).first()
    if r:
        return ReporteLaboralOut(
            id=r.id,
            maquina_id=r.maquina_id,
            usuario_id=r.usuario_id,
            proyecto_id=r.proyecto_id,
            fecha_asignacion=r.fecha_asignacion,
            horas_turno=r.horas_turno,
            horometro_inicial=r.horometro_inicial
        )
    return None


def create_reporte_laboral(db: Session, reporte: ReporteLaboralCreate) -> ReporteLaboralOut:
    payload = reporte.model_dump()
    # Si no viene tarifa_hora, buscar en catálogo por proyecto
    if payload.get("tarifa_hora") is None and payload.get("proyecto_id") and payload.get("maquina_id"):
        from app.services.cuenta_corriente_service import get_tarifa_maquina_proyecto
        tarifa_catalogo = get_tarifa_maquina_proyecto(
            db, payload["proyecto_id"], payload["maquina_id"]
        )
        if tarifa_catalogo is not None:
            payload["tarifa_hora"] = tarifa_catalogo
    nuevo_reporte = ReporteLaboral(**payload)
    db.add(nuevo_reporte)
    db.flush()  # Obtener el ID del reporte antes de commit

    print(f"🔍 DEBUG - Reporte creado:")
    print(f"   - maquina_id: {nuevo_reporte.maquina_id}")
    print(f"   - horometro_inicial del reporte: {nuevo_reporte.horometro_inicial}")

    # Si el reporte tiene un horometro_inicial, actualizar el de la máquina
    if nuevo_reporte.horometro_inicial is not None and nuevo_reporte.maquina_id:
        maquina = db.query(Maquina).filter(Maquina.id == nuevo_reporte.maquina_id).first()

        if maquina:
            valor_anterior = maquina.horometro_inicial
            valor_nuevo = nuevo_reporte.horometro_inicial

            print(f"🔍 DEBUG - Actualizando máquina ID {maquina.id}:")
            print(f"   - Valor anterior: {valor_anterior}")
            print(f"   - Valor nuevo: {valor_nuevo}")

            # Solo actualizar si el valor cambió
            if valor_anterior != valor_nuevo:
                # Actualizar el horometro_inicial de la máquina
                maquina.horometro_inicial = valor_nuevo
                print(f"✅ Horómetro actualizado de {valor_anterior} a {valor_nuevo}")

                # Registrar el cambio en el historial
                historial = HorometroHistorial(
                    maquina_id=maquina.id,
                    valor_anterior=valor_anterior,
                    valor_nuevo=valor_nuevo,
                    usuario_id=nuevo_reporte.usuario_id,
                    motivo="reporte_laboral",
                    reporte_laboral_id=nuevo_reporte.id
                )
                db.add(historial)
            else:
                print(f"⚠️  No se actualizó - valores iguales")
    else:
        print(f"⚠️  No se actualizó el horómetro - horometro_inicial es None o no hay maquina_id")

    db.commit()
    db.refresh(nuevo_reporte)

    return ReporteLaboralOut(
        id=nuevo_reporte.id,
        maquina_id=nuevo_reporte.maquina_id,
        usuario_id=nuevo_reporte.usuario_id,
        proyecto_id=nuevo_reporte.proyecto_id,
        fecha_asignacion=nuevo_reporte.fecha_asignacion,
        horas_turno=nuevo_reporte.horas_turno,
        horometro_inicial=nuevo_reporte.horometro_inicial
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
            proyecto_id=existing_reporte.proyecto_id,
            fecha_asignacion=existing_reporte.fecha_asignacion,
            horas_turno=existing_reporte.horas_turno,
            horometro_inicial=existing_reporte.horometro_inicial
        )
    return None


def delete_reporte_laboral(db: Session, reporte_id: int) -> bool:
    reporte = db.query(ReporteLaboral).filter(ReporteLaboral.id == reporte_id).first()
    if reporte:
        db.delete(reporte)
        db.commit()
        return True
    return False


def get_total_horas_mes_actual(db: Session) -> float:
    """Devuelve la cantidad total de horas registradas durante el mes actual"""
    now = datetime.now()
    total_horas = db.query(func.sum(ReporteLaboral.horas_turno)).filter(
        extract('year', ReporteLaboral.fecha_asignacion) == now.year,
        extract('month', ReporteLaboral.fecha_asignacion) == now.month
    ).scalar()
    return float(total_horas) if total_horas else 0.0


def get_all_reportes_laborales_paginated(db: Session, skip: int = 0, limit: int = 15) -> List[ReporteLaboralOut]:
    reportes = db.query(ReporteLaboral).offset(skip).limit(limit).all()
    return [ReporteLaboralOut(
        id=r.id,
        maquina_id=r.maquina_id,
        usuario_id=r.usuario_id,
        proyecto_id=r.proyecto_id,
        fecha_asignacion=r.fecha_asignacion,
        horas_turno=r.horas_turno,
        horometro_inicial=r.horometro_inicial
    ) for r in reportes]