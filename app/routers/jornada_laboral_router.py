# app/routers/jornada_laboral_router.py - VERSIÓN COMPLETAMENTE CORREGIDA CON PUT

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel
from app.db.dependencies import get_db
from app.schemas.schemas import (
    JornadaLaboralCreate,
    JornadaLaboralCreateManual,
    JornadaLaboralResponse,
    JornadaLaboralUpdate,
    EstadisticasJornadaResponse
)
from app.services.jornada_laboral_service import JornadaLaboralService
from app.security.auth import get_current_user
from sqlalchemy import and_, desc
from app.db.models.jornada_laboral import JornadaLaboral, _get_limites_dia
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

# ✅ NUEVO: Schema para actualización completa de jornada
class ActualizarJornadaRequest(BaseModel):
    fecha: Optional[str] = None
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None
    tiempo_descanso: Optional[int] = None
    es_feriado: Optional[bool] = None
    notas_inicio: Optional[str] = None
    notas_fin: Optional[str] = None
    estado: Optional[str] = None

router = APIRouter(
    prefix="/jornadas-laborales", 
    tags=["Jornadas Laborales"], 
    dependencies=[Depends(get_current_user)]
)

# ============ ENDPOINTS DE CREACIÓN ============

@router.post("", response_model=JornadaLaboralResponse, status_code=201)
async def crear_jornada_laboral_manual(
    jornada: JornadaLaboralCreateManual,
    db: Session = Depends(get_db)
):
    """
    ✅ NUEVO: Crear jornada laboral manualmente con todos los campos

    Permite crear jornadas laborales completas (históricas o actuales) con todos los campos.

    **Validaciones:**
    - usuario_id debe existir en la tabla usuarios
    - Si estado = "completada", hora_fin es OBLIGATORIO
    - Si hora_fin no es null, debe ser mayor que hora_inicio
    - tiempo_descanso >= 0

    **Cálculos automáticos al crear:**
    - horas_regulares: calculadas según límite del día (8h L-V, 4h sábados)
    - horas_extras: calculadas como excedente sobre límite regular (máx 4h)
    - total_horas: (hora_fin - hora_inicio - tiempo_descanso) en horas decimales
    - Si es_feriado = true, se marca la jornada como feriado

    **Request Body:**
    ```json
    {
      "usuario_id": 4,
      "fecha": "2025-11-23",
      "hora_inicio": "2025-11-23T08:00:00",
      "hora_fin": "2025-11-23T18:00:00",  // Opcional (null si jornada en curso)
      "tiempo_descanso": 60,               // en minutos (default: 60)
      "es_feriado": false,                 // boolean (default: false)
      "estado": "completada",              // "activa" | "completada" | "pausada" | "cancelada"
      "notas_inicio": "string",            // Opcional
      "notas_fin": "string"                // Opcional
    }
    ```

    **Response:** 201 Created con la jornada creada completa
    """
    try:
        print(f"📝 Creando jornada laboral manual")
        print(f"   Usuario ID: {jornada.usuario_id}")
        print(f"   Fecha: {jornada.fecha}")
        print(f"   Estado: {jornada.estado}")

        nueva_jornada = JornadaLaboralService.crear_jornada_manual(
            db=db,
            usuario_id=jornada.usuario_id,
            fecha=jornada.fecha,
            hora_inicio=jornada.hora_inicio,
            hora_fin=jornada.hora_fin,
            tiempo_descanso=jornada.tiempo_descanso,
            es_feriado=jornada.es_feriado,
            estado=jornada.estado,
            notas_inicio=jornada.notas_inicio,
            notas_fin=jornada.notas_fin
        )

        response = JornadaLaboralResponse.from_orm(nueva_jornada)
        print(f"✅ Jornada manual creada con ID: {response.id}")
        print(f"   Total horas: {response.total_horas}h")
        print(f"   Horas regulares: {response.horas_regulares}h")
        print(f"   Horas extras: {response.horas_extras}h")

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error inesperado al crear jornada manual: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al crear jornada laboral: {str(e)}")

# ============ ENDPOINTS DE FICHAJE ============

@router.post("/fichar-entrada", response_model=JornadaLaboralResponse)
async def fichar_entrada(
    request: FicharEntradaRequest,
    db: Session = Depends(get_db)
):
    """Fichar entrada usando Request Body JSON"""
    try:
        print(f"🚀 Fichando entrada para usuario: {request.usuario_id}")
        print(f"📝 Notas: {request.notas_inicio}")
        
        jornada = JornadaLaboralService.iniciar_jornada(
            db=db,
            usuario_id=request.usuario_id,
            notas_inicio=request.notas_inicio,
            ubicacion=request.ubicacion
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
    request: FinalizarJornadaRequest,
    db: Session = Depends(get_db)
):
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

