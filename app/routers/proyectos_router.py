from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from typing import List
from app.db.dependencies import get_db
from app.schemas.schemas import ProyectoSchema, ProyectoCreate, ContratoArchivoResponse
from sqlalchemy.orm import Session
import shutil
import os
import time
from app.services.proyecto_service import (
    get_proyectos as service_get_proyectos,
    get_proyecto as service_get_proyecto,
    create_proyecto as service_create_proyecto,
    update_proyecto as service_update_proyecto,
    delete_proyecto as service_delete_proyecto,
    get_maquinas_by_proyecto,
    get_aridos_by_proyecto,
    get_cantidad_proyectos_activos,
    get_all_proyectos_paginated
)
from app.security.auth import get_current_user
from app.db.models import ReporteLaboral, Proyecto, ContratoArchivo  # 👈 AGREGAR ESTE IMPORT

router = APIRouter(prefix="/proyectos", tags=["Proyectos"], dependencies=[Depends(get_current_user)])

# Endpoints Proyectos
@router.get("/", response_model=List[ProyectoSchema])
def get_proyectos(
    skip: int = 0,
    limit: int = 100,
    solo_activos: bool = False,  # Nuevo parámetro
    session: Session = Depends(get_db)
):
    query = session.query(Proyecto)
    
    # Filtrar solo proyectos activos si se solicita
    if solo_activos:
        query = query.filter(Proyecto.estado == True)
    
    proyectos = query.offset(skip).limit(limit).all()
    return proyectos

@router.get("/{id}", response_model=ProyectoSchema)
def get_proyecto(id: int, session: Session = Depends(get_db)):
    proyecto = service_get_proyecto(session, id)
    if proyecto:
        return proyecto
    else:
        return JSONResponse(content={"error": "Proyecto no encontrado"}, status_code=404)

@router.post("/", response_model=ProyectoSchema, status_code=201)
def create_proyecto(proyecto: ProyectoCreate, session: Session = Depends(get_db)):
    return service_create_proyecto(session, proyecto)

@router.put("/{id}", response_model=ProyectoSchema)
def update_proyecto(id: int, proyecto: ProyectoSchema, session: Session = Depends(get_db)):
    try:
        updated = service_update_proyecto(session, id, proyecto)
        if updated:
            return updated
        else:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar proyecto: {str(e)}")

@router.delete("/{id}")
def delete_proyecto(id: int, session: Session = Depends(get_db)):
    deleted = service_delete_proyecto(session, id)
    if deleted:
        return {"message": "Proyecto eliminado"}
    else:
        return JSONResponse(content={"error": "Proyecto no encontrado"}, status_code=404)

@router.get("/{id}/maquinas")
def get_maquinas_proyecto(id: int, session: Session = Depends(get_db)):
    from app.services.proyecto_service import get_maquinas_by_proyecto
    try:
        return get_maquinas_by_proyecto(session, id)
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

@router.get("/{id}/aridos")
def get_aridos_proyecto(id: int, session: Session = Depends(get_db)):
    from app.services.proyecto_service import get_aridos_by_proyecto
    try:
        return get_aridos_by_proyecto(session, id)
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

# 👇 AGREGAR ESTE NUEVO ENDPOINT
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
        return JSONResponse(status_code=500, content={"detail": str(e)})

# Endpoint para cantidad de proyectos activos
@router.get("/activos/cantidad")
def cantidad_proyectos_activos(session: Session = Depends(get_db)):
    cantidad = get_cantidad_proyectos_activos(session)
    return {"cantidad_activos": cantidad}

@router.get("/paginado")
def proyectos_paginado(skip: int = 0, limit: int = 15, session: Session = Depends(get_db)):
    return get_all_proyectos_paginated(session, skip=skip, limit=limit)

# Endpoints para manejo de contratos
@router.post("/{proyecto_id}/contrato")
async def subir_contrato(
    proyecto_id: int,
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validar que el proyecto existe
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    # Validar tipo de archivo
    allowed_types = ["application/pdf", "application/msword", 
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if archivo.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")
    
    # Crear directorio si no existe
    upload_dir = f"uploads/contratos/{proyecto_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generar nombre único para el archivo
    file_extension = archivo.filename.split('.')[-1]
    unique_filename = f"contrato_{proyecto_id}_{int(time.time())}.{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Guardar archivo
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)
    
    # Guardar información en base de datos
    contrato_archivo = ContratoArchivo(
        proyecto_id=proyecto_id,
        nombre_archivo=archivo.filename,
        ruta_archivo=file_path,
        tipo_archivo=archivo.content_type,
        tamaño_archivo=archivo.size
    )
    
    db.add(contrato_archivo)
    db.commit()
    
    # Actualizar proyecto con ruta del archivo
    proyecto.contrato_file_path = file_path
    db.commit()
    
    return {"message": "Contrato subido exitosamente", "archivo_id": contrato_archivo.id}

@router.get("/{proyecto_id}/contrato")
async def descargar_contrato(proyecto_id: int, db: Session = Depends(get_db)):
    proyecto = db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()
    if not proyecto or not proyecto.contrato_file_path:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    
    if not os.path.exists(proyecto.contrato_file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return FileResponse(
        proyecto.contrato_file_path,
        media_type='application/octet-stream',
        filename=f"contrato_{proyecto_id}.pdf"
    )