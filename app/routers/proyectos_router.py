from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Optional
from app.db.dependencies import get_db
from app.schemas.schemas import (
    ProyectoSchema,
    ProyectoCreate,
    ContratoArchivoResponse,
    ProyectoConDetallesResponse
)
from sqlalchemy.orm import Session
import shutil
import os
import time
from datetime import datetime, date
from app.services.proyecto_service import (
    get_proyectos as service_get_proyectos,
    get_proyecto as service_get_proyecto,
    delete_proyecto as service_delete_proyecto,
    get_maquinas_by_proyecto,
    get_aridos_by_proyecto,
    get_cantidad_proyectos_activos,
    get_all_proyectos_paginated
)
from app.services.proyecto_optimizado_service import (
    get_proyecto_con_detalles_optimizado,
    get_proyectos_con_detalles_optimizado
)
from app.security.auth import get_current_user
from app.db.models import ReporteLaboral, Proyecto, ContratoArchivo

router = APIRouter(prefix="/proyectos", tags=["Proyectos"], dependencies=[Depends(get_current_user)])

# Configuración de uploads
UPLOAD_DIR = "uploads/contratos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Endpoints Proyectos
@router.get("/", response_model=List[ProyectoSchema])
def get_proyectos(
    skip: int = 0,
    limit: int = 100,
    solo_activos: bool = False,
    session: Session = Depends(get_db)
):
    query = session.query(Proyecto)
    
    if solo_activos:
        query = query.filter(Proyecto.estado == True)
    
    proyectos = query.offset(skip).limit(limit).all()
    
    # Agregar URLs de contratos a cada proyecto
    for proyecto in proyectos:
        if proyecto.contrato_file_path and os.path.exists(proyecto.contrato_file_path):
            # Obtener el último contrato archivo
            ultimo_contrato = session.query(ContratoArchivo).filter(
                ContratoArchivo.proyecto_id == proyecto.id
            ).order_by(ContratoArchivo.fecha_subida.desc()).first()
            
            if ultimo_contrato:
                proyecto.contrato_url = f"/api/proyectos/{proyecto.id}/contrato"
                proyecto.contrato_nombre = ultimo_contrato.nombre_archivo
                proyecto.contrato_tipo = ultimo_contrato.tipo_archivo
    
    return proyectos

# ============= RUTAS ESPECÍFICAS (DEBEN IR ANTES DE /{id}) =============

@router.get("/con-detalles", response_model=List[ProyectoConDetallesResponse])
def get_proyectos_con_detalles(
    solo_activos: bool = True,
    session: Session = Depends(get_db)
):
    """
    Endpoint optimizado que retorna TODOS los proyectos con sus relaciones completas.

    Elimina el problema de N+1 queries usando eager loading.
    Retorna en UNA SOLA llamada:
    - Información del proyecto
    - Máquinas asociadas con horas totales
    - Áridos asociados con información de usuario
    - Reportes laborales con máquina y usuario completos
    - Archivos de contrato

    Args:
        solo_activos: Si True, solo retorna proyectos activos (default: True)

    Returns:
        Lista de proyectos con todas sus relaciones

    Ejemplo de uso:
        GET /api/v1/proyectos/con-detalles
        GET /api/v1/proyectos/con-detalles?solo_activos=false
    """
    try:
        return get_proyectos_con_detalles_optimizado(session, solo_activos)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener proyectos con detalles: {str(e)}"
        )

@router.get("/activos/cantidad")
def cantidad_proyectos_activos(session: Session = Depends(get_db)):
    cantidad = get_cantidad_proyectos_activos(session)
    return {"cantidad_activos": cantidad}

@router.get("/paginado")
def proyectos_paginado(skip: int = 0, limit: int = 15, session: Session = Depends(get_db)):
    return get_all_proyectos_paginated(session, skip=skip, limit=limit)

# ============= RUTAS CON PARÁMETROS (/{id} debe ir después) =============

@router.get("/{id}", response_model=ProyectoSchema)
def get_proyecto(id: int, session: Session = Depends(get_db)):
    proyecto = service_get_proyecto(session, id)
    if proyecto:
        # Agregar URL del contrato si existe
        if proyecto.contrato_file_path and os.path.exists(proyecto.contrato_file_path):
            ultimo_contrato = session.query(ContratoArchivo).filter(
                ContratoArchivo.proyecto_id == proyecto.id
            ).order_by(ContratoArchivo.fecha_subida.desc()).first()
            
            if ultimo_contrato:
                proyecto.contrato_url = f"/api/proyectos/{proyecto.id}/contrato"
                proyecto.contrato_nombre = ultimo_contrato.nombre_archivo
                proyecto.contrato_tipo = ultimo_contrato.tipo_archivo
        
        return proyecto
    else:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

