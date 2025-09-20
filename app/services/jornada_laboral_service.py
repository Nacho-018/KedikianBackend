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
        Inicia una nueva jornada laboral
        """
        # Verificar que no haya una jornada activa
        jornada_activa = JornadaLaboralService.obtener_jornada_activa(db, usuario_id)
        if jornada_activa:
            raise HTTPException(
                status_code=409, 
                detail="Ya existe una jornada laboral activa para este usuario"
            )
        
        # Verificar que el usuario existe
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        now = datetime.now()
        today = now.date()
        
        # Crear nueva jornada
        jornada = JornadaLaboral(
            usuario_id=usuario_id,
            fecha=today,
            hora_inicio=now,
            estado='activa',
            notas_inicio=notas_inicio,
            ubicacion_inicio=json.dumps(ubicacion) if ubicacion else None,
            es_feriado=JornadaLaboralService._es_feriado(today)
        )
        
        db.add(jornada)
        db.commit()
        db.refresh(jornada)
        
        return jornada
    
    @staticmethod
    def pausar_por_limite_regular(
        db: Session,
        jornada_id: int
    ) -> JornadaLaboral:
        """
        Pausa automáticamente la jornada al alcanzar las 9 horas regulares
        """
        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        if not jornada:
            raise HTTPException(status_code=404, detail="Jornada no encontrada")
        
        jornada.pausar_por_limite()
        db.commit()
        db.refresh(jornada)
        
        return jornada
    
    @staticmethod
    def confirmar_horas_extras(
        db: Session,
        jornada_id: int,
        notas_overtime: Optional[str] = None
    ) -> JornadaLaboral:
        """
        Confirma las horas extras y reanuda la jornada
        """
        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        if not jornada:
            raise HTTPException(status_code=404, detail="Jornada no encontrada")
        
        if not jornada.limite_regular_alcanzado:
            raise HTTPException(
                status_code=400, 
                detail="No se han completado las 9 horas regulares"
            )
        
        jornada.reanudar_con_overtime(notas_overtime)
        db.commit()
        db.refresh(jornada)
        
        return jornada
    
    @staticmethod
    def rechazar_horas_extras(
        db: Session,
        jornada_id: int,
        tiempo_descanso: int = 60,
        notas_fin: Optional[str] = None
    ) -> JornadaLaboral:
        """
        Rechaza las horas extras y finaliza la jornada
        """
        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        if not jornada:
            raise HTTPException(status_code=404, detail="Jornada no encontrada")
        
        jornada.tiempo_descanso = tiempo_descanso
        jornada.finalizar_jornada(
            notas_fin=f"{notas_fin or ''} - Finalizado al completar 9 horas regulares",
            motivo="Rechazo de horas extras"
        )
        
        db.commit()
        db.refresh(jornada)
        
        return jornada
    
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
        Finaliza una jornada laboral
        """
        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        if not jornada:
            raise HTTPException(status_code=404, detail="Jornada no encontrada")
        
        if not jornada.is_active and not jornada.is_paused:
            raise HTTPException(
                status_code=400, 
                detail="La jornada no está activa o pausada"
            )
        
        # Actualizar tiempo de descanso y ubicación
        jornada.tiempo_descanso = tiempo_descanso
        if ubicacion:
            jornada.ubicacion_fin = json.dumps(ubicacion)
        
        # Finalizar según el tipo
        if forzado:
            jornada.finalizar_forzosamente("Finalización forzosa por el usuario")
        else:
            motivo = "Finalización normal" if not jornada.is_in_overtime else "Finalización de horas extras"
            jornada.finalizar_jornada(notas_fin=notas_fin, motivo=motivo)
        
        db.commit()
        db.refresh(jornada)
        
        return jornada
    
    @staticmethod
    def finalizar_automaticamente(
        db: Session,
        jornada_id: int,
        motivo: str = "Límite máximo de horas alcanzado"
    ) -> JornadaLaboral:
        """
        Finaliza automáticamente una jornada por límite de horas
        """
        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        if not jornada:
            raise HTTPException(status_code=404, detail="Jornada no encontrada")
        
        jornada.finalizar_forzosamente(motivo)
        db.commit()
        db.refresh(jornada)
        
        return jornada
    
    # ============ MÉTODOS DE CONSULTA ============
    
    @staticmethod
    def obtener_jornada_activa(db: Session, usuario_id: int) -> Optional[JornadaLaboral]:
        """
        Obtiene la jornada activa o pausada de un usuario
        """
        return db.query(JornadaLaboral).filter(
            and_(
                JornadaLaboral.usuario_id == usuario_id,
                JornadaLaboral.estado.in_(['activa', 'pausada']),
                JornadaLaboral.hora_fin.is_(None)
            )
        ).first()
    
    @staticmethod
    def obtener_jornada_por_id(db: Session, jornada_id: int) -> Optional[JornadaLaboral]:
        """
        Obtiene una jornada por su ID
        """
        return db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
    
    @staticmethod
    def obtener_jornadas_usuario(
        db: Session,
        usuario_id: int,
        limite: int = 10,
        offset: int = 0
    ) -> List[JornadaLaboral]:
        """
        Obtiene las jornadas de un usuario (más recientes primero)
        """
        return db.query(JornadaLaboral).filter(
            JornadaLaboral.usuario_id == usuario_id
        ).order_by(desc(JornadaLaboral.fecha), desc(JornadaLaboral.created)).offset(offset).limit(limite).all()
    
    @staticmethod
    def obtener_jornadas_periodo(
        db: Session,
        usuario_id: Optional[int] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        limite: int = 50
    ) -> List[JornadaLaboral]:
        """
        Obtiene jornadas por periodo
        """
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
        """
        Obtiene estadísticas del mes para un usuario
        """
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
            'jornadas': [j.to_dict() for j in jornadas]
        }
    
    # ============ MÉTODOS DE VALIDACIÓN Y CONTROL ============
    
    @staticmethod
    def actualizar_estado_jornada(db: Session, jornada_id: int) -> JornadaLaboral:
        """
        Actualiza el estado de una jornada basado en el tiempo transcurrido
        """
        jornada = db.query(JornadaLaboral).filter(JornadaLaboral.id == jornada_id).first()
        if not jornada or not jornada.is_active:
            return jornada
        
        # Calcular horas actuales
        jornada.calcular_horas()
        
        # Verificar si debe pausarse automáticamente (9 horas)
        if (jornada.horas_regulares >= 9.0 and 
            not jornada.limite_regular_alcanzado and 
            not jornada.overtime_confirmado):
            jornada.pausar_por_limite()
        
        # Verificar si debe finalizarse automáticamente (13 horas)
        elif jornada.debe_finalizar_automaticamente:
            jornada.finalizar_forzosamente("Límite máximo de 13 horas alcanzado")
        
        db.commit()
        db.refresh(jornada)
        
        return jornada
    
    @staticmethod
    def verificar_y_actualizar_jornadas_activas(db: Session) -> List[JornadaLaboral]:
        """
        Verifica y actualiza todas las jornadas activas (para ejecución periódica)
        """
        jornadas_activas = db.query(JornadaLaboral).filter(
            JornadaLaboral.estado.in_(['activa', 'pausada']),
            JornadaLaboral.hora_fin.is_(None)
        ).all()
        
        jornadas_actualizadas = []
        for jornada in jornadas_activas:
            jornada_actualizada = JornadaLaboralService.actualizar_estado_jornada(db, jornada.id)
            jornadas_actualizadas.append(jornada_actualizada)
        
        return jornadas_actualizadas
    
    # ============ MÉTODOS DE UTILIDAD ============
    
    @staticmethod
    def _es_feriado(fecha: date) -> bool:
        """
        Determina si una fecha es feriado (implementar según necesidades)
        """
        # Por ahora, solo domingos
        return fecha.weekday() == 6
    
    @staticmethod
    def calcular_tiempo_restante(jornada: JornadaLaboral) -> Dict[str, Any]:
        """
        Calcula el tiempo restante para diferentes límites
        """
        if not jornada.is_active:
            return {
                'tiempo_hasta_advertencia': 0,
                'tiempo_hasta_limite_regular': 0,
                'tiempo_hasta_limite_maximo': 0,
                'en_overtime': False
            }
        
        # Calcular tiempo trabajado hasta ahora
        now = datetime.now()
        tiempo_trabajado_min = (now - jornada.hora_inicio).total_seconds() / 60 - jornada.tiempo_descanso
        tiempo_trabajado_horas = tiempo_trabajado_min / 60
        
        # Calcular tiempos restantes
        tiempo_hasta_advertencia = max(0, (8 * 60) - tiempo_trabajado_min)  # 8 horas
        tiempo_hasta_limite_regular = max(0, (9 * 60) - tiempo_trabajado_min)  # 9 horas
        tiempo_hasta_limite_maximo = max(0, (13 * 60) - tiempo_trabajado_min)  # 13 horas
        
        return {
            'tiempo_hasta_advertencia': int(tiempo_hasta_advertencia),
            'tiempo_hasta_limite_regular': int(tiempo_hasta_limite_regular),
            'tiempo_hasta_limite_maximo': int(tiempo_hasta_limite_maximo),
            'en_overtime': tiempo_trabajado_horas > 9,
            'horas_trabajadas': round(tiempo_trabajado_horas, 2)
        }
    
    @staticmethod
    def obtener_resumen_dia(db: Session, usuario_id: int, fecha: date) -> Dict[str, Any]:
        """
        Obtiene resumen de jornadas para un día específico
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
                'estado': 'sin_actividad'
            }
        
        jornada_principal = jornadas[0]  # Asumir una jornada por día
        
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
            'en_overtime': jornada_principal.is_in_overtime
        }