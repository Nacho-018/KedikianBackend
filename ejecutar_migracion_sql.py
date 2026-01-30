#!/usr/bin/env python3
"""
Script simple para ejecutar la migración SQL
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def ejecutar_migracion():
    """Ejecuta el archivo SQL de migración"""

    # Leer el archivo SQL
    sql_file = Path(__file__).parent / "migrations" / "add_precio_tarifa_fields.sql"

    if not sql_file.exists():
        print(f"❌ No se encontró el archivo: {sql_file}")
        return False

    with open(sql_file, 'r') as f:
        sql_content = f.read()

    # Ejecutar el SQL
    try:
        engine = create_engine(settings.DATABASE_URL)
        print(f"📊 Conectando a: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")

        with engine.connect() as conn:
            # Dividir por statement (punto y coma)
            statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

            for i, statement in enumerate(statements, 1):
                if statement:
                    print(f"🔄 Ejecutando statement {i}/{len(statements)}...")
                    conn.execute(text(statement))

            conn.commit()

        print("✅ Migración ejecutada exitosamente")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 Ejecutando migración SQL")
    print("=" * 80)
    print()

    success = ejecutar_migracion()

    if success:
        print()
        print("=" * 80)
        print("🎉 ¡Migración completada!")
        print("=" * 80)
        print()
        print("📋 Próximos pasos:")
        print("   1. Reiniciar el servidor FastAPI")
        print("   2. Probar los nuevos endpoints en /docs")
        print()
    else:
        print()
        print("💥 La migración falló")
        exit(1)
