#!/usr/bin/env python3
"""
Script de migración para agregar campos de precio y tarifa
- Agrega precio_unitario a entrega_arido
- Agrega tarifa_hora a reporte_laboral

Ejecutar con: python migrate_precio_tarifa_fields.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Ejecuta la migración para agregar campos precio_unitario y tarifa_hora"""

    try:
        # Crear engine usando la configuración de la aplicación
        engine = create_engine(settings.DATABASE_URL)

        logger.info("🔄 Iniciando migración de campos precio_unitario y tarifa_hora...")
        logger.info(f"📊 Base de datos: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")

        # Verificar que las tablas existen
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        if 'entrega_arido' not in existing_tables:
            logger.error("❌ La tabla entrega_arido no existe")
            return False

        if 'reporte_laboral' not in existing_tables:
            logger.error("❌ La tabla reporte_laboral no existe")
            return False

        with engine.connect() as conn:
            db_dialect = engine.dialect.name
            logger.info(f"🔧 Detectado dialecto de base de datos: {db_dialect}")

            # 1. Agregar campo precio_unitario a entrega_arido
            logger.info("📝 Agregando campo precio_unitario a entrega_arido...")

            # Verificar si la columna ya existe
            entrega_arido_columns = [col['name'] for col in inspector.get_columns('entrega_arido')]

            if 'precio_unitario' not in entrega_arido_columns:
                try:
                    if db_dialect == 'postgresql':
                        conn.execute(text("""
                            ALTER TABLE entrega_arido
                            ADD COLUMN precio_unitario DOUBLE PRECISION NULL
                        """))
                    elif db_dialect == 'sqlite':
                        conn.execute(text("""
                            ALTER TABLE entrega_arido
                            ADD COLUMN precio_unitario REAL NULL
                        """))
                    logger.info("✅ Campo precio_unitario agregado a entrega_arido")
                except Exception as e:
                    logger.error(f"❌ Error al agregar precio_unitario: {e}")
                    return False
            else:
                logger.info("⚠️  Campo precio_unitario ya existe en entrega_arido")

            # 2. Agregar campo tarifa_hora a reporte_laboral
            logger.info("📝 Agregando campo tarifa_hora a reporte_laboral...")

            # Verificar si la columna ya existe
            reporte_laboral_columns = [col['name'] for col in inspector.get_columns('reporte_laboral')]

            if 'tarifa_hora' not in reporte_laboral_columns:
                try:
                    if db_dialect == 'postgresql':
                        conn.execute(text("""
                            ALTER TABLE reporte_laboral
                            ADD COLUMN tarifa_hora DOUBLE PRECISION NULL
                        """))
                    elif db_dialect == 'sqlite':
                        conn.execute(text("""
                            ALTER TABLE reporte_laboral
                            ADD COLUMN tarifa_hora REAL NULL
                        """))
                    logger.info("✅ Campo tarifa_hora agregado a reporte_laboral")
                except Exception as e:
                    logger.error(f"❌ Error al agregar tarifa_hora: {e}")
                    return False
            else:
                logger.info("⚠️  Campo tarifa_hora ya existe en reporte_laboral")

            # 3. Crear índices para mejorar rendimiento
            if db_dialect == 'postgresql':
                logger.info("📝 Creando índices adicionales para PostgreSQL...")

                indices = [
                    "CREATE INDEX IF NOT EXISTS idx_entrega_arido_tipo_fecha ON entrega_arido(tipo_arido, fecha_entrega)",
                    "CREATE INDEX IF NOT EXISTS idx_reporte_laboral_maquina_fecha ON reporte_laboral(maquina_id, fecha_asignacion)",
                    "CREATE INDEX IF NOT EXISTS idx_entrega_arido_proyecto_tipo_fecha ON entrega_arido(proyecto_id, tipo_arido, fecha_entrega)",
                    "CREATE INDEX IF NOT EXISTS idx_reporte_laboral_proyecto_maquina_fecha ON reporte_laboral(proyecto_id, maquina_id, fecha_asignacion)"
                ]

                for idx_sql in indices:
                    try:
                        conn.execute(text(idx_sql))
                        idx_name = idx_sql.split('IF NOT EXISTS')[1].split('ON')[0].strip()
                        logger.info(f"✅ Índice creado: {idx_name}")
                    except Exception as e:
                        logger.warning(f"⚠️  No se pudo crear índice: {e}")

                # Agregar comentarios descriptivos
                logger.info("📝 Agregando comentarios descriptivos...")
                try:
                    conn.execute(text("""
                        COMMENT ON COLUMN entrega_arido.precio_unitario IS
                        'Precio unitario del árido en el momento de la entrega (por m³)'
                    """))
                    conn.execute(text("""
                        COMMENT ON COLUMN reporte_laboral.tarifa_hora IS
                        'Tarifa por hora de la máquina en el momento del reporte'
                    """))
                    logger.info("✅ Comentarios agregados exitosamente")
                except Exception as e:
                    logger.warning(f"⚠️  No se pudieron agregar comentarios: {e}")

            elif db_dialect == 'sqlite':
                logger.info("📝 SQLite detectado - Los índices básicos ya están definidos")

            conn.commit()

        logger.info("✅ Migración completada exitosamente")
        return True

    except Exception as e:
        logger.error(f"❌ Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_migracion():
    """Verifica que la migración se haya aplicado correctamente"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        inspector = inspect(engine)

        # Verificar tabla entrega_arido
        entrega_arido_columns = [col['name'] for col in inspector.get_columns('entrega_arido')]
        if 'precio_unitario' not in entrega_arido_columns:
            logger.error("❌ El campo precio_unitario no existe en entrega_arido")
            return False
        logger.info("✅ Campo precio_unitario presente en entrega_arido")

        # Verificar tabla reporte_laboral
        reporte_laboral_columns = [col['name'] for col in inspector.get_columns('reporte_laboral')]
        if 'tarifa_hora' not in reporte_laboral_columns:
            logger.error("❌ El campo tarifa_hora no existe en reporte_laboral")
            return False
        logger.info("✅ Campo tarifa_hora presente en reporte_laboral")

        # Verificar índices (solo PostgreSQL)
        if engine.dialect.name == 'postgresql':
            indices_entrega = [idx['name'] for idx in inspector.get_indexes('entrega_arido')]
            indices_reporte = [idx['name'] for idx in inspector.get_indexes('reporte_laboral')]

            logger.info(f"📊 Índices en entrega_arido: {len(indices_entrega)}")
            logger.info(f"📊 Índices en reporte_laboral: {len(indices_reporte)}")

        logger.info("✅ Verificación exitosa: Todos los campos están presentes")
        return True

    except Exception as e:
        logger.error(f"❌ Error durante la verificación: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 MIGRACIÓN: Agregar campos precio_unitario y tarifa_hora")
    print("=" * 80)
    print()

    # Ejecutar migración
    success = run_migration()

    if success:
        print()
        print("=" * 80)
        print("🔍 Verificando migración...")
        print("=" * 80)
        print()

        # Verificar migración
        verificacion = verificar_migracion()

        if verificacion:
            print()
            print("=" * 80)
            print("🎉 ¡Migración completada y verificada exitosamente!")
            print("=" * 80)
            print()
            print("📋 Próximos pasos:")
            print("   1. Reiniciar el servidor FastAPI")
            print("   2. Verificar nuevos endpoints en /docs:")
            print("      - PUT /api/v1/proyectos/{id}/aridos/actualizar-precio")
            print("      - PUT /api/v1/proyectos/{id}/maquinas/actualizar-tarifa")
            print()
            print("💡 Ejemplo de uso:")
            print("   Actualizar precio de áridos:")
            print('   POST /api/v1/proyectos/1/aridos/actualizar-precio')
            print('   {')
            print('     "tipo_arido": "Arena",')
            print('     "nuevo_precio": 15000.50,')
            print('     "periodo_inicio": "2026-01-01",')
            print('     "periodo_fin": "2026-01-31"')
            print('   }')
            print()
            print("   Actualizar tarifa de máquina:")
            print('   POST /api/v1/proyectos/1/maquinas/actualizar-tarifa')
            print('   {')
            print('     "maquina_id": 5,')
            print('     "nueva_tarifa": 25000.00,')
            print('     "periodo_inicio": "2026-01-01",')
            print('     "periodo_fin": "2026-01-31"')
            print('   }')
            print()
        else:
            print()
            print("=" * 80)
            print("⚠️  Migración completada pero la verificación falló")
            print("=" * 80)
            exit(1)
    else:
        print()
        print("=" * 80)
        print("💥 Error en la migración")
        print("=" * 80)
        exit(1)
