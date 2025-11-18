# app/services/jornada_laboral_service.py - VERSIÓN CORREGIDA

from sqlalchemy.orm import Session
from sqlalchemy import and_, extract, func, desc
from app.db.models.jornada_laboral import JornadaLaboral, _es_sabado, _get_limites_dia
from app.db.models.usuario import Usuario
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from fastapi import HTTPException
import json

class JornadaLaboralService:
    
    # ============ MÉTODOS DE FICHAJE ============
    
    @staticmethod
    def iniciar_jornada(
        db: Session,
        usuario_id: int,
        notas_inicio: Optional[str] = None,
        ubicacion: Optional[Dict] = None
    ) -> JornadaLaboral:
        """✅ Inicia una nueva jornada laboral"""
        print(f"🚀 Iniciando jornada para usuario {usuario_id}")
        
        # Verificar que no haya una jornada activa
        jornada_existente = JornadaLaboralService.obtener_jornada_activa(db, usuario_id)
        if jornada_existente:
            print(f"❌ Ya existe jornada activa: {jornada_existente.id}")
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe una jornada laboral activa (ID: {jornada_existente.id})"
            )

        # Verificar que no sea domingo (bloqueado para fichaje)
        now = datetime.now()
        today = now.date()

        if today.weekday() == 6:  # Domingo
            print(f"❌ Intento de fichaje en domingo bloqueado")
            raise HTTPException(
                status_code=403,
                detail="No se permite fichar los domingos. Por favor, intenta en otro día."
            )

        # Verificar que el usuario existe
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Crear nueva jornada
        jornada = JornadaLaboral(
            usuario_id=usuario_id,
            fecha=today,
            hora_inicio=now,
            estado='activa',
            notas_inicio=notas_inicio,
            ubicacion_inicio=json.dumps(ubicacion) if ubicacion else None,
            es_feriado=JornadaLaboralService._es_feriado(today),
            tiempo_descanso=0,
            horas_regulares=0.0,
            horas_extras=0.0,
            total_horas=0.0,
            limite_regular_alcanzado=False,
            overtime_solicitado=False,
            overtime_confirmado=False,
            pausa_automatica=False,
            finalizacion_forzosa=False,
            advertencia_8h_mostrada=False,
            advertencia_limite_mostrada=False
        )
        
        try:
            db.add(jornada)
            db.commit()
            db.refresh(jornada)
            
            print(f"✅ Jornada creada exitosamente con ID: {jornada.id}")
            return jornada
            
        except Exception as e:
            print(f"❌ Error guardando jornada: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al guardar jornada: {str(e)}")
    
    @staticmethod
    def finalizar_jornada(
        db: Session,
        jornada_id: int,
        tiempo_descanso: int = 60,
        notas_fin: Optional[str] = None,
        ubicacion: Optional[Dict] = None,
        forzado: bool = False
    ) -> JornadaLaboral:
        """✅ Finaliza una jornada laboral"""
        print(f"🛑 Finalizando jornada ID: {jornada_id}")
        
        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        if not jornada:
            raise HTTPException(status_code=404, detail="Jornada no encontrada")
        
        if jornada.estado not in ['activa', 'pausada']:
            raise HTTPException(
                status_code=400, 
                detail=f"La jornada está en estado '{jornada.estado}' y no puede ser finalizada"
            )
        
        if jornada.hora_fin is not None:
            return jornada
        
        now = datetime.now()
        
        jornada.hora_fin = now
        jornada.estado = 'completada'
        jornada.tiempo_descanso = tiempo_descanso
        jornada.notas_fin = notas_fin
        jornada.finalizacion_forzosa = forzado
        
        if ubicacion:
            jornada.ubicacion_fin = json.dumps(ubicacion)
        
        if forzado:
            jornada.motivo_finalizacion = "Finalización forzosa"
        elif jornada.overtime_confirmado:
            jornada.motivo_finalizacion = "Finalización de horas extras"
        else:
            jornada.motivo_finalizacion = "Finalización normal"
        
        JornadaLaboralService._calcular_horas_trabajadas(jornada)
        
        try:
            db.commit()
            db.refresh(jornada)
            
            print(f"✅ Jornada finalizada: {jornada.total_horas}h ({jornada.horas_regulares}h + {jornada.horas_extras}h extras)")
            return jornada
            
        except Exception as e:
            print(f"❌ Error finalizando jornada: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al finalizar jornada: {str(e)}")
    
    @staticmethod
    def confirmar_horas_extras(
        db: Session,
        jornada_id: int,
        notas_overtime: Optional[str] = None
    ) -> JornadaLaboral:
        """
        ✅ CORREGIDO: Confirma horas extras después de alcanzar límite regular
        - L-V: después de 8h REALES trabajadas
        - Sábados: después de 4h REALES trabajadas
        """
        print(f"🕐 Confirmando horas extras para jornada: {jornada_id}")

        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        if not jornada:
            raise HTTPException(status_code=404, detail="Jornada no encontrada")

        # Obtener límites según el día de inicio de la jornada
        max_regular, _ = _get_limites_dia(jornada.hora_inicio.date())

        # ✅ Calcular horas en tiempo real PRIMERO
        if jornada.estado in ['activa', 'pausada']:
            JornadaLaboralService._calcular_horas_en_tiempo_real(jornada)
            print(f"   Horas trabajadas (sin descanso): {jornada.horas_regulares:.2f}h")

        # ✅ VALIDACIÓN: Estado activo o pausado
        if jornada.estado not in ['activa', 'pausada']:
            raise HTTPException(
                status_code=400,
                detail=f"La jornada debe estar activa o pausada. Estado actual: '{jornada.estado}'"
            )

        # ✅ VALIDACIÓN: Mínimo horas regulares REALES trabajadas (sin descanso)
        if jornada.horas_regulares < max_regular:
            raise HTTPException(
                status_code=400,
                detail=f"Debes completar {max_regular} horas trabajadas (sin descanso). Horas actuales: {jornada.horas_regulares:.2f}h"
            )
        
        # ✅ VALIDACIÓN: No finalizada
        if jornada.hora_fin is not None:
            raise HTTPException(status_code=400, detail="La jornada ya está finalizada")
        
        # ✅ VALIDACIÓN: No duplicar
        if jornada.overtime_confirmado:
            print(f"⚠️ Horas extras ya confirmadas")
            return jornada
        
        # ✅ ACTIVAR HORAS EXTRAS
        jornada.estado = 'activa'
        jornada.overtime_confirmado = True
        jornada.overtime_iniciado = datetime.now()
        jornada.overtime_solicitado = True
        jornada.limite_regular_alcanzado = True
        jornada.pausa_automatica = False
        
        if notas_overtime:
            jornada.notas_fin = f"{jornada.notas_fin or ''} | Overtime: {notas_overtime}".strip()
        
        try:
            db.commit()
            db.refresh(jornada)
            print(f"✅ Horas extras confirmadas: {jornada.horas_regulares:.2f}h regulares")
            return jornada
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def rechazar_horas_extras(
        db: Session,
        jornada_id: int,
        tiempo_descanso: int = 60,
        notas_fin: Optional[str] = None
    ) -> JornadaLaboral:
        """✅ Rechaza horas extras y finaliza en el límite de horas regulares"""
        return JornadaLaboralService.finalizar_jornada(
            db=db,
            jornada_id=jornada_id,
            tiempo_descanso=tiempo_descanso,
            notas_fin=f"{notas_fin or ''} - Finalizado en horas regulares".strip(),
            forzado=False
        )
    
    # ============ MÉTODOS DE CONSULTA ============
    
    @staticmethod
    def obtener_jornada_activa(db: Session, usuario_id: int) -> Optional[JornadaLaboral]:
        """
        ✅ Obtiene jornada activa y verifica límites automáticamente
        """
        jornada = db.query(JornadaLaboral).filter(
            and_(
                JornadaLaboral.usuario_id == usuario_id,
                JornadaLaboral.estado.in_(['activa', 'pausada']),
                JornadaLaboral.hora_fin.is_(None)
            )
        ).order_by(desc(JornadaLaboral.created)).first()
        
        if not jornada:
            return None
        
        # Limpiar jornadas muy antiguas (>24h)
        hace_24h = datetime.now() - timedelta(hours=24)
        if jornada.created < hace_24h:
            print(f"⚠️ Jornada antigua ({jornada.id}), finalizando automáticamente")
            JornadaLaboralService._calcular_horas_trabajadas(jornada)
            jornada.hora_fin = datetime.now()
            jornada.estado = 'completada'
            jornada.motivo_finalizacion = "Auto-finalizada (>24h)"
            jornada.finalizacion_forzosa = True
            db.commit()
            return None
        
        # ✅ Verificar límites automáticos
        if jornada.estado == 'activa':
            JornadaLaboralService.verificar_limites_automaticos(db, jornada)
        
        return jornada
    
    @staticmethod
    def obtener_jornada_por_id(db: Session, jornada_id: int) -> Optional[JornadaLaboral]:
        """✅ Obtiene jornada por ID"""
        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        
        if jornada and jornada.estado == 'activa':
            JornadaLaboralService._calcular_horas_en_tiempo_real(jornada)
        
        return jornada
    
    @staticmethod
    def obtener_jornadas_usuario(
        db: Session,
        usuario_id: int,
        limite: int = 500,
        offset: int = 0
    ) -> List[JornadaLaboral]:
        """✅ Obtiene jornadas de un usuario"""
        try:
            jornadas = db.query(JornadaLaboral).filter(
                JornadaLaboral.usuario_id == usuario_id
            ).order_by(
                desc(JornadaLaboral.fecha), 
                desc(JornadaLaboral.created)
            ).offset(offset).limit(limite).all()
            
            return jornadas
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            raise
    
    @staticmethod
    def obtener_jornadas_periodo(
        db: Session,
        usuario_id: Optional[int] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        limite: int = 50
    ) -> List[JornadaLaboral]:
        """✅ Obtiene jornadas por periodo"""
        query = db.query(JornadaLaboral)
        
        if usuario_id:
            query = query.filter(JornadaLaboral.usuario_id == usuario_id)
        if fecha_inicio:
            query = query.filter(JornadaLaboral.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(JornadaLaboral.fecha <= fecha_fin)
        
        return query.order_by(desc(JornadaLaboral.fecha)).limit(limite).all()
    
    @staticmethod
    def obtener_estadisticas_mes(
        db: Session,
        usuario_id: int,
        mes: int,
        año: int
    ) -> Dict[str, Any]:
        """✅ Estadísticas del mes"""
        jornadas = db.query(JornadaLaboral).filter(
            and_(
                JornadaLaboral.usuario_id == usuario_id,
                extract('month', JornadaLaboral.fecha) == mes,
                extract('year', JornadaLaboral.fecha) == año,
                JornadaLaboral.estado == 'completada'
            )
        ).all()
        
        total_jornadas = len(jornadas)
        total_horas_regulares = sum(j.horas_regulares for j in jornadas)
        total_horas_extras = sum(j.horas_extras for j in jornadas)
        total_horas = sum(j.total_horas for j in jornadas)
        jornadas_con_extras = len([j for j in jornadas if j.horas_extras > 0])
        promedio_horas_dia = total_horas / total_jornadas if total_jornadas > 0 else 0
        
        return {
            'mes': mes,
            'año': año,
            'total_jornadas': total_jornadas,
            'total_horas_regulares': round(total_horas_regulares, 2),
            'total_horas_extras': round(total_horas_extras, 2),
            'total_horas': round(total_horas, 2),
            'jornadas_con_extras': jornadas_con_extras,
            'promedio_horas_dia': round(promedio_horas_dia, 2),
            'jornadas': [
                {
                    'id': j.id,
                    'fecha': j.fecha.isoformat(),
                    'total_horas': j.total_horas,
                    'horas_regulares': j.horas_regulares,
                    'horas_extras': j.horas_extras,
                    'estado': j.estado,
                    'es_feriado': j.es_feriado
                }
                for j in jornadas
            ]
        }
    
    # ============ MÉTODOS DE VALIDACIÓN AUTOMÁTICA ============
    
    @staticmethod
    def verificar_limites_automaticos(db: Session, jornada: JornadaLaboral) -> None:
        """
        ✅ CORREGIDO: Verifica límites basándose en horas REALES trabajadas (sin descanso)
        - Límites dinámicos según día de inicio de jornada:
          * L-V: Pausa a 8h, finalización a 12h
          * Sábados: Pausa a 4h, finalización a 8h
        """
        # Obtener límites según el día de inicio de la jornada
        max_regular, max_total = _get_limites_dia(jornada.hora_inicio.date())

        # Calcular horas actuales (ya descuentan descanso)
        JornadaLaboralService._calcular_horas_en_tiempo_real(jornada)

        cambio_realizado = False

        # LÍMITE 1: Horas regulares alcanzadas (pausa automática)
        if (jornada.horas_regulares >= max_regular and
            not jornada.limite_regular_alcanzado and
            not jornada.overtime_confirmado):

            print(f"⏰ AUTO-PAUSA: Jornada {jornada.id} alcanzó {max_regular}h REALES trabajadas")
            print(f"   (Tiempo total transcurrido: {jornada.total_horas:.2f}h incluye {jornada.tiempo_descanso}min descanso)")

            jornada.estado = 'pausada'
            jornada.limite_regular_alcanzado = True
            jornada.pausa_automatica = True
            jornada.hora_limite_regular = datetime.now()
            cambio_realizado = True

        # LÍMITE 2: Horas totales máximas alcanzadas (finalización automática)
        if jornada.total_horas >= max_total:
            print(f"🛑 AUTO-FINALIZACIÓN: Jornada {jornada.id} alcanzó {max_total}h REALES trabajadas")
            print(f"   Horas regulares: {jornada.horas_regulares:.2f}h")
            print(f"   Horas extras: {jornada.horas_extras:.2f}h")

            jornada.hora_fin = datetime.now()
            jornada.estado = 'completada'
            jornada.finalizacion_forzosa = True
            jornada.motivo_finalizacion = f"Límite máximo de {max_total}h REALES trabajadas alcanzado"

            # Calcular horas finales
            JornadaLaboralService._calcular_horas_trabajadas(jornada)
            cambio_realizado = True
        
        if cambio_realizado:
            try:
                db.commit()
                db.refresh(jornada)
                print(f"✅ Estado actualizado automáticamente")
            except Exception as e:
                print(f"❌ Error actualizando estado: {str(e)}")
                db.rollback()
    
    @staticmethod
    def actualizar_estado_jornada(db: Session, jornada_id: int) -> JornadaLaboral:
        """✅ Actualiza estado basado en tiempo transcurrido"""
        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        if not jornada or jornada.estado not in ['activa', 'pausada']:
            return jornada
        
        JornadaLaboralService.verificar_limites_automaticos(db, jornada)
        return jornada
    
    @staticmethod
    def verificar_y_actualizar_jornadas_activas(db: Session) -> List[JornadaLaboral]:
        """✅ Verifica TODAS las jornadas activas (para CRON job)"""
        jornadas_activas = db.query(JornadaLaboral).filter(
            JornadaLaboral.estado.in_(['activa', 'pausada']),
            JornadaLaboral.hora_fin.is_(None)
        ).all()
        
        jornadas_actualizadas = []
        for jornada in jornadas_activas:
            try:
                JornadaLaboralService.verificar_limites_automaticos(db, jornada)
                jornadas_actualizadas.append(jornada)
            except Exception as e:
                print(f"❌ Error actualizando jornada {jornada.id}: {str(e)}")
        
        print(f"🔄 Verificadas {len(jornadas_activas)} jornadas activas")
        return jornadas_actualizadas
    
    # ============ MÉTODOS DE UTILIDAD ============
    
    @staticmethod
    def _es_feriado(fecha: date) -> bool:
        """✅ Determina si es feriado (domingos - bloqueados para fichaje)"""
        return fecha.weekday() == 6  # 6 = Domingo
    
    @staticmethod
    def _calcular_horas_trabajadas(jornada: JornadaLaboral) -> None:
        """
        ✅ CORREGIDO: Calcula horas trabajadas descontando tiempo de descanso
        - Límites dinámicos según día de inicio:
          * L-V: Regulares máx 8h, Total máx 12h
          * Sábados: Regulares máx 4h, Total máx 8h
        - Horas extras: hasta 4h adicionales
        """
        if not jornada.hora_inicio or not jornada.hora_fin:
            return

        # Obtener límites según el día de inicio de la jornada
        max_regular, _ = _get_limites_dia(jornada.hora_inicio.date())

        # Tiempo total transcurrido en milisegundos
        tiempo_total_ms = (jornada.hora_fin - jornada.hora_inicio).total_seconds() * 1000

        # Tiempo de descanso en milisegundos
        tiempo_descanso_ms = jornada.tiempo_descanso * 60 * 1000

        # ✅ CRÍTICO: Tiempo trabajado = Total - Descanso
        tiempo_trabajado_ms = tiempo_total_ms - tiempo_descanso_ms
        tiempo_trabajado_horas = max(0, tiempo_trabajado_ms / (1000 * 60 * 60))

        print(f"📊 Cálculo de horas:")
        print(f"   Tiempo total transcurrido: {tiempo_total_ms / (1000 * 60 * 60):.2f}h")
        print(f"   Descanso descontado: {tiempo_descanso_ms / (1000 * 60 * 60):.2f}h ({jornada.tiempo_descanso}min)")
        print(f"   Tiempo trabajado REAL: {tiempo_trabajado_horas:.2f}h")

        # ✅ Distribuir entre regulares y extras según límites del día
        if tiempo_trabajado_horas <= max_regular:
            # Si trabajó menos que el límite regular, todo es regular
            jornada.horas_regulares = tiempo_trabajado_horas
            jornada.horas_extras = 0.0
        else:
            # Si trabajó más que el límite regular, el exceso son extras (máx 4h)
            jornada.horas_regulares = max_regular
            jornada.horas_extras = min(4.0, tiempo_trabajado_horas - max_regular)

        jornada.total_horas = jornada.horas_regulares + jornada.horas_extras

        print(f"✅ Resultado final:")
        print(f"   Horas regulares: {jornada.horas_regulares:.2f}h (límite: {max_regular}h)")
        print(f"   Horas extras: {jornada.horas_extras:.2f}h")
        print(f"   Total trabajado: {jornada.total_horas:.2f}h")

    @staticmethod
    def _calcular_horas_en_tiempo_real(jornada: JornadaLaboral) -> None:
        """
        ✅ CORREGIDO: Calcula horas en tiempo real descontando descanso
        - Las horas_regulares muestran tiempo REAL trabajado (sin descanso)
        - Límites dinámicos según día de inicio:
          * L-V: 8h regulares
          * Sábados: 4h regulares
        """
        if not jornada.hora_inicio:
            return

        # Obtener límites según el día de inicio de la jornada
        max_regular, _ = _get_limites_dia(jornada.hora_inicio.date())

        now = datetime.now()

        # Tiempo total transcurrido
        tiempo_total_ms = (now - jornada.hora_inicio).total_seconds() * 1000

        # ✅ CRÍTICO: Restar tiempo de descanso
        tiempo_descanso_ms = jornada.tiempo_descanso * 60 * 1000
        tiempo_trabajado_ms = tiempo_total_ms - tiempo_descanso_ms
        tiempo_trabajado_horas = max(0, tiempo_trabajado_ms / (1000 * 60 * 60))

        # Distribuir entre regulares y extras según límites del día
        if tiempo_trabajado_horas <= max_regular:
            jornada.horas_regulares = tiempo_trabajado_horas
            jornada.horas_extras = 0.0
        else:
            jornada.horas_regulares = max_regular
            jornada.horas_extras = min(4.0, tiempo_trabajado_horas - max_regular)

        jornada.total_horas = jornada.horas_regulares + jornada.horas_extras

        # ✅ Marcar límite cuando llegue al límite regular REALES trabajadas
        if jornada.horas_regulares >= max_regular and not jornada.limite_regular_alcanzado:
            jornada.limite_regular_alcanzado = True
            # Calcular cuándo alcanzó el límite regular (hora_inicio + max_regular + descanso)
            jornada.hora_limite_regular = jornada.hora_inicio + timedelta(
                hours=max_regular,
                minutes=jornada.tiempo_descanso
            )
    
    @staticmethod
    def calcular_tiempo_restante(jornada: JornadaLaboral) -> Dict[str, Any]:
        """
        ✅ CORREGIDO: Calcula tiempo restante considerando descanso
        - Límites dinámicos según día de inicio:
          * L-V: Advertencia 7h, Pausa 8h, Finalización 12h
          * Sábados: Advertencia 3h, Pausa 4h, Finalización 8h
        """
        if jornada.estado != 'activa':
            return {
                'tiempo_hasta_advertencia': 0,
                'tiempo_hasta_limite_regular': 0,
                'tiempo_hasta_limite_maximo': 0,
                'en_overtime': False,
                'horas_trabajadas': jornada.total_horas or 0,
                'horas_regulares': jornada.horas_regulares or 0,
                'tiempo_descanso_minutos': jornada.tiempo_descanso or 0
            }

        # Obtener límites según el día de inicio de la jornada
        max_regular, max_total = _get_limites_dia(jornada.hora_inicio.date())

        # Actualizar horas en tiempo real
        JornadaLaboralService._calcular_horas_en_tiempo_real(jornada)

        # ✅ CRÍTICO: Calcular en base a horas REALES trabajadas (sin descanso)
        tiempo_trabajado_min = jornada.total_horas * 60

        # Advertencia 1 hora antes del límite regular
        hora_advertencia = max_regular - 1

        # Tiempo restante para cada límite
        tiempo_hasta_advertencia = max(0, (hora_advertencia * 60) - tiempo_trabajado_min)
        tiempo_hasta_limite_regular = max(0, (max_regular * 60) - tiempo_trabajado_min)
        tiempo_hasta_limite_maximo = max(0, (max_total * 60) - tiempo_trabajado_min)

        return {
            'tiempo_hasta_advertencia': int(tiempo_hasta_advertencia),
            'tiempo_hasta_limite_regular': int(tiempo_hasta_limite_regular),
            'tiempo_hasta_limite_maximo': int(tiempo_hasta_limite_maximo),
            'en_overtime': jornada.overtime_confirmado or False,
            'horas_trabajadas': round(jornada.total_horas, 2),
            'horas_regulares': round(jornada.horas_regulares, 2),
            'horas_extras': round(jornada.horas_extras or 0, 2),
            'tiempo_descanso_minutos': jornada.tiempo_descanso or 0,
            'descripcion': f"{int(jornada.horas_regulares)}h {int((jornada.horas_regulares % 1) * 60)}min trabajadas (descanso descontado: {jornada.tiempo_descanso}min)"
        }
    
    # ============ MÉTODOS ADICIONALES ============
    
    @staticmethod
    def actualizar_jornada_completa(
        db: Session,
        jornada_id: int,
        fecha: Optional[str] = None,
        hora_inicio: Optional[str] = None,
        hora_fin: Optional[str] = None,
        tiempo_descanso: Optional[int] = None,
        es_feriado: Optional[bool] = None,
        notas_inicio: Optional[str] = None,
        notas_fin: Optional[str] = None,
        estado: Optional[str] = None
    ) -> JornadaLaboral:
        """✅ Actualiza jornada completa"""
        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        if not jornada:
            raise HTTPException(status_code=404, detail="Jornada no encontrada")
        
        if fecha:
            jornada.fecha = date.fromisoformat(fecha)
        if hora_inicio:
            jornada.hora_inicio = datetime.fromisoformat(hora_inicio)
        if hora_fin:
            jornada.hora_fin = datetime.fromisoformat(hora_fin) if hora_fin else None
        if tiempo_descanso is not None:
            jornada.tiempo_descanso = tiempo_descanso
        if es_feriado is not None:
            jornada.es_feriado = es_feriado
        if notas_inicio is not None:
            jornada.notas_inicio = notas_inicio
        if notas_fin is not None:
            jornada.notas_fin = notas_fin
        if estado is not None:
            if estado.lower() not in ['activa', 'pausada', 'completada', 'cancelada']:
                raise HTTPException(status_code=400, detail="Estado inválido")
            jornada.estado = estado.lower()
        
        if jornada.hora_fin or jornada.estado == 'completada':
            JornadaLaboralService._calcular_horas_trabajadas(jornada)
        
        try:
            db.commit()
            db.refresh(jornada)
            return jornada
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    
    @staticmethod
    def obtener_resumen_dia(db: Session, usuario_id: int, fecha: date) -> Dict[str, Any]:
        """✅ Resumen del día"""
        jornadas = db.query(JornadaLaboral).filter(
            and_(
                JornadaLaboral.usuario_id == usuario_id,
                JornadaLaboral.fecha == fecha
            )
        ).all()
        
        if not jornadas:
            return {
                'fecha': fecha.isoformat(),
                'tiene_jornadas': False,
                'total_horas': 0,
                'estado': 'sin_actividad'
            }
        
        jornada = jornadas[0]
        
        if jornada.estado == 'activa':
            JornadaLaboralService._calcular_horas_en_tiempo_real(jornada)
        
        return {
            'fecha': fecha.isoformat(),
            'tiene_jornadas': True,
            'jornada_id': jornada.id,
            'estado': jornada.estado,
            'hora_inicio': jornada.hora_inicio.strftime('%H:%M') if jornada.hora_inicio else None,
            'hora_fin': jornada.hora_fin.strftime('%H:%M') if jornada.hora_fin else None,
            'total_horas': jornada.total_horas,
            'horas_regulares': jornada.horas_regulares,
            'horas_extras': jornada.horas_extras,
            'es_feriado': jornada.es_feriado,
            'en_overtime': jornada.overtime_confirmado or False
        }