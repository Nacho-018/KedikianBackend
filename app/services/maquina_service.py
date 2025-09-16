# Servicio para operaciones de Maquina

from app.db.models import Maquina, Proyecto, ReporteLaboral
from app.schemas.schemas import (
    MaquinaSchema, MaquinaCreate, MaquinaOut,
    RegistroHorasMaquinaCreate, HistorialProyectoOut,
    CambiarProyectoRequest, CambiarProyectoResponse
)
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, text
from typing import List, Optional
from datetime import datetime
from sqlalchemy.schema import CreateTable

def get_maquinas(db: Session) -> List[MaquinaOut]:
    maquinas = db.query(Maquina).all()
    return [MaquinaOut(
        id=m.id,
        nombre=m.nombre,
        estado=m.estado,
        horas_uso=m.horas_uso,
        proyecto_id=m.proyecto_id
    ) for m in maquinas]

def get_maquina(db: Session, maquina_id: int) -> Optional[MaquinaOut]:
    m = db.query(Maquina).filter(Maquina.id == maquina_id).first()
    if m:
        return MaquinaOut(
            id=m.id,
            nombre=m.nombre,
            estado=m.estado,
            horas_uso=m.horas_uso, 
            proyecto_id=m.proyecto_id
        )
    return None

def create_maquina(db: Session, maquina: MaquinaCreate) -> MaquinaOut:
    nueva_maquina = Maquina(**maquina.model_dump())
    db.add(nueva_maquina)
    db.commit()
    db.refresh(nueva_maquina)
    return MaquinaOut(
        id=nueva_maquina.id,
        nombre=nueva_maquina.nombre,
        estado=nueva_maquina.estado,
        horas_uso=nueva_maquina.horas_uso,
        proyecto_id=nueva_maquina.proyecto_id
    )

def update_maquina(db: Session, maquina_id: int, maquina: MaquinaSchema) -> Optional[MaquinaOut]:
    existing_maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()
    if existing_maquina:
        for field, value in maquina.model_dump().items():
            setattr(existing_maquina, field, value)
        db.commit()
        db.refresh(existing_maquina)
        return MaquinaOut(
            id=existing_maquina.id,
            nombre=existing_maquina.nombre,
            estado=existing_maquina.estado,
            horas_uso=existing_maquina.horas_uso,
            proyecto_id=existing_maquina.proyecto_id
        )
    return None

def delete_maquina(db: Session, maquina_id: int) -> bool:
    maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()
    if maquina:
        db.delete(maquina)
        db.commit()
        return True
    return False

def get_all_maquinas_paginated(db: Session, skip: int = 0, limit: int = 15) -> List[MaquinaOut]:
    maquinas = db.query(Maquina).offset(skip).limit(limit).all()
    return [MaquinaOut.model_validate(m) for m in maquinas]

from datetime import datetime

