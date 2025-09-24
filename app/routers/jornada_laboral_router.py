# app/routers/jornada_laboral_router.py - VERSIÓN COMPLETAMENTE CORREGIDA

from fastapi import APIRouter, Depends, HTTPException, Query
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

# ✅ SCHEMAS CORREGIDOS PARA REQUEST BODY
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
    usuario_id: int = Query(..., description="ID del usuario"),
    notas_inicio: Optional[str] = Query(None, description="Notas de inicio"),
    db: Session = Depends(get_db)
):
    """
    ✅ CORREGIDO: Fichar entrada usando Query parameters
    """
    try:
        print(f"🚀 Fichando entrada para usuario: {usuario_id}")
        print(f"📝 Notas: {notas_inicio}")
        
        jornada = JornadaLaboralService.iniciar_jornada(
            db=db,
            usuario_id=usuario_id,
            notas_inicio=notas_inicio,
            ubicacion=None
        )
        
        response = JornadaLaboralResponse.from_orm(jornada)
        print(f"✅ Jornada creada con ID: {response.id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al fichar entrada: {str(e)}")

@router.put("/finalizar/{jornada_id}", response_model=JornadaLaboralResponse)
async def finalizar_jornada(
    jornada_id: int,
    tiempo_descanso: int = Query(60, description="Tiempo de descanso en minutos"),
    notas_fin: Optional[str] = Query(None, description="Notas de finalización"),
    forzado: bool = Query(False, description="Finalización forzada"),
    db: Session = Depends(get_db)
):
    """
    ✅ CORREGIDO: Finalizar jornada usando Query parameters
    """
    try:
        print(f"🛑 Finalizando jornada ID: {jornada_id}")
        print(f"⏰ Tiempo descanso: {tiempo_descanso} minutos")
        print(f"💪 Forzado: {forzado}")
        
        jornada = JornadaLaboralService.finalizar_jornada(
            db=db,
            jornada_id=jornada_id,
            tiempo_descanso=tiempo_descanso,
            notas_fin=notas_fin,
            ubicacion=None,
            forzado=forzado
        )
        
        response = JornadaLaboralResponse.from_orm(jornada)
        print(f"✅ Jornada finalizada: {response.id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al finalizar jornada: {str(e)}")

@router.put("/confirmar-overtime/{jornada_id}", response_model=JornadaLaboralResponse)
async def confirmar_horas_extras(
    jornada_id: int,
    notas_overtime: Optional[str] = Query(None, description="Notas de horas extras"),
    db: Session = Depends(get_db)
):
    """
    ✅ NUEVO: Confirmar horas extras
    """
    try:
        print(f"🕐 Confirmando horas extras para jornada: {jornada_id}")
        
        jornada = JornadaLaboralService.confirmar_horas_extras(
            db=db,
            jornada_id=jornada_id,
            notas_overtime=notas_overtime
        )
        
        response = JornadaLaboralResponse.from_orm(jornada)
        print(f"✅ Horas extras confirmadas: {response.id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al confirmar horas extras: {str(e)}")

@router.put("/rechazar-overtime/{jornada_id}", response_model=JornadaLaboralResponse)
async def rechazar_horas_extras(
    jornada_id: int,
    tiempo_descanso: int = Query(60, description="Tiempo de descanso en minutos"),
    notas_fin: Optional[str] = Query(None, description="Notas de finalización"),
    db: Session = Depends(get_db)
):
    """
    ✅ NUEVO: Rechazar horas extras y finalizar en 9 horas
    """
    try:
        print(f"❌ Rechazando horas extras para jornada: {jornada_id}")
        
        jornada = JornadaLaboralService.rechazar_horas_extras(
            db=db,
            jornada_id=jornada_id,
            tiempo_descanso=tiempo_descanso,
            notas_fin=notas_fin
        )
        
        response = JornadaLaboralResponse.from_orm(jornada)
        print(f"✅ Jornada finalizada en 9h regulares: {response.id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al rechazar horas extras: {str(e)}")

# ============ ENDPOINTS DE CONSULTA ============

