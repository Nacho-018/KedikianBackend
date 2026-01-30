#!/usr/bin/env python3
"""
Script para ejecutar la migración que agrega el campo 'pagado'
a las tablas entrega_arido y reporte_laboral
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def ejecutar_migracion():
    """Ejecuta el archivo SQL de migración"""

    # Leer el archivo SQL
    sql_file = Path(__file__).parent / "migrations" / "add_pagado_field.sql"

    if not sql_file.exists():
        print(f"❌ No se encontró el archivo: {sql_file}")
        return False

    with open(sql_file, 'r', encoding='utf-8') as f:
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
        print("   - Campo 'pagado' agregado a tabla 'entrega_arido'")
        print("   - Campo 'pagado' agregado a tabla 'reporte_laboral'")

        # Verificar que los campos se agregaron correctamente
        print("\n🔍 Verificando campos agregados...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns
                WHERE table_name = 'entrega_arido' AND column_name = 'pagado';
            """)).fetchone()

            if result:
                print(f"   ✓ entrega_arido.pagado: {result[1]} (default: {result[2]})")
            else:
                print("   ⚠️  No se pudo verificar entrega_arido.pagado")

            result = conn.execute(text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns
                WHERE table_name = 'reporte_laboral' AND column_name = 'pagado';
            """)).fetchone()

            if result:
                print(f"   ✓ reporte_laboral.pagado: {result[1]} (default: {result[2]})")
            else:
                print("   ⚠️  No se pudo verificar reporte_laboral.pagado")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 Ejecutando migración: Agregar campo 'pagado'")
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
        print("   2. Probar el nuevo endpoint en /docs:")
        print("      GET /cuenta-corriente/reportes/{id}/detalle")
        print()
        sys.exit(0)
    else:
        print()
        print("💥 La migración falló")
        print()
        sys.exit(1)