@router.post("/", status_code=201)
async def create_proyecto(
    nombre: str = Form(...),
    fecha_inicio: str = Form(...),
    estado: bool = Form(...),
    gerente: str = Form(...),
    ubicacion: str = Form(...),
    descripcion: str = Form(...),
    fecha_creacion: str = Form(...),
    contrato: Optional[UploadFile] = File(None),
    session: Session = Depends(get_db)
):
    """
    Crear proyecto con archivo de contrato opcional
    """
    try:
        # Convertir fecha_inicio a date
        fecha_inicio_date = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        fecha_creacion_date = datetime.strptime(fecha_creacion, "%Y-%m-%d").date()
        
        # Crear proyecto
        nuevo_proyecto = Proyecto(
            nombre=nombre,
            fecha_inicio=fecha_inicio_date,
            estado=estado,
            gerente=gerente,
            ubicacion=ubicacion,
            descripcion=descripcion,
            fecha_creacion=fecha_creacion_date
        )
        
        session.add(nuevo_proyecto)
        session.flush()  # Para obtener el ID antes del commit
        
        # Si hay archivo de contrato, guardarlo
        if contrato:
            # Validar tipo de archivo
            allowed_types = [
                "application/pdf", 
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "image/jpeg",
                "image/png",
                "image/jpg"
            ]
            
            if contrato.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")
            
            # Crear directorio del proyecto
            proyecto_dir = os.path.join(UPLOAD_DIR, str(nuevo_proyecto.id))
            os.makedirs(proyecto_dir, exist_ok=True)
            
            # Generar nombre único
            file_extension = contrato.filename.split('.')[-1]
            unique_filename = f"contrato_{nuevo_proyecto.id}_{int(time.time())}.{file_extension}"
            file_path = os.path.join(proyecto_dir, unique_filename)
            
            # Guardar archivo físico
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(contrato.file, buffer)
            
            # Guardar registro en base de datos
            contrato_archivo = ContratoArchivo(
                proyecto_id=nuevo_proyecto.id,
                nombre_archivo=contrato.filename,
                ruta_archivo=file_path,
                tipo_archivo=contrato.content_type,
                tamaño_archivo=contrato.size or 0
            )
            
            session.add(contrato_archivo)
            nuevo_proyecto.contrato_file_path = file_path
        
        session.commit()
        session.refresh(nuevo_proyecto)
        
        # Agregar URLs del contrato para la respuesta
        if nuevo_proyecto.contrato_file_path:
            nuevo_proyecto.contrato_url = f"/api/proyectos/{nuevo_proyecto.id}/contrato"
            ultimo_contrato = session.query(ContratoArchivo).filter(
                ContratoArchivo.proyecto_id == nuevo_proyecto.id
            ).order_by(ContratoArchivo.fecha_subida.desc()).first()
            if ultimo_contrato:
                nuevo_proyecto.contrato_nombre = ultimo_contrato.nombre_archivo
                nuevo_proyecto.contrato_tipo = ultimo_contrato.tipo_archivo
        
        return nuevo_proyecto
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al crear proyecto: {str(e)}")

@router.put("/{id}")
async def update_proyecto(
    id: int,
    nombre: str = Form(...),
    fecha_inicio: str = Form(...),
    estado: bool = Form(...),
    gerente: str = Form(...),
    ubicacion: str = Form(...),
    descripcion: str = Form(...),
    contrato: Optional[UploadFile] = File(None),
    session: Session = Depends(get_db)
):
    """
    Actualizar proyecto con archivo de contrato opcional
    """
    try:
        # Buscar proyecto
        proyecto = session.query(Proyecto).filter(Proyecto.id == id).first()
        if not proyecto:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        # Actualizar campos
        proyecto.nombre = nombre
        proyecto.fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        proyecto.estado = estado
        proyecto.gerente = gerente
        proyecto.ubicacion = ubicacion
        proyecto.descripcion = descripcion
        
        # Si hay nuevo archivo de contrato
        if contrato:
            # Validar tipo de archivo
            allowed_types = [
                "application/pdf", 
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "image/jpeg",
                "image/png",
                "image/jpg"
            ]
            
            if contrato.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")
            
            # Crear directorio si no existe
            proyecto_dir = os.path.join(UPLOAD_DIR, str(proyecto.id))
            os.makedirs(proyecto_dir, exist_ok=True)
            
            # Generar nombre único
            file_extension = contrato.filename.split('.')[-1]
            unique_filename = f"contrato_{proyecto.id}_{int(time.time())}.{file_extension}"
            file_path = os.path.join(proyecto_dir, unique_filename)
            
            # Guardar nuevo archivo
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(contrato.file, buffer)
            
            # Guardar registro en base de datos
            contrato_archivo = ContratoArchivo(
                proyecto_id=proyecto.id,
                nombre_archivo=contrato.filename,
                ruta_archivo=file_path,
                tipo_archivo=contrato.content_type,
                tamaño_archivo=contrato.size or 0
            )
            
            session.add(contrato_archivo)
            proyecto.contrato_file_path = file_path
        
        session.commit()
        session.refresh(proyecto)
        
        # Agregar URLs del contrato para la respuesta
        if proyecto.contrato_file_path:
            proyecto.contrato_url = f"/api/proyectos/{proyecto.id}/contrato"
            ultimo_contrato = session.query(ContratoArchivo).filter(
                ContratoArchivo.proyecto_id == proyecto.id
            ).order_by(ContratoArchivo.fecha_subida.desc()).first()
            if ultimo_contrato:
                proyecto.contrato_nombre = ultimo_contrato.nombre_archivo
                proyecto.contrato_tipo = ultimo_contrato.tipo_archivo
        
        return proyecto
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar proyecto: {str(e)}")

