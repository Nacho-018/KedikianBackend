"""
Script de migración para agregar columna observaciones a la tabla entrega_arido
Ejecutar: python migrate_add_observaciones_aridos.py
"""

import sys
import os

# Agregar el directorio raíz al path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine, SessionLocal
from sqlalchemy import text, inspect

def migrar_observaciones_aridos():
    """Agrega la columna observaciones a la tabla entrega_arido"""

    db = SessionLocal()

    try:
        print("🔄 Iniciando migración de observaciones en entrega_arido...")

        # Verificar si la tabla existe
        inspector = inspect(engine)
        tabla_existe = 'entrega_arido' in inspector.get_table_names()

        if not tabla_existe:
            print("❌ La tabla entrega_arido no existe. Por favor, crea la tabla primero.")
            return

        # Obtener columnas existentes
        columnas = [col['name'] for col in inspector.get_columns('entrega_arido')]

        # Verificar y agregar observaciones si no existe
        if 'observaciones' not in columnas:
            print("📝 Agregando columna observaciones...")
            db.execute(text("""
                ALTER TABLE entrega_arido
                ADD COLUMN observaciones VARCHAR(255) NULL
            """))
            db.commit()
            print("✅ Columna observaciones agregada exitosamente")
        else:
            print("✅ La columna observaciones ya existe")

        print("🎉 Migración completada exitosamente")

    except Exception as e:
        print(f"❌ Error durante la migración: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    migrar_observaciones_aridos()
