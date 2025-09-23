# app/routers/jornada_laboral_router.py - VERSIÓN CORREGIDA FINAL

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
from app.db.dependencies import get_db
from app.schemas.schemas import (
    JornadaLaboralCreate,
    JornadaLaboralResponse,
    JornadaLaboralUpdate,
    EstadisticasJornadaResponse
)
from app.services.jornada_laboral_service import JornadaLaboralService
from app.security.auth import get_current_user

# ✅ SCHEMAS PARA REQUEST BODY
class FicharEntradaRequest(BaseModel):
    usuario_id: int
    notas_inicio: Optional[str] = None
    ubicacion: Optional[dict] = None

class FinalizarJornadaRequest(BaseModel):
    tiempo_descanso: int = 60
    notas_fin: Optional[str] = None
    ubicacion: Optional[dict] = None
    forzado: bool = False

class ConfirmarOvertimeRequest(BaseModel):
    notas_overtime: Optional[str] = None

class RechazarOvertimeRequest(BaseModel):
    tiempo_descanso: int = 60
    notas_fin: Optional[str] = None

router = APIRouter(
    prefix="/jornadas-laborales", 
    tags=["Jornadas Laborales"], 
    dependencies=[Depends(get_current_user)]
)

# ============ ENDPOINTS DE FICHAJE ============

@router.post("/fichar-entrada", response_model=JornadaLaboralResponse)
async def fichar_entrada(
    request: FicharEntradaRequest,  # ✅ CORREGIDO: Usar schema apropiado
    db: Session = Depends(get_db)
):
    """
    Fichar entrada - Iniciar jornada laboral
    """
    try:
        jornada = JornadaLaboralService.iniciar_jornada(
            db=db,
            usuario_id=request.usuario_id,
            notas_inicio=request.notas_inicio,
            ubicacion=request.ubicacion
        )
        return JornadaLaboralResponse.from_orm(jornada)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al fichar entrada: {str(e)}")

@router.put("/finalizar/{jornada_id}", response_model=JornadaLaboralResponse)
async def finalizar_jornada(
    jornada_id: int,
    request: FinalizarJornadaRequest,  # ✅ CORREGIDO: Usar schema apropiado
    db: Session = Depends(get_db)
):
    """
    Finalizar jornada laboral
    """
    try:
        jornada = JornadaLaboralService.finalizar_jornada(
            db=db,
            jornada_id=jornada_id,
            tiempo_descanso=request.tiempo_descanso,
            notas_fin=request.notas_fin,
            ubicacion=request.ubicacion,
            forzado=request.forzado
        )
        return JornadaLaboralResponse.from_orm(jornada)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al finalizar jornada: {str(e)}")

@router.put("/confirmar-overtime/{jornada_id}", response_model=JornadaLaboralResponse)
async def confirmar_horas_extras(
    jornada_id: int,
    request: ConfirmarOvertimeRequest,  # ✅ CORREGIDO: Usar schema apropiado
    db: Session = Depends(get_db)
):
    """
    Confirmar horas extras y reanudar jornada
    """
    try:
        jornada = JornadaLaboralService.confirmar_horas_extras(
            db=db,
            jornada_id=jornada_id,
            notas_overtime=request.notas_overtime
        )
        return JornadaLaboralResponse.from_orm(jornada)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al confirmar horas extras: {str(e)}")

@router.put("/rechazar-overtime/{jornada_id}", response_model=JornadaLaboralResponse)
async def rechazar_horas_extras(
    jornada_id: int,
    request: RechazarOvertimeRequest,  # ✅ CORREGIDO: Usar schema apropiado
    db: Session = Depends(get_db)
):
    """
    Rechazar horas extras y finalizar jornada
    """
    try:
        jornada = JornadaLaboralService.rechazar_horas_extras(
            db=db,
            jornada_id=jornada_id,
            tiempo_descanso=request.tiempo_descanso,
            notas_fin=request.notas_fin
        )
        return JornadaLaboralResponse.from_orm(jornada)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al rechazar horas extras: {str(e)}")

# ============ ENDPOINTS DE CONSULTA ============