@router.get("/activa/{usuario_id}", response_model=Optional[JornadaLaboralResponse])
async def obtener_jornada_activa(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    ✅ CORREGIDO: Obtener jornada activa con respuesta null si no existe
    """
    try:
        print(f"🔍 Buscando jornada activa para usuario: {usuario_id}")
        
        jornada = JornadaLaboralService.obtener_jornada_activa(db, usuario_id)
        
        if jornada:
            response = JornadaLaboralResponse.from_orm(jornada)
            print(f"✅ Jornada activa encontrada: {response.id}")
            return response
        else:
            print("ℹ️ No hay jornada activa")
            return None
            
    except Exception as e:
        print(f"❌ Error buscando jornada activa: {str(e)}")
        # En lugar de error, devolver None
        return None

@router.get("/usuario/{usuario_id}", response_model=List[JornadaLaboralResponse])
async def obtener_jornadas_usuario(
    usuario_id: int,
    limite: int = Query(10, description="Cantidad de registros"),
    offset: int = Query(0, description="Desde qué registro"),
    db: Session = Depends(get_db)
):
    """
    ✅ Obtener jornadas de un usuario
    """
    try:
        print(f"📋 Obteniendo jornadas para usuario: {usuario_id} (limite: {limite}, offset: {offset})")
        
        jornadas = JornadaLaboralService.obtener_jornadas_usuario(
            db=db,
            usuario_id=usuario_id,
            limite=limite,
            offset=offset
        )
        
        response = [JornadaLaboralResponse.from_orm(j) for j in jornadas]
        print(f"✅ Se encontraron {len(response)} jornadas")
        
        return response
        
    except Exception as e:
        print(f"❌ Error obteniendo jornadas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener jornadas: {str(e)}")

@router.get("/periodo", response_model=List[JornadaLaboralResponse])
async def obtener_jornadas_periodo(
    usuario_id: Optional[int] = Query(None, description="ID del usuario"),
    fecha_inicio: Optional[date] = Query(None, description="Fecha de inicio"),
    fecha_fin: Optional[date] = Query(None, description="Fecha de fin"),
    limite: int = Query(50, description="Cantidad máxima de registros"),
    db: Session = Depends(get_db)
):
    """
    ✅ Obtener jornadas por periodo
    """
    try:
        jornadas = JornadaLaboralService.obtener_jornadas_periodo(
            db=db,
            usuario_id=usuario_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            limite=limite
        )
        
        response = [JornadaLaboralResponse.from_orm(j) for j in jornadas]
        return response
        
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
    ✅ Obtener estadísticas del mes
    """
    try:
        print(f"📊 Obteniendo estadísticas para usuario {usuario_id}, {mes}/{anio}")
        
        estadisticas = JornadaLaboralService.obtener_estadisticas_mes(
            db=db,
            usuario_id=usuario_id,
            mes=mes,
            año=anio
        )
        
        response = EstadisticasJornadaResponse(**estadisticas)
        print(f"✅ Estadísticas obtenidas: {response.total_jornadas} jornadas, {response.total_horas} horas")
        
        return response
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")

# ============ ENDPOINTS DE CONTROL ============

@router.put("/actualizar-estado/{jornada_id}", response_model=JornadaLaboralResponse)
async def actualizar_estado_jornada(
    jornada_id: int,
    db: Session = Depends(get_db)
):
    """
    ✅ Actualizar estado de jornada basado en tiempo transcurrido
    """
    try:
        jornada = JornadaLaboralService.actualizar_estado_jornada(db, jornada_id)
        response = JornadaLaboralResponse.from_orm(jornada)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar estado: {str(e)}")

@router.get("/verificar-activas", response_model=List[JornadaLaboralResponse])
async def verificar_jornadas_activas(db: Session = Depends(get_db)):
    """
    ✅ Verificar y actualizar jornadas activas (para tareas programadas)
    """
    try:
        jornadas = JornadaLaboralService.verificar_y_actualizar_jornadas_activas(db)
        response = [JornadaLaboralResponse.from_orm(j) for j in jornadas]
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al verificar jornadas activas: {str(e)}")

@router.get("/resumen-dia/{usuario_id}/{fecha}")
async def obtener_resumen_dia(
    usuario_id: int,
    fecha: date,
    db: Session = Depends(get_db)
):
    """
    ✅ Obtener resumen de jornadas para un día específico
    """
    try:
        resumen = JornadaLaboralService.obtener_resumen_dia(db, usuario_id, fecha)
        return resumen
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener resumen del día: {str(e)}")

# ============ ENDPOINTS DE PRUEBA ============

@router.get("/test")
async def test_endpoint():
    """
    ✅ Endpoint de prueba para verificar conectividad
    """
    return {
        "message": "Router de jornadas laborales funcionando correctamente", 
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0"
    }

@router.get("/tiempo-restante/{jornada_id}")
async def calcular_tiempo_restante(
    jornada_id: int,
    db: Session = Depends(get_db)
):
    """
    ✅ Calcular tiempo restante para diferentes límites
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

# ============ ENDPOINT DE DEBUG PARA DESARROLLO ============

@router.get("/debug/{usuario_id}")
async def debug_jornada_usuario(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    🔧 ENDPOINT DE DEBUG - Solo para desarrollo
    """
    try:
        from app.db.models.jornada_laboral import JornadaLaboral
        
        # Obtener todas las jornadas del usuario
        all_jornadas = db.query(JornadaLaboral).filter(
            JornadaLaboral.usuario_id == usuario_id
        ).all()
        
        # Jornada activa
        active_jornada = JornadaLaboralService.obtener_jornada_activa(db, usuario_id)
        
        return {
            "usuario_id": usuario_id,
            "total_jornadas": len(all_jornadas),
            "jornada_activa": {
                "existe": active_jornada is not None,
                "id": active_jornada.id if active_jornada else None,
                "estado": active_jornada.estado if active_jornada else None,
                "hora_inicio": active_jornada.hora_inicio.isoformat() if active_jornada else None,
                "hora_fin": active_jornada.hora_fin.isoformat() if active_jornada and active_jornada.hora_fin else None
            },
            "ultimas_5_jornadas": [
                {
                    "id": j.id,
                    "fecha": j.fecha.isoformat(),
                    "estado": j.estado,
                    "total_horas": j.total_horas,
                    "horas_extras": j.horas_extras
                }
                for j in sorted(all_jornadas, key=lambda x: x.created, reverse=True)[:5]
            ]
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "usuario_id": usuario_id,
            "debug": "Error obteniendo información de debug"
        }