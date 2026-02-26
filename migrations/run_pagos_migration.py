"""
Script para ejecutar la migración de la tabla pagos_reportes
"""
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path para poder importar módulos de la app
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy import text
from app.db.database import engine

def run_migration():
    """Ejecuta el script SQL de migración para crear la tabla pagos_reportes"""
    migration_file = Path(__file__).parent / "create_pagos_reportes.sql"

    if not migration_file.exists():
        print(f"❌ Error: No se encontró el archivo {migration_file}")
        return False

    print(f"📄 Leyendo migración desde: {migration_file}")

    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    try:
        print("🔄 Ejecutando migración...")
        with engine.begin() as connection:
            connection.execute(text(sql_script))

        print("✅ Migración ejecutada exitosamente")
        print("✅ Tabla 'pagos_reportes' creada con éxito")
        return True

    except Exception as e:
        print(f"❌ Error al ejecutar la migración: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("MIGRACIÓN: Crear tabla pagos_reportes")
    print("=" * 60)

    success = run_migration()

    print("=" * 60)
    if success:
        print("✅ Proceso completado exitosamente")
    else:
        print("❌ Proceso completado con errores")
    print("=" * 60)

    sys.exit(0 if success else 1)
