"""
Script de migración para crear/actualizar la tabla configuracion_tarifas
Ejecutar: python migrate_configuracion_tarifas.py
"""

import sys
import os

# Agregar el directorio raíz al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine, SessionLocal
from sqlalchemy import text, inspect

def migrar_configuracion_tarifas():
    """Crea o actualiza la tabla configuracion_tarifas"""

    db = SessionLocal()

    try:
        print("🔄 Iniciando migración de configuracion_tarifas...")

        # Verificar si la tabla existe
        inspector = inspect(engine)
        tabla_existe = 'configuracion_tarifas' in inspector.get_table_names()

        if not tabla_existe:
            print("📝 Creando tabla configuracion_tarifas...")

            # Crear tabla completa (sin valores default, el admin debe ingresarlos)
            db.execute(text("""
                CREATE TABLE configuracion_tarifas (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    hora_normal DECIMAL(10, 2) NOT NULL,
                    hora_feriado DECIMAL(10, 2) NOT NULL,
                    hora_extra DECIMAL(10, 2) NOT NULL,
                    multiplicador_extra DECIMAL(5, 2) NOT NULL,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """))

            db.commit()
            print("✅ Tabla configuracion_tarifas creada exitosamente")
            print("⚠️  IMPORTANTE: El administrador debe configurar las tarifas usando el endpoint POST /v1/excel/configuracion-tarifas")

        else:
            print("📋 La tabla configuracion_tarifas ya existe, verificando columnas...")

            # Obtener columnas existentes
            columnas = [col['name'] for col in inspector.get_columns('configuracion_tarifas')]

            # Verificar y agregar hora_extra si no existe
            if 'hora_extra' not in columnas:
                print("📝 Agregando columna hora_extra...")
                db.execute(text("""
                    ALTER TABLE configuracion_tarifas
                    ADD COLUMN hora_extra DECIMAL(10, 2) NOT NULL DEFAULT 9750
                """))
                db.commit()
                print("✅ Columna hora_extra agregada")

            # Verificar y agregar multiplicador_extra si no existe
            if 'multiplicador_extra' not in columnas:
                print("📝 Agregando columna multiplicador_extra...")
                db.execute(text("""
                    ALTER TABLE configuracion_tarifas
                    ADD COLUMN multiplicador_extra DECIMAL(5, 2) NOT NULL DEFAULT 1.5
                """))
                db.commit()
                print("✅ Columna multiplicador_extra agregada")

            # Eliminar columnas antiguas si existen
            if 'activo' in columnas:
                print("🗑️  Eliminando columna obsoleta 'activo'...")
                db.execute(text("""
                    ALTER TABLE configuracion_tarifas
                    DROP COLUMN activo
                """))
                db.commit()
                print("✅ Columna activo eliminada")

            if 'created' in columnas:
                print("🗑️  Eliminando columna obsoleta 'created'...")
                db.execute(text("""
                    ALTER TABLE configuracion_tarifas
                    DROP COLUMN created
                """))
                db.commit()
                print("✅ Columna created eliminada")

            if 'updated' in columnas:
                print("🗑️  Eliminando columna obsoleta 'updated'...")
                db.execute(text("""
                    ALTER TABLE configuracion_tarifas
                    DROP COLUMN updated
                """))
                db.commit()
                print("✅ Columna updated eliminada")

            # Agregar fecha_actualizacion si no existe
            if 'fecha_actualizacion' not in columnas:
                print("📝 Agregando columna fecha_actualizacion...")
                db.execute(text("""
                    ALTER TABLE configuracion_tarifas
                    ADD COLUMN fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                """))
                db.commit()
                print("✅ Columna fecha_actualizacion agregada")

            print("✅ Tabla configuracion_tarifas actualizada correctamente")

            # Verificar si existe configuración
            resultado = db.execute(text("SELECT COUNT(*) as count FROM configuracion_tarifas")).fetchone()
            if resultado.count == 0:
                print("⚠️  No hay configuración de tarifas. El administrador debe configurarlas usando el endpoint POST /v1/excel/configuracion-tarifas")

        print("🎉 Migración completada exitosamente")

    except Exception as e:
        print(f"❌ Error durante la migración: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    migrar_configuracion_tarifas()
