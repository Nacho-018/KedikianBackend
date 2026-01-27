#!/usr/bin/env python3
"""
Script de migración para crear la tabla reportes_cuenta_corriente
Sistema de Cuenta Corriente - Reportes de áridos y horas por proyecto

Ejecutar con: python migrate_reportes_cuenta_corriente.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings
from app.db.models import Base, ReporteCuentaCorriente
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Ejecuta la migración para crear la tabla reportes_cuenta_corriente"""

    try:
        # Crear engine usando la configuración de la aplicación
        engine = create_engine(settings.DATABASE_URL)

        logger.info("🔄 Iniciando migración de reportes_cuenta_corriente...")
        logger.info(f"📊 Base de datos: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")

        # Verificar si la tabla ya existe
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        if 'reportes_cuenta_corriente' in existing_tables:
            logger.warning("⚠️  La tabla reportes_cuenta_corriente ya existe")
            respuesta = input("¿Deseas recrearla? (s/N): ")
            if respuesta.lower() != 's':
                logger.info("❌ Migración cancelada por el usuario")
                return False

            # Eliminar la tabla existente
            with engine.connect() as conn:
                logger.info("🗑️  Eliminando tabla existente...")
                conn.execute(text("DROP TABLE IF EXISTS reportes_cuenta_corriente CASCADE"))
                conn.commit()

        # Crear la tabla usando SQLAlchemy ORM
        logger.info("📝 Creando tabla reportes_cuenta_corriente...")
        Base.metadata.create_all(engine, tables=[ReporteCuentaCorriente.__table__])

        # Crear índices adicionales si la BD es PostgreSQL
        with engine.connect() as conn:
            db_dialect = engine.dialect.name
            logger.info(f"🔧 Detectado dialecto de base de datos: {db_dialect}")

            if db_dialect == 'postgresql':
                logger.info("📝 Creando índices adicionales para PostgreSQL...")

                indices = [
                    "CREATE INDEX IF NOT EXISTS idx_reportes_cc_proyecto_id ON reportes_cuenta_corriente(proyecto_id)",
                    "CREATE INDEX IF NOT EXISTS idx_reportes_cc_periodo ON reportes_cuenta_corriente(periodo_inicio, periodo_fin)",
                    "CREATE INDEX IF NOT EXISTS idx_reportes_cc_fecha_generacion ON reportes_cuenta_corriente(fecha_generacion DESC)",
                    "CREATE INDEX IF NOT EXISTS idx_reportes_cc_estado ON reportes_cuenta_corriente(estado)"
                ]

                for idx_sql in indices:
                    try:
                        conn.execute(text(idx_sql))
                        logger.info(f"✅ Índice creado: {idx_sql.split('IF NOT EXISTS')[1].split('ON')[0].strip()}")
                    except Exception as e:
                        logger.warning(f"⚠️  No se pudo crear índice: {e}")

                # Crear trigger para actualizar campo 'updated'
                logger.info("📝 Creando trigger para campo 'updated'...")
                try:
                    conn.execute(text("""
                        CREATE OR REPLACE FUNCTION update_reportes_cuenta_corriente_updated_column()
                        RETURNS TRIGGER AS $$
                        BEGIN
                            NEW.updated = CURRENT_TIMESTAMP;
                            RETURN NEW;
                        END;
                        $$ language 'plpgsql'
                    """))

                    conn.execute(text("""
                        DROP TRIGGER IF EXISTS trigger_update_reportes_cuenta_corriente_updated ON reportes_cuenta_corriente
                    """))

                    conn.execute(text("""
                        CREATE TRIGGER trigger_update_reportes_cuenta_corriente_updated
                            BEFORE UPDATE ON reportes_cuenta_corriente
                            FOR EACH ROW
                            EXECUTE FUNCTION update_reportes_cuenta_corriente_updated_column()
                    """))

                    logger.info("✅ Trigger creado exitosamente")
                except Exception as e:
                    logger.warning(f"⚠️  No se pudo crear trigger: {e}")

                conn.commit()

            elif db_dialect == 'sqlite':
                logger.info("📝 SQLite detectado - Los índices básicos se crean automáticamente")

        # Verificar que la tabla se creó correctamente
        inspector = inspect(engine)
        if 'reportes_cuenta_corriente' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('reportes_cuenta_corriente')]
            logger.info(f"✅ Tabla creada exitosamente con {len(columns)} columnas:")
            for col in columns:
                logger.info(f"   - {col}")

            # Mostrar índices creados
            indices = inspector.get_indexes('reportes_cuenta_corriente')
            if indices:
                logger.info(f"📊 Índices creados: {len(indices)}")
                for idx in indices:
                    logger.info(f"   - {idx['name']}: {idx['column_names']}")

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

        if 'reportes_cuenta_corriente' not in inspector.get_table_names():
            logger.error("❌ La tabla reportes_cuenta_corriente no existe")
            return False

        # Verificar columnas requeridas
        columnas_requeridas = [
            'id', 'proyecto_id', 'periodo_inicio', 'periodo_fin',
            'total_aridos', 'total_horas', 'importe_aridos', 'importe_horas',
            'importe_total', 'estado', 'fecha_generacion'
        ]

        columnas_existentes = [col['name'] for col in inspector.get_columns('reportes_cuenta_corriente')]
        columnas_faltantes = [col for col in columnas_requeridas if col not in columnas_existentes]

        if columnas_faltantes:
            logger.error(f"❌ Faltan columnas: {columnas_faltantes}")
            return False

        logger.info("✅ Verificación exitosa: Todas las columnas requeridas están presentes")
        return True

    except Exception as e:
        logger.error(f"❌ Error durante la verificación: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 MIGRACIÓN: Crear tabla reportes_cuenta_corriente")
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
            print("   2. Verificar endpoints en /docs:")
            print("      - GET /api/v1/cuenta-corriente/reportes")
            print("      - POST /api/v1/cuenta-corriente/reportes")
            print("      - GET /api/v1/cuenta-corriente/proyectos/{id}/resumen")
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
