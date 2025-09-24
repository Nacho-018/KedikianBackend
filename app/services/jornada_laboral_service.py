# app/services/jornada_laboral_service.py - VERSIÓN COMPLETA CORREGIDA

from sqlalchemy.orm import Session
from sqlalchemy import and_, extract, func, desc
from app.db.models.jornada_laboral import JornadaLaboral
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
        """
        ✅ CORREGIDO: Inicia una nueva jornada laboral
        """
        print(f"🚀 Iniciando jornada para usuario {usuario_id}")
        
        # ✅ CRÍTICO: Verificar que no haya una jornada activa
        jornada_existente = JornadaLaboralService.obtener_jornada_activa(db, usuario_id)
        if jornada_existente:
            print(f"❌ Ya existe jornada activa: {jornada_existente.id}")
            raise HTTPException(
                status_code=409, 
                detail=f"Ya existe una jornada laboral activa (ID: {jornada_existente.id})"
            )
        
        # ✅ Verificar que el usuario existe
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            print(f"❌ Usuario no encontrado: {usuario_id}")
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        now = datetime.now()
        today = now.date()
        
        print(f"📅 Creando jornada para fecha: {today}")
        print(f"⏰ Hora de inicio: {now}")
        
        # ✅ CRÍTICO: Crear nueva jornada con todos los campos
        jornada = JornadaLaboral(
            usuario_id=usuario_id,
            fecha=today,
            hora_inicio=now,
            estado='activa',
            notas_inicio=notas_inicio,
            ubicacion_inicio=json.dumps(ubicacion) if ubicacion else None,
            es_feriado=JornadaLaboralService._es_feriado(today),
            
            # ✅ Inicializar campos de control
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
        """
        ✅ CORREGIDO: Finaliza una jornada laboral
        """
        print(f"🛑 Finalizando jornada ID: {jornada_id}")
        
        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        if not jornada:
            print(f"❌ Jornada no encontrada: {jornada_id}")
            raise HTTPException(status_code=404, detail="Jornada no encontrada")
        
        # ✅ Verificar que la jornada esté en estado válido para finalizar
        if jornada.estado not in ['activa', 'pausada']:
            print(f"❌ Jornada en estado inválido: {jornada.estado}")
            raise HTTPException(
                status_code=400, 
                detail=f"La jornada está en estado '{jornada.estado}' y no puede ser finalizada"
            )
        
        # ✅ Si ya está finalizada, no hacer nada
        if jornada.hora_fin is not None:
            print(f"⚠️ Jornada ya finalizada: {jornada.hora_fin}")
            return jornada
        
        now = datetime.now()
        
        # ✅ Actualizar campos de finalización
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
        
        # ✅ CRÍTICO: Calcular horas trabajadas
        JornadaLaboralService._calcular_horas_trabajadas(jornada)
        
        try:
            db.commit()
            db.refresh(jornada)
            
            print(f"✅ Jornada finalizada: Total {jornada.total_horas}h ({jornada.horas_regulares}h regulares + {jornada.horas_extras}h extras)")
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
        ✅ NUEVO: Confirma las horas extras y reanuda la jornada
        """
        print(f"🕐 Confirmando horas extras para jornada: {jornada_id}")
        
        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        if not jornada:
            raise HTTPException(status_code=404, detail="Jornada no encontrada")
        
        # ✅ Verificar que esté en estado pausado y que haya completado 9h
        if not jornada.limite_regular_alcanzado:
            raise HTTPException(
                status_code=400, 
                detail="No se han completado las 9 horas regulares"
            )
        
        # ✅ CRÍTICO: Reactivar la jornada para horas extras
        jornada.estado = 'activa'
        jornada.overtime_confirmado = True
        jornada.overtime_iniciado = datetime.now()
        jornada.overtime_solicitado = True
        
        if notas_overtime:
            current_notes = jornada.notas_fin or ''
            jornada.notas_fin = f"{current_notes} | Overtime: {notas_overtime}".strip()
        
        try:
            db.commit()
            db.refresh(jornada)
            
            print(f"✅ Horas extras confirmadas y jornada reactivada")
            return jornada
            
        except Exception as e:
            print(f"❌ Error confirmando horas extras: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al confirmar horas extras: {str(e)}")
    
    @staticmethod
    def rechazar_horas_extras(
        db: Session,
        jornada_id: int,
        tiempo_descanso: int = 60,
        notas_fin: Optional[str] = None
    ) -> JornadaLaboral:
        """
        ✅ NUEVO: Rechaza las horas extras y finaliza la jornada en 9 horas
        """
        print(f"❌ Rechazando horas extras para jornada: {jornada_id}")
        
        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        if not jornada:
            raise HTTPException(status_code=404, detail="Jornada no encontrada")
        
        # ✅ Finalizar la jornada normalmente
        return JornadaLaboralService.finalizar_jornada(
            db=db,
            jornada_id=jornada_id,
            tiempo_descanso=tiempo_descanso,
            notas_fin=f"{notas_fin or ''} - Finalizado al completar 9 horas regulares".strip(),
            forzado=False
        )
    
    # ============ MÉTODOS DE CONSULTA ============
    
    @staticmethod
    def obtener_jornada_activa(db: Session, usuario_id: int) -> Optional[JornadaLaboral]:
        """
        ✅ CORREGIDO: Obtiene la jornada activa o pausada de un usuario
        """
        jornada = db.query(JornadaLaboral).filter(
            and_(
                JornadaLaboral.usuario_id == usuario_id,
                JornadaLaboral.estado.in_(['activa', 'pausada']),
                JornadaLaboral.hora_fin.is_(None)
            )
        ).order_by(desc(JornadaLaboral.created)).first()
        
        if jornada:
            print(f"✅ Jornada activa encontrada: ID {jornada.id}, estado: {jornada.estado}")
            
            # ✅ Actualizar horas en tiempo real si está activa
            if jornada.estado == 'activa':
                JornadaLaboralService._calcular_horas_en_tiempo_real(jornada)
        else:
            print(f"ℹ️ No hay jornada activa para usuario {usuario_id}")
        
        return jornada
    
    @staticmethod
    def obtener_jornada_por_id(db: Session, jornada_id: int) -> Optional[JornadaLaboral]:
        """
        ✅ Obtiene una jornada por su ID
        """
        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        
        if jornada and jornada.estado == 'activa':
            JornadaLaboralService._calcular_horas_en_tiempo_real(jornada)
        
        return jornada
    
    @staticmethod
    def obtener_jornadas_usuario(
        db: Session,
        usuario_id: int,
        limite: int = 10,
        offset: int = 0
    ) -> List[JornadaLaboral]:
        """
        ✅ Obtiene las jornadas de un usuario (más recientes primero)
        """
        jornadas = db.query(JornadaLaboral).filter(
            JornadaLaboral.usuario_id == usuario_id
        ).order_by(desc(JornadaLaboral.fecha), desc(JornadaLaboral.created)).offset(offset).limit(limite).all()
        
        print(f"📋 Encontradas {len(jornadas)} jornadas para usuario {usuario_id}")
        return jornadas
    
    @staticmethod
    def obtener_jornadas_periodo(
        db: Session,
        usuario_id: Optional[int] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        limite: int = 50
    ) -> List[JornadaLaboral]:
        """
        ✅ Obtiene jornadas por periodo
        """
        query = db.query(JornadaLaboral)
        
        if usuario_id:
            query = query.filter(JornadaLaboral.usuario_id == usuario_id)
        
        if fecha_inicio:
            query = query.filter(JornadaLaboral.fecha >= fecha_inicio)
        
        if fecha_fin:
            query = query.filter(JornadaLaboral.fecha <= fecha_fin)
        
        jornadas = query.order_by(desc(JornadaLaboral.fecha)).limit(limite).all()
        
        print(f"📅 Encontradas {len(jornadas)} jornadas en el periodo")
        return jornadas
    
    @staticmethod
    def obtener_estadisticas_mes(
        db: Session,
        usuario_id: int,
        mes: int,
        año: int
    ) -> Dict[str, Any]:
        """
        ✅ Obtiene estadísticas del mes para un usuario
        """
        print(f"📊 Calculando estadísticas para usuario {usuario_id}, {mes}/{año}")
        
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
        
        estadisticas = {
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
        
        print(f"✅ Estadísticas calculadas: {total_jornadas} jornadas, {total_horas} horas totales")
        return estadisticas
    
    # ============ MÉTODOS DE VALIDACIÓN Y CONTROL ============
    
    @staticmethod
    def actualizar_estado_jornada(db: Session, jornada_id: int) -> JornadaLaboral:
        """
        ✅ Actualiza el estado de una jornada basado en el tiempo transcurrido
        """
        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        if not jornada or jornada.estado != 'activa':
            return jornada
        
        # ✅ Calcular horas actuales
        JornadaLaboralService._calcular_horas_en_tiempo_real(jornada)
        
        # ✅ Verificar si debe pausarse automáticamente (9 horas)
        if (jornada.horas_regulares >= 9.0 and 
            not jornada.limite_regular_alcanzado and 
            not jornada.overtime_confirmado):
            
            print(f"⏰ Pausando automáticamente jornada {jornada_id} por límite de 9h")
            jornada.estado = 'pausada'
            jornada.limite_regular_alcanzado = True
            jornada.pausa_automatica = True
            jornada.hora_limite_regular = datetime.now()
        
        # ✅ Verificar si debe finalizarse automáticamente (13 horas)
        elif jornada.total_horas >= 13.0:
            print(f"🚨 Finalizando automáticamente jornada {jornada_id} por límite de 13h")
            jornada.hora_fin = datetime.now()
            jornada.estado = 'completada'
            jornada.finalizacion_forzosa = True
            jornada.motivo_finalizacion = "Límite máximo de 13 horas alcanzado"
        
        try:
            db.commit()
            db.refresh(jornada)
            return jornada
        except Exception as e:
            print(f"❌ Error actualizando estado: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error actualizando estado: {str(e)}")
    
    @staticmethod
    def verificar_y_actualizar_jornadas_activas(db: Session) -> List[JornadaLaboral]:
        """
        ✅ Verifica y actualiza todas las jornadas activas (para ejecución periódica)
        """
        jornadas_activas = db.query(JornadaLaboral).filter(
            JornadaLaboral.estado.in_(['activa', 'pausada']),
            JornadaLaboral.hora_fin.is_(None)
        ).all()
        
        jornadas_actualizadas = []
        for jornada in jornadas_activas:
            try:
                jornada_actualizada = JornadaLaboralService.actualizar_estado_jornada(db, jornada.id)
                jornadas_actualizadas.append(jornada_actualizada)
            except Exception as e:
                print(f"❌ Error actualizando jornada {jornada.id}: {str(e)}")
        
        print(f"🔄 Verificadas {len(jornadas_activas)} jornadas activas")
        return jornadas_actualizadas
    
    # ============ MÉTODOS DE UTILIDAD ============
    
    @staticmethod
    def _es_feriado(fecha: date) -> bool:
        """
        ✅ Determina si una fecha es feriado
        """
        # Por ahora, solo domingos
        return fecha.weekday() == 6
    
    @staticmethod
    def _calcular_horas_trabajadas(jornada: JornadaLaboral) -> None:
        """
        ✅ CRÍTICO: Calcula las horas trabajadas de una jornada finalizada
        """
        if not jornada.hora_inicio or not jornada.hora_fin:
            print("⚠️ No se pueden calcular horas: faltan hora_inicio o hora_fin")
            return
        
        # ✅ Calcular tiempo total trabajado (descontando descansos)
        tiempo_total_ms = (jornada.hora_fin - jornada.hora_inicio).total_seconds() * 1000
        tiempo_descanso_ms = jornada.tiempo_descanso * 60 * 1000  # minutos a ms
        tiempo_trabajado_ms = tiempo_total_ms - tiempo_descanso_ms
        tiempo_trabajado_horas = max(0, tiempo_trabajado_ms / (1000 * 60 * 60))  # ms a horas
        
        # ✅ Separar horas regulares y extras
        if tiempo_trabajado_horas <= 9.0:
            jornada.horas_regulares = tiempo_trabajado_horas
            jornada.horas_extras = 0.0
        else:
            jornada.horas_regulares = 9.0
            jornada.horas_extras = min(4.0, tiempo_trabajado_horas - 9.0)
        
        jornada.total_horas = jornada.horas_regulares + jornada.horas_extras
        
        print(f"⏱️ Horas calculadas: {jornada.total_horas}h total ({jornada.horas_regulares}h regulares + {jornada.horas_extras}h extras)")
    
    @staticmethod
    def _calcular_horas_en_tiempo_real(jornada: JornadaLaboral) -> None:
        """
        ✅ NUEVO: Calcula las horas trabajadas en tiempo real para jornadas activas
        """
        if not jornada.hora_inicio:
            return
        
        now = datetime.now()
        
        # ✅ Calcular tiempo trabajado hasta ahora (descontando descansos)
        tiempo_total_ms = (now - jornada.hora_inicio).total_seconds() * 1000
        tiempo_descanso_ms = jornada.tiempo_descanso * 60 * 1000
        tiempo_trabajado_ms = tiempo_total_ms - tiempo_descanso_ms
        tiempo_trabajado_horas = max(0, tiempo_trabajado_ms / (1000 * 60 * 60))
        
        # ✅ Separar horas regulares y extras
        if tiempo_trabajado_horas <= 9.0:
            jornada.horas_regulares = tiempo_trabajado_horas
            jornada.horas_extras = 0.0
        else:
            jornada.horas_regulares = 9.0
            jornada.horas_extras = min(4.0, tiempo_trabajado_horas - 9.0)
        
        jornada.total_horas = jornada.horas_regulares + jornada.horas_extras
        
        # ✅ Actualizar estado de límite regular
        if jornada.horas_regulares >= 9.0 and not jornada.limite_regular_alcanzado:
            jornada.limite_regular_alcanzado = True
            jornada.hora_limite_regular = jornada.hora_inicio + timedelta(
                hours=9, 
                minutes=jornada.tiempo_descanso
            )
    
    @staticmethod
    def calcular_tiempo_restante(jornada: JornadaLaboral) -> Dict[str, Any]:
        """
        ✅ Calcula el tiempo restante para diferentes límites
        """
        if jornada.estado != 'activa':
            return {
                'tiempo_hasta_advertencia': 0,
                'tiempo_hasta_limite_regular': 0,
                'tiempo_hasta_limite_maximo': 0,
                'en_overtime': False,
                'horas_trabajadas': jornada.total_horas or 0
            }
        
        # ✅ Actualizar horas en tiempo real
        JornadaLaboralService._calcular_horas_en_tiempo_real(jornada)
        
        # ✅ Calcular tiempo trabajado en minutos
        tiempo_trabajado_min = jornada.total_horas * 60
        
        # ✅ Calcular tiempos restantes
        tiempo_hasta_advertencia = max(0, (8 * 60) - tiempo_trabajado_min)  # 8 horas
        tiempo_hasta_limite_regular = max(0, (9 * 60) - tiempo_trabajado_min)  # 9 horas
        tiempo_hasta_limite_maximo = max(0, (13 * 60) - tiempo_trabajado_min)  # 13 horas
        
        return {
            'tiempo_hasta_advertencia': int(tiempo_hasta_advertencia),
            'tiempo_hasta_limite_regular': int(tiempo_hasta_limite_regular),
            'tiempo_hasta_limite_maximo': int(tiempo_hasta_limite_maximo),
            'en_overtime': jornada.overtime_confirmado or False,
            'horas_trabajadas': round(jornada.total_horas, 2)
        }
    
    @staticmethod
    def obtener_resumen_dia(db: Session, usuario_id: int, fecha: date) -> Dict[str, Any]:
        """
        ✅ Obtiene resumen de jornadas para un día específico
        """
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
                'horas_regulares': 0,
                'horas_extras': 0,
                'estado': 'sin_actividad',
                'es_feriado': False,
                'en_overtime': False
            }
        
        jornada_principal = jornadas[0]  # Asumir una jornada por día
        
        # ✅ Si está activa, actualizar horas en tiempo real
        if jornada_principal.estado == 'activa':
            JornadaLaboralService._calcular_horas_en_tiempo_real(jornada_principal)
        
        return {
            'fecha': fecha.isoformat(),
            'tiene_jornadas': True,
            'jornada_id': jornada_principal.id,
            'estado': jornada_principal.estado,
            'hora_inicio': jornada_principal.hora_inicio.strftime('%H:%M') if jornada_principal.hora_inicio else None,
            'hora_fin': jornada_principal.hora_fin.strftime('%H:%M') if jornada_principal.hora_fin else None,
            'total_horas': jornada_principal.total_horas,
            'horas_regulares': jornada_principal.horas_regulares,
            'horas_extras': jornada_principal.horas_extras,
            'es_feriado': jornada_principal.es_feriado,
            'en_overtime': jornada_principal.overtime_confirmado or False
        }