@router.delete("/{id}")
def delete_proyecto(id: int, session: Session = Depends(get_db)):
    deleted = service_delete_proyecto(session, id)
    if deleted:
        return {"message": "Proyecto eliminado"}
    else:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

@router.get("/{id}/maquinas")
def get_maquinas_proyecto(id: int, session: Session = Depends(get_db)):
    try:
        return get_maquinas_by_proyecto(session, id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}/aridos")
def get_aridos_proyecto(id: int, session: Session = Depends(get_db)):
    try:
        return get_aridos_by_proyecto(session, id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}/reportes-laborales")
def get_reportes_laborales_proyecto(id: int, session: Session = Depends(get_db)):
    """
    Obtiene todos los reportes laborales de un proyecto específico
    """
    try:
        reportes = session.query(ReporteLaboral).filter(
            ReporteLaboral.proyecto_id == id
        ).all()
        
        return [
            {
                "id": r.id,
                "maquina_id": r.maquina_id,
                "usuario_id": r.usuario_id,
                "proyecto_id": r.proyecto_id,
                "fecha_asignacion": r.fecha_asignacion,
                "horas_turno": r.horas_turno,
                "horometro_inicial": r.horometro_inicial,
                "created": r.created,
                "updated": r.updated
            }
            for r in reportes
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============= ENDPOINTS OPTIMIZADOS CON EAGER LOADING =============

@router.get("/{id}/con-detalles", response_model=ProyectoConDetallesResponse)
def get_proyecto_con_detalles(
    id: int,
    session: Session = Depends(get_db)
):
    """
    Endpoint optimizado que retorna UN proyecto específico con todas sus relaciones.

    Elimina el problema de N+1 queries usando eager loading.
    Retorna en UNA SOLA llamada:
    - Información del proyecto
    - Máquinas asociadas con horas totales
    - Áridos asociados con información de usuario
    - Reportes laborales con máquina y usuario completos
    - Archivos de contrato

    Args:
        id: ID del proyecto a buscar

    Returns:
        Proyecto con todas sus relaciones

    Raises:
        HTTPException 404: Si el proyecto no existe

    Ejemplo de uso:
        GET /api/v1/proyectos/123/con-detalles
    """
    try:
        proyecto = get_proyecto_con_detalles_optimizado(session, id)

        if not proyecto:
            raise HTTPException(
                status_code=404,
                detail=f"Proyecto con ID {id} no encontrado"
            )

        return proyecto
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener proyecto con detalles: {str(e)}"
        )

# Endpoint para descargar contrato
@router.get("/{proyecto_id}/contrato")
async def descargar_contrato(proyecto_id: int, db: Session = Depends(get_db)):
    """
    Descargar el archivo de contrato de un proyecto
    """
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if not proyecto.contrato_file_path or not os.path.exists(proyecto.contrato_file_path):
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    
    # Obtener información del archivo desde la BD
    contrato_archivo = db.query(ContratoArchivo).filter(
        ContratoArchivo.proyecto_id == proyecto_id
    ).order_by(ContratoArchivo.fecha_subida.desc()).first()
    
    filename = contrato_archivo.nombre_archivo if contrato_archivo else f"contrato_{proyecto_id}.pdf"
    media_type = contrato_archivo.tipo_archivo if contrato_archivo else "application/pdf"
    
    return FileResponse(
        proyecto.contrato_file_path,
        media_type=media_type,
        filename=filename
    )