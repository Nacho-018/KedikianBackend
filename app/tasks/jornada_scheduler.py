# app/tasks/jornada_scheduler.py - NUEVO ARCHIVO

from apscheduler.schedulers.background import BackgroundScheduler
from app.db.dependencies import SessionLocal
from app.services.jornada_laboral_service import JornadaLaboralService
import logging

logger = logging.getLogger(__name__)

def verificar_jornadas_activas():
    """
    ✅ Tarea que se ejecuta cada minuto para verificar jornadas activas
    - Pausa automáticamente a las 9h
    - Finaliza automáticamente a las 13h
    """
    db = SessionLocal()
    try:
        logger.info("🔄 Verificando jornadas activas...")
        jornadas = JornadaLaboralService.verificar_y_actualizar_jornadas_activas(db)
        logger.info(f"✅ Verificadas {len(jornadas)} jornadas")
    except Exception as e:
        logger.error(f"❌ Error verificando jornadas: {str(e)}")
    finally:
        db.close()

def iniciar_scheduler():
    """✅ Inicia el scheduler de tareas programadas"""
    scheduler = BackgroundScheduler()
    
    # Verificar jornadas cada 1 minuto
    scheduler.add_job(
        verificar_jornadas_activas,
        'interval',
        minutes=1,
        id='verificar_jornadas',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Scheduler de jornadas iniciado (cada 1 minuto)")
    
    return scheduler