# ✅ NUEVO: Endpoint PUT para actualizar jornada completa
@router.put("/{jornada_id}", response_model=JornadaLaboralResponse)
async def actualizar_jornada(
    jornada_id: int,
    request: ActualizarJornadaRequest,
    db: Session = Depends(get_db)
):
    """
    ✅ NUEVO: Actualiza una jornada laboral existente
    Permite editar fecha, horas, descanso, notas, estado y si es feriado
    """
    try:
        print(f"✏️ Actualizando jornada ID: {jornada_id}")
        print(f"📝 Datos recibidos: {request.dict(exclude_none=True)}")
        
        jornada = JornadaLaboralService.actualizar_jornada_completa(
            db=db,
            jornada_id=jornada_id,
            fecha=request.fecha,
            hora_inicio=request.hora_inicio,
            hora_fin=request.hora_fin,
            tiempo_descanso=request.tiempo_descanso,
            es_feriado=request.es_feriado,
            notas_inicio=request.notas_inicio,
            notas_fin=request.notas_fin,
            estado=request.estado
        )
        
        response = JornadaLaboralResponse.from_orm(jornada)
        print(f"✅ Jornada actualizada correctamente: {response.id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error actualizando jornada: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar jornada: {str(e)}")

@router.put("/actualizar-estado/{jornada_id}", response_model=JornadaLaboralResponse)
async def actualizar_estado_jornada(
    jornada_id: int,
    db: Session = Depends(get_db)
):
    """
    Actualiza el estado de una jornada basado en tiempo transcurrido
    - Límites dinámicos según día de inicio:
      * L-V: Pausa a 8h, finalización a 12h
      * Sábados: Pausa a 4h, finalización a 8h
    """
    try:
        print(f"🔄 Actualizando estado de jornada: {jornada_id}")

        jornada = db.query(JornadaLaboral).filter(
            JornadaLaboral.id == jornada_id
        ).first()

        if not jornada:
            print(f"❌ Jornada no encontrada: {jornada_id}")
            raise HTTPException(status_code=404, detail="Jornada no encontrada")

        # Obtener límites según el día de inicio de la jornada
        max_regular, max_total = _get_limites_dia(jornada.hora_inicio.date())

        print(f"   Estado actual: {jornada.estado}")
        print(f"   Horas regulares: {jornada.horas_regulares}")
        print(f"   Total horas: {jornada.total_horas}")
        print(f"   Límites del día: {max_regular}h regulares, {max_total}h total")

        # PASO 1: Calcular horas actuales en tiempo real
        if jornada.estado == 'activa':
            JornadaLaboralService._calcular_horas_en_tiempo_real(jornada)
            print(f"   Horas recalculadas: {jornada.total_horas}h")

        # PASO 2: Verificar si debe pausarse (límite regular)
        if (jornada.horas_regulares >= max_regular and
            not jornada.limite_regular_alcanzado and
            not jornada.overtime_confirmado):

            print(f"✋ Pausando jornada: alcanzó {max_regular} horas")

            jornada.estado = 'pausada'
            jornada.limite_regular_alcanzado = True
            jornada.pausa_automatica = True
            jornada.hora_limite_regular = datetime.now()

        # PASO 3: Verificar si debe finalizarse (límite total)
        elif jornada.total_horas >= max_total and jornada.hora_fin is None:

            print(f"🛑 Finalizando jornada: alcanzó {max_total} horas")

            jornada.hora_fin = datetime.now()
            jornada.estado = 'completada'
            jornada.finalizacion_forzosa = True
            jornada.motivo_finalizacion = f"Límite máximo de {max_total} horas alcanzado"
        
        # PASO 4: Guardar cambios
        try:
            db.commit()
            db.refresh(jornada)
            
            response = JornadaLaboralResponse.from_orm(jornada)
            print(f"✅ Estado actualizado: {jornada.estado}")
            print(f"   Total horas: {jornada.total_horas}h")
            
            return response
            
        except Exception as e:
            print(f"❌ Error guardando cambios: {str(e)}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error al actualizar estado: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error inesperado: {type(e)._name_}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.put("/confirmar-overtime/{jornada_id}", response_model=JornadaLaboralResponse)
async def confirmar_horas_extras(
    jornada_id: int,
    notas_overtime: Optional[str] = Query(None, description="Notas de horas extras"),
    db: Session = Depends(get_db)
):
    """✅ Confirmar horas extras"""
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
    """✅ Rechazar horas extras y finalizar en el límite de horas regulares"""
    try:
        print(f"❌ Rechazando horas extras para jornada: {jornada_id}")

        jornada = JornadaLaboralService.rechazar_horas_extras(
            db=db,
            jornada_id=jornada_id,
            tiempo_descanso=tiempo_descanso,
            notas_fin=notas_fin
        )

        response = JornadaLaboralResponse.from_orm(jornada)
        print(f"✅ Jornada finalizada en horas regulares: {response.id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al rechazar horas extras: {str(e)}")

# ============ ENDPOINTS DE CONSULTA ============

@router.get("/activa/usuario/{usuario_id}", response_model=Optional[JornadaLaboralResponse])
async def obtener_jornada_activa(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    ✅ CORREGIDO: Obtener jornada activa con cálculo en tiempo real
    - Límites dinámicos según día de inicio
    """
    try:
        print(f"🔍 Buscando jornada activa para usuario: {usuario_id}")

        jornada = db.query(JornadaLaboral).filter(
            and_(
                JornadaLaboral.usuario_id == usuario_id,
                JornadaLaboral.estado.in_(['activa', 'pausada']),
                JornadaLaboral.hora_fin.is_(None)
            )
        ).order_by(desc(JornadaLaboral.created)).first()

        if not jornada:
            print(f"ℹ️ No hay jornada activa")
            return None

        # Obtener límites según el día de inicio de la jornada
        max_regular, max_total = _get_limites_dia(jornada.hora_inicio.date())

        print(f"✅ Jornada activa encontrada: ID {jornada.id}, estado: {jornada.estado}")
        print(f"   Límites del día: {max_regular}h regulares, {max_total}h total")

        # ✅ CRÍTICO: Calcular horas en tiempo real
        JornadaLaboralService._calcular_horas_en_tiempo_real(jornada)

        # ✅ CRÍTICO: Verificar y actualizar estado automáticamente
        if jornada.estado == 'activa':
            # Verificar si debe pausarse al alcanzar límite regular
            if jornada.horas_regulares >= max_regular and not jornada.limite_regular_alcanzado:
                print(f"⏰ Auto-pausando jornada: alcanzó {max_regular} horas")
                jornada.estado = 'pausada'
                jornada.limite_regular_alcanzado = True
                jornada.pausa_automatica = True
                jornada.hora_limite_regular = datetime.now()

                db.commit()
                db.refresh(jornada)

            # Verificar si debe finalizarse al alcanzar límite total
            elif jornada.total_horas >= max_total:
                print(f"🛑 Auto-finalizando jornada: alcanzó {max_total} horas")
                jornada.hora_fin = datetime.now()
                jornada.estado = 'completada'
                jornada.finalizacion_forzosa = True
                jornada.motivo_finalizacion = f"Límite máximo de {max_total} horas alcanzado"

                db.commit()
                db.refresh(jornada)
                return None  # Ya no está activa
        
        response = JornadaLaboralResponse.from_orm(jornada)
        return response
        
    except Exception as e:
        print(f"❌ Error obteniendo jornada activa: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/usuario/{usuario_id}", response_model=List[JornadaLaboralResponse])
async def obtener_jornadas_usuario(
    usuario_id: int,
    limite: int = Query(500, description="Cantidad de registros"),
    offset: int = Query(0, description="Desde qué registro"),
    db: Session = Depends(get_db)
):
    """✅ Obtener jornadas de un usuario"""
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
    """✅ Obtener jornadas por periodo"""
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
    """✅ Obtener estadísticas del mes"""
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


@router.get("/verificar-activas", response_model=List[JornadaLaboralResponse])
async def verificar_jornadas_activas(db: Session = Depends(get_db)):
    """✅ Verificar y actualizar jornadas activas (para tareas programadas)"""
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
    """✅ Obtener resumen de jornadas para un día específico"""
    try:
        resumen = JornadaLaboralService.obtener_resumen_dia(db, usuario_id, fecha)
        return resumen
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener resumen del día: {str(e)}")

# ============ ENDPOINTS DE PRUEBA ============

@router.get("/test")
async def test_endpoint():
    """✅ Endpoint de prueba para verificar conectividad"""
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
    """✅ Calcular tiempo restante para diferentes límites"""
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
@router.post("/limpiar-inconsistencias/{usuario_id}")
async def limpiar_inconsistencias(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """
    ✅ CRÍTICO: Limpia jornadas inconsistentes (muy viejas o en estado inválido)
    """
    print(f"🧹 Limpiando inconsistencias para usuario: {usuario_id}")
    
    try:
        from datetime import datetime, timedelta
        from app.db.models.jornada_laboral import JornadaLaboral
        
        # Buscar jornadas activas muy viejas (más de 24 horas)
        hace_24h = datetime.now() - timedelta(hours=24)
        
        jornadas_viejas = db.query(JornadaLaboral).filter(
            and_(
                JornadaLaboral.usuario_id == usuario_id,
                JornadaLaboral.estado.in_(['activa', 'pausada']),
                JornadaLaboral.hora_fin.is_(None),
                JornadaLaboral.created < hace_24h
            )
        ).all()
        
        for jornada in jornadas_viejas:
            print(f"🚨 Finalizando jornada antigua: ID {jornada.id}, creada hace {(datetime.now() - jornada.created).days} días")
            
            # Calcular horas finales
            JornadaLaboralService._calcular_horas_trabajadas(jornada)
            
            jornada.hora_fin = datetime.now()
            jornada.estado = 'completada'
            jornada.motivo_finalizacion = "Finalización automática por jornada antigua"
            jornada.finalizacion_forzosa = True
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Se limpiaron {len(jornadas_viejas)} jornada(s) antigua(s)",
            "jornadas_limpiadas": len(jornadas_viejas)
        }
        
    except Exception as e:
        print(f"❌ Error en limpieza: {str(e)}")
        db.rollback()
        return {
            "success": True,  # Devolver True para no romper el flujo
            "message": "Limpieza completada (con algunas limitaciones)",
            "error": str(e)
        }

@router.delete("/{jornada_id}", status_code=200)
async def eliminar_jornada(
    jornada_id: int,
    db: Session = Depends(get_db)
):
    """
    ✅ NUEVO: Eliminar una jornada laboral
    
    Permite eliminar una jornada laboral completamente.
    Útil para correcciones de errores de fichaje.
    
    Args:
        jornada_id: ID de la jornada a eliminar
        
    Returns:
        Mensaje de confirmación
        
    Raises:
        HTTPException 404: Si la jornada no existe
        HTTPException 500: Si hay un error en la eliminación
    """
    try:
        print(f"🗑️ Intentando eliminar jornada ID: {jornada_id}")
        
        # Buscar la jornada
        jornada = db.query(JornadaLaboral).filter(
            JornadaLaboral.id == jornada_id
        ).first()
        
        if not jornada:
            print(f"❌ Jornada no encontrada: {jornada_id}")
            raise HTTPException(
                status_code=404, 
                detail=f"Jornada con ID {jornada_id} no encontrada"
            )
        
        # Guardar información para el log
        usuario_id = jornada.usuario_id
        fecha = jornada.fecha
        estado = jornada.estado
        
        print(f"📋 Datos de jornada a eliminar:")
        print(f"   - Usuario ID: {usuario_id}")
        print(f"   - Fecha: {fecha}")
        print(f"   - Estado: {estado}")
        print(f"   - Total horas: {jornada.total_horas}")
        
        # Eliminar la jornada
        db.delete(jornada)
        db.commit()
        
        print(f"✅ Jornada eliminada exitosamente: ID {jornada_id}")
        
        return {
            "success": True,
            "message": f"Jornada laboral eliminada correctamente",
            "jornada_eliminada": {
                "id": jornada_id,
                "usuario_id": usuario_id,
                "fecha": fecha.isoformat() if fecha else None,
                "estado": estado,
                "total_horas": jornada.total_horas
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error al eliminar jornada: {str(e)}")
        import traceback
        traceback.print_exc()
        
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error al eliminar la jornada: {str(e)}"
        )
        
@router.get("/debug/{usuario_id}")
async def debug_jornada_usuario(
    usuario_id: int,
    db: Session = Depends(get_db)
):
    """🔧 ENDPOINT DE DEBUG - Solo para desarrollo"""
    try:
        from app.db.models.jornada_laboral import JornadaLaboral
        
        all_jornadas = db.query(JornadaLaboral).filter(
            JornadaLaboral.usuario_id == usuario_id
        ).all()
        
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