@router.get("/activa/{usuario_id}", response_model=Optional[JornadaLaboralResponse])
async def obtener_jornada_activa(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtener jornada activa de un usuario
    """
    try:
        jornada = JornadaLaboralService.obtener_jornada_activa(db, usuario_id)
        return JornadaLaboralResponse.from_orm(jornada) if jornada else None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener jornada activa: {str(e)}")

@router.get("/usuario/{usuario_id}", response_model=List[JornadaLaboralResponse])
async def obtener_jornadas_usuario(
    usuario_id: int,
    limite: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Obtener jornadas de un usuario
    """
    try:
        jornadas = JornadaLaboralService.obtener_jornadas_usuario(
            db=db,
            usuario_id=usuario_id,
            limite=limite,
            offset=offset
        )
        return [JornadaLaboralResponse.from_orm(j) for j in jornadas]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener jornadas: {str(e)}")

@router.get("/periodo", response_model=List[JornadaLaboralResponse])
async def obtener_jornadas_periodo(
    usuario_id: Optional[int] = None,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    limite: int = 50,
    db: Session = Depends(get_db)
):
    """
    Obtener jornadas por periodo
    """
    try:
        jornadas = JornadaLaboralService.obtener_jornadas_periodo(
            db=db,
            usuario_id=usuario_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            limite=limite
        )
        return [JornadaLaboralResponse.from_orm(j) for j in jornadas]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener jornadas por periodo: {str(e)}")

@router.get("/estadisticas/{usuario_id}/{mes}/{anio}", response_model=EstadisticasJornadaResponse)
async def obtener_estadisticas_mes(
    usuario_id: int,
    mes: int,
    anio: int,
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas del mes para un usuario
    """
    try:
        estadisticas = JornadaLaboralService.obtener_estadisticas_mes(
            db=db,
            usuario_id=usuario_id,
            mes=mes,
            año=anio
        )
        return EstadisticasJornadaResponse(**estadisticas)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")

# ============ ENDPOINTS DE CONTROL ============

@router.put("/actualizar-estado/{jornada_id}", response_model=JornadaLaboralResponse)
async def actualizar_estado_jornada(
    jornada_id: int,
    db: Session = Depends(get_db)
):
    """
    Actualizar estado de una jornada basado en el tiempo transcurrido
    """
    try:
        jornada = JornadaLaboralService.actualizar_estado_jornada(db, jornada_id)
        return JornadaLaboralResponse.from_orm(jornada)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar estado: {str(e)}")

@router.get("/verificar-activas", response_model=List[JornadaLaboralResponse])
async def verificar_jornadas_activas(db: Session = Depends(get_db)):
    """
    Verificar y actualizar todas las jornadas activas (para ejecución periódica)
    """
    try:
        jornadas = JornadaLaboralService.verificar_y_actualizar_jornadas_activas(db)
        return [JornadaLaboralResponse.from_orm(j) for j in jornadas]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al verificar jornadas activas: {str(e)}")

@router.get("/resumen-dia/{usuario_id}/{fecha}")
async def obtener_resumen_dia(
    usuario_id: int,
    fecha: date,
    db: Session = Depends(get_db)
):
    """
    Obtener resumen de jornadas para un día específico
    """
    try:
        resumen = JornadaLaboralService.obtener_resumen_dia(db, usuario_id, fecha)
        return resumen
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener resumen del día: {str(e)}")

# ============ ENDPOINT DE DEBUG ============

@router.get("/test")
async def test_endpoint():
    """
    Endpoint de prueba para verificar que el router funciona
    """
    return {"message": "Router de jornadas laborales funcionando correctamente", "status": "OK"}

@router.get("/tiempo-restante/{jornada_id}")
async def calcular_tiempo_restante(
    jornada_id: int,
    db: Session = Depends(get_db)
):
    """
    Calcular tiempo restante para diferentes límites
    """
    try:
        jornada = JornadaLaboralService.obtener_jornada_por_id(db, jornada_id)
        if not jornada:
            raise HTTPException(status_code=404, detail="Jornada no encontrada")
        
        tiempo_restante = JornadaLaboralService.calcular_tiempo_restante(jornada)
        return tiempo_restante
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al calcular tiempo restante: {str(e)}")