"""
Script de diagnóstico para investigar jornadas que se finalizan automáticamente

Este script te ayudará a identificar:
1. Jornadas finalizadas forzosamente
2. Causas de finalización automática
3. Problemas con el cálculo de horas
4. Jornadas con pausa automática
"""

from app.db.database import SessionLocal
from app.db.models.jornada_laboral import JornadaLaboral
from app.db.models.usuario import Usuario
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
import sys

def diagnosticar_operario(usuario_id=None, dias_atras=7):
    """
    Diagnóstica jornadas de un operario específico o de todos

    Args:
        usuario_id: ID del operario (None para todos)
        dias_atras: Cuántos días hacia atrás revisar
    """
    db = SessionLocal()

    try:
        print("\n" + "="*80)
        print("DIAGNÓSTICO DE JORNADAS - FINALIZACIONES AUTOMÁTICAS")
        print("="*80 + "\n")

        # Fecha de inicio
        fecha_inicio = datetime.now() - timedelta(days=dias_atras)

        # Query base
        query = db.query(JornadaLaboral).filter(
            JornadaLaboral.created >= fecha_inicio
        )

        if usuario_id:
            query = query.filter(JornadaLaboral.usuario_id == usuario_id)
            usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
            if usuario:
                print(f"🔍 Analizando operario: {usuario.nombre} {usuario.apellido} (ID: {usuario_id})")
            else:
                print(f"⚠️  No se encontró operario con ID: {usuario_id}")
                return
        else:
            print("🔍 Analizando TODOS los operarios")

        print(f"📅 Período: Últimos {dias_atras} días (desde {fecha_inicio.strftime('%Y-%m-%d %H:%M')})\n")

        # ========================================================================
        # 1. JORNADAS FINALIZADAS FORZOSAMENTE
        # ========================================================================
        print("\n" + "-"*80)
        print("1️⃣  JORNADAS FINALIZADAS FORZOSAMENTE (finalizacion_forzosa = True)")
        print("-"*80)

        jornadas_forzosas = query.filter(
            JornadaLaboral.finalizacion_forzosa == True
        ).order_by(JornadaLaboral.created.desc()).all()

        if jornadas_forzosas:
            print(f"\n⚠️  Encontradas {len(jornadas_forzosas)} jornadas finalizadas forzosamente:\n")

            for j in jornadas_forzosas:
                usuario_obj = db.query(Usuario).filter(Usuario.id == j.usuario_id).first()
                nombre = f"{usuario_obj.nombre} {usuario_obj.apellido}" if usuario_obj else "Desconocido"

                duracion = ""
                if j.hora_fin and j.hora_inicio:
                    delta = j.hora_fin - j.hora_inicio
                    horas = delta.total_seconds() / 3600
                    duracion = f"{horas:.2f}h"

                print(f"  📌 ID: {j.id}")
                print(f"     Usuario: {nombre} (ID: {j.usuario_id})")
                print(f"     Fecha: {j.fecha}")
                print(f"     Inicio: {j.hora_inicio.strftime('%Y-%m-%d %H:%M:%S') if j.hora_inicio else 'N/A'}")
                print(f"     Fin: {j.hora_fin.strftime('%Y-%m-%d %H:%M:%S') if j.hora_fin else 'N/A'}")
                print(f"     Duración: {duracion}")
                print(f"     Total horas: {j.total_horas:.2f}h (Regulares: {j.horas_regulares:.2f}h, Extras: {j.horas_extras:.2f}h)")
                print(f"     Tiempo descanso: {j.tiempo_descanso} minutos")
                print(f"     Estado: {j.estado}")
                print(f"     ⚠️  Motivo: {j.motivo_finalizacion or 'No especificado'}")
                print(f"     Pausa automática: {j.pausa_automatica}")
                print(f"     Overtime confirmado: {j.overtime_confirmado}")
                print()
        else:
            print("\n✅ No se encontraron jornadas finalizadas forzosamente")

        # ========================================================================
        # 2. JORNADAS CON PAUSA AUTOMÁTICA
        # ========================================================================
        print("\n" + "-"*80)
        print("2️⃣  JORNADAS CON PAUSA AUTOMÁTICA (pausa_automatica = True)")
        print("-"*80)

        jornadas_pausadas = query.filter(
            JornadaLaboral.pausa_automatica == True
        ).order_by(JornadaLaboral.created.desc()).all()

        if jornadas_pausadas:
            print(f"\n⚠️  Encontradas {len(jornadas_pausadas)} jornadas con pausa automática:\n")

            for j in jornadas_pausadas:
                usuario_obj = db.query(Usuario).filter(Usuario.id == j.usuario_id).first()
                nombre = f"{usuario_obj.nombre} {usuario_obj.apellido}" if usuario_obj else "Desconocido"

                print(f"  📌 ID: {j.id}")
                print(f"     Usuario: {nombre} (ID: {j.usuario_id})")
                print(f"     Fecha: {j.fecha}")
                print(f"     Estado actual: {j.estado}")
                print(f"     Total horas: {j.total_horas:.2f}h")
                print(f"     Límite regular alcanzado: {j.limite_regular_alcanzado}")
                print(f"     Overtime confirmado: {j.overtime_confirmado}")
                print()
        else:
            print("\n✅ No se encontraron jornadas con pausa automática")

        # ========================================================================
        # 3. JORNADAS CON MUCHAS HORAS (>10h L-V o >6h sábados)
        # ========================================================================
        print("\n" + "-"*80)
        print("3️⃣  JORNADAS CON MUCHAS HORAS TRABAJADAS")
        print("-"*80)

        jornadas_largas = query.filter(
            JornadaLaboral.total_horas >= 10.0
        ).order_by(JornadaLaboral.total_horas.desc()).all()

        if jornadas_largas:
            print(f"\n⚠️  Encontradas {len(jornadas_largas)} jornadas con 10+ horas:\n")

            for j in jornadas_largas:
                usuario_obj = db.query(Usuario).filter(Usuario.id == j.usuario_id).first()
                nombre = f"{usuario_obj.nombre} {usuario_obj.apellido}" if usuario_obj else "Desconocido"

                es_sabado = "SÍ" if j.fecha.weekday() == 5 else "NO"
                limite = "8h" if j.fecha.weekday() == 5 else "12h"

                print(f"  📌 ID: {j.id}")
                print(f"     Usuario: {nombre} (ID: {j.usuario_id})")
                print(f"     Fecha: {j.fecha} (Sábado: {es_sabado}, Límite: {limite})")
                print(f"     Total horas: {j.total_horas:.2f}h")
                print(f"     Estado: {j.estado}")
                print(f"     Finalización forzosa: {j.finalizacion_forzosa}")
                print()
        else:
            print("\n✅ No se encontraron jornadas con muchas horas")

        # ========================================================================
        # 4. JORNADAS ACTIVAS ACTUALES
        # ========================================================================
        print("\n" + "-"*80)
        print("4️⃣  JORNADAS ACTIVAS ACTUALMENTE")
        print("-"*80)

        jornadas_activas_query = db.query(JornadaLaboral).filter(
            or_(
                JornadaLaboral.estado == 'activa',
                JornadaLaboral.estado == 'pausada'
            ),
            JornadaLaboral.hora_fin.is_(None)
        )

        if usuario_id:
            jornadas_activas_query = jornadas_activas_query.filter(
                JornadaLaboral.usuario_id == usuario_id
            )

        jornadas_activas = jornadas_activas_query.all()

        if jornadas_activas:
            print(f"\n⚠️  Encontradas {len(jornadas_activas)} jornadas activas:\n")

            for j in jornadas_activas:
                usuario_obj = db.query(Usuario).filter(Usuario.id == j.usuario_id).first()
                nombre = f"{usuario_obj.nombre} {usuario_obj.apellido}" if usuario_obj else "Desconocido"

                # Calcular tiempo transcurrido
                tiempo_transcurrido = datetime.now() - j.hora_inicio
                horas_transcurridas = tiempo_transcurrido.total_seconds() / 3600

                # Advertencia si lleva más de 12h
                advertencia = ""
                if horas_transcurridas > 12:
                    advertencia = " ⚠️  MÁS DE 12 HORAS"
                elif horas_transcurridas > 8:
                    advertencia = " ⚠️  MÁS DE 8 HORAS"

                print(f"  📌 ID: {j.id}")
                print(f"     Usuario: {nombre} (ID: {j.usuario_id})")
                print(f"     Fecha inicio: {j.hora_inicio.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"     Tiempo transcurrido: {horas_transcurridas:.2f}h{advertencia}")
                print(f"     Total horas: {j.total_horas:.2f}h")
                print(f"     Estado: {j.estado}")
                print(f"     Tiempo descanso: {j.tiempo_descanso} minutos")
                print()
        else:
            print("\n✅ No hay jornadas activas actualmente")

        # ========================================================================
        # 5. ESTADÍSTICAS GENERALES
        # ========================================================================
        print("\n" + "-"*80)
        print("5️⃣  ESTADÍSTICAS GENERALES")
        print("-"*80 + "\n")

        total_jornadas = query.count()
        total_forzosas = db.query(JornadaLaboral).filter(
            JornadaLaboral.created >= fecha_inicio,
            JornadaLaboral.finalizacion_forzosa == True
        )
        if usuario_id:
            total_forzosas = total_forzosas.filter(JornadaLaboral.usuario_id == usuario_id)
        total_forzosas = total_forzosas.count()

        porcentaje = (total_forzosas / total_jornadas * 100) if total_jornadas > 0 else 0

        print(f"  📊 Total jornadas: {total_jornadas}")
        print(f"  ⚠️  Finalizaciones forzosas: {total_forzosas} ({porcentaje:.1f}%)")

        # Motivos de finalización
        motivos = db.query(
            JornadaLaboral.motivo_finalizacion,
            db.func.count(JornadaLaboral.id).label('count')
        ).filter(
            JornadaLaboral.created >= fecha_inicio,
            JornadaLaboral.motivo_finalizacion.isnot(None)
        )

        if usuario_id:
            motivos = motivos.filter(JornadaLaboral.usuario_id == usuario_id)

        motivos = motivos.group_by(JornadaLaboral.motivo_finalizacion).all()

        if motivos:
            print(f"\n  📋 Motivos de finalización:")
            for motivo, count in motivos:
                print(f"     - {motivo}: {count} veces")

        print("\n" + "="*80)
        print("FIN DEL DIAGNÓSTICO")
        print("="*80 + "\n")

        # Recomendaciones
        print("💡 RECOMENDACIONES:\n")
        if total_forzosas > 0:
            print("  1. Revisa las jornadas con finalizacion_forzosa = True")
            print("  2. Verifica el campo 'motivo_finalizacion' para entender la causa")
            print("  3. Si encuentras 'Límite máximo alcanzado', el scheduler está finalizando por exceso de horas")
            print("  4. Si encuentras 'Auto-finalizada (>24h)', hay jornadas que no se finalizaron manualmente")
            print("  5. Considera ajustar los límites o deshabilitar el scheduler temporalmente")

        if len(jornadas_activas) > 0:
            print("\n  ⚠️  HAY JORNADAS ACTIVAS: Revisa si alguna lleva mucho tiempo activa")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n🔍 Script de Diagnóstico de Jornadas")
    print("=====================================\n")

    # Puedes especificar el usuario_id como argumento
    usuario_id = None
    dias = 7

    if len(sys.argv) > 1:
        try:
            usuario_id = int(sys.argv[1])
        except:
            print("⚠️  ID de usuario inválido, analizando todos los operarios")

    if len(sys.argv) > 2:
        try:
            dias = int(sys.argv[2])
        except:
            print("⚠️  Días inválidos, usando 7 días por defecto")

    if usuario_id:
        print(f"Uso: python diagnostico_jornadas.py {usuario_id} {dias}")
    else:
        print(f"Uso: python diagnostico_jornadas.py [usuario_id] [dias_atras]")
        print(f"     python diagnostico_jornadas.py 123 7  # Operario ID 123, últimos 7 días")
        print(f"     python diagnostico_jornadas.py         # Todos los operarios, últimos 7 días")

    print()

    diagnosticar_operario(usuario_id, dias)