def registrar_horas_maquina_proyecto(
    db: Session, 
    maquina_id: int, 
    proyecto_id: int, 
    registro: RegistroHorasMaquinaCreate,
    usuario_id: int
) -> Optional[dict]:
    """
    Registra horas de uso de una máquina en un proyecto específico
    """
    try:
        # Buscar la máquina
        maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()
        if not maquina:
            raise Exception(f"Máquina con ID {maquina_id} no encontrada")
        
        # Buscar el proyecto
        proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
        if not proyecto:
            raise Exception(f"Proyecto con ID {proyecto_id} no encontrado")
        
        # Convertir fecha si viene como string
        fecha_asignacion = registro.fecha
        if isinstance(fecha_asignacion, str):
            try:
                # Si la fecha viene sin hora, agregar 00:00:00
                if 'T' not in fecha_asignacion:
                    fecha_asignacion = f"{fecha_asignacion}T00:00:00"
                fecha_asignacion = datetime.fromisoformat(fecha_asignacion)
            except Exception as e:
                print(f"Error al procesar la fecha: {str(e)}")
                fecha_asignacion = datetime.now()

        # Crear reporte laboral con solo los campos que sabemos que existen
        reporte_data = {
            'maquina_id': maquina_id,
            'usuario_id': usuario_id,
            'fecha_asignacion': fecha_asignacion,
            'horas_turno': registro.horas
        }
        
        try:
            # Crear el reporte
            reporte = ReporteLaboral(**reporte_data)
            
            try:
                # Intentar asignar proyecto_id
                reporte.proyecto_id = proyecto_id
            except Exception as e:
                print(f"No se pudo asignar proyecto_id: {str(e)}")
            
            # Agregar y guardar el reporte
            db.add(reporte)
            
            # Actualizar horas de uso de la máquina
            if maquina.horas_uso is None:
                maquina.horas_uso = 0
            maquina.horas_uso += registro.horas

            # Commit de los cambios
            db.commit()
            db.refresh(reporte)
            
            return {
                "mensaje": f"Se registraron {registro.horas} horas para la máquina {maquina.nombre} en el proyecto {proyecto.nombre}",
                "horas_totales": maquina.horas_uso,
                "fecha_registro": fecha_asignacion
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error creando el reporte: {str(e)}")
            raise Exception(f"Error al crear el reporte: {str(e)}")
            
    except Exception as e:
        print(f"Error en el proceso: {str(e)}")
        raise Exception(str(e))

def obtener_historial_proyectos_maquina(db: Session, maquina_id: int) -> List[HistorialProyectoOut]:
    """
    Obtiene el historial de proyectos de una máquina
    """
    # Verificar que la máquina existe
    maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()
    if not maquina:
        return []
    
    # Obtener reportes laborales de la máquina
    reportes = db.query(ReporteLaboral).filter(
        ReporteLaboral.maquina_id == maquina_id
    ).order_by(desc(ReporteLaboral.fecha_asignacion)).all()
    
    # Agrupar por proyecto y calcular totales
    proyectos_historial = {}
    
    for reporte in reportes:
        # Obtener el proyecto actual de la máquina
        proyecto_actual = db.query(Proyecto).filter(Proyecto.id == maquina.proyecto_id).first()
        
        if proyecto_actual:
            proyecto_id = proyecto_actual.id
            if proyecto_id not in proyectos_historial:
                proyectos_historial[proyecto_id] = {
                    "proyecto_id": proyecto_id,
                    "proyecto_nombre": proyecto_actual.nombre,
                    "fecha_asignacion": reporte.fecha_asignacion,
                    "fecha_retiro": None,
                    "total_horas": 0,
                    "estado": "activo" if maquina.proyecto_id == proyecto_id else "finalizado"
                }
            
            # Sumar horas (asumiendo que cada reporte representa 1 hora)
            proyectos_historial[proyecto_id]["total_horas"] += 1
    
    return [HistorialProyectoOut(**proyecto) for proyecto in proyectos_historial.values()]

def cambiar_proyecto_maquina(
    db: Session, 
    maquina_id: int, 
    cambio: CambiarProyectoRequest
) -> Optional[CambiarProyectoResponse]:
    """
    Cambia el proyecto asignado a una máquina
    """
    # Verificar que la máquina existe
    maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()
    if not maquina:
        return None
    
    # Verificar que el nuevo proyecto existe
    nuevo_proyecto = db.query(Proyecto).filter(Proyecto.id == cambio.nuevo_proyecto_id).first()
    if not nuevo_proyecto:
        return None
    
    # Guardar el proyecto anterior
    proyecto_anterior_id = maquina.proyecto_id
    
    # Actualizar la máquina con el nuevo proyecto
    maquina.proyecto_id = cambio.nuevo_proyecto_id
    
    db.commit()
    db.refresh(maquina)
    
    return CambiarProyectoResponse(
        maquina_id=maquina_id,
        proyecto_anterior_id=proyecto_anterior_id,
        proyecto_nuevo_id=cambio.nuevo_proyecto_id,
        fecha_cambio=cambio.fecha_cambio,
        mensaje=f"Máquina {maquina.nombre} reasignada del proyecto {proyecto_anterior_id} al proyecto {nuevo_proyecto.nombre}"
    )
    
def obtener_historial_horas_maquina(db: Session, maquina_id: int) -> List[HistorialHorasOut]:
    """
    Obtiene el historial individual de horas trabajadas de una máquina
    """
    # Verificar que la máquina existe
    maquina = db.query(Maquina).filter(Maquina.id == maquina_id).first()
    if not maquina:
        return []
    
    # Obtener todos los reportes laborales de la máquina que tienen proyecto asignado
    reportes = db.query(ReporteLaboral).filter(
        and_(
            ReporteLaboral.maquina_id == maquina_id,
            ReporteLaboral.proyecto_id.is_not(None)  # Solo registros con proyecto
        )
    ).order_by(desc(ReporteLaboral.fecha_asignacion)).all()
    
    historial = []
    
    for reporte in reportes:
        historial_item = HistorialHorasOut(
            id=reporte.id,
            maquina_id=reporte.maquina_id,
            proyecto_id=reporte.proyecto_id,
            horas_trabajadas=reporte.horas_turno or 0,
            fecha=reporte.fecha_asignacion,
            usuario_id=reporte.usuario_id,
            created_at=reporte.created,
            updated_at=reporte.updated
        )
        historial.append(historial_item)
    
    return historial