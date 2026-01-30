#!/usr/bin/env python3
"""
Script simple para ejecutar la migración que agrega el campo 'pagado'
a las tablas entrega_arido y reporte_laboral
(No requiere importar módulos de la app)
"""
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import os

def leer_env():
    """Lee el archivo .env y retorna DATABASE_URL"""
    env_file = Path(__file__).parent / ".env"

    if not env_file.exists():
        print(f"❌ No se encontró el archivo .env en: {env_file}")
        return None

    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('DATABASE_URL='):
                return line.split('=', 1)[1]

    return None

def ejecutar_migracion():
    """Ejecuta el archivo SQL de migración"""

    # Leer DATABASE_URL del .env
    database_url = leer_env()

    if not database_url:
        print("❌ No se pudo leer DATABASE_URL del archivo .env")
        return False

    # Leer el archivo SQL
    sql_file = Path(__file__).parent / "migrations" / "add_pagado_field.sql"

    if not sql_file.exists():
        print(f"❌ No se encontró el archivo: {sql_file}")
        return False

    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Ejecutar el SQL
    try:
        engine = create_engine(database_url)
        print(f"📊 Conectando a: {database_url.split('@')[-1] if '@' in database_url else database_url}")

        with engine.begin() as conn:
            # Dividir por statement (punto y coma) y filtrar comentarios y líneas vacías
            lines = sql_content.split('\n')
            clean_lines = [line for line in lines if line.strip() and not line.strip().startswith('--')]
            clean_sql = '\n'.join(clean_lines)

            statements = [s.strip() for s in clean_sql.split(';') if s.strip()]

            print(f"📋 Se encontraron {len(statements)} statements para ejecutar\n")

            for i, statement in enumerate(statements, 1):
                if statement:
                    # Mostrar primeras palabras del statement
                    preview = ' '.join(statement.split()[:5]) + '...'
                    print(f"🔄 Ejecutando statement {i}/{len(statements)}: {preview}")
                    conn.execute(text(statement))
                    print(f"   ✓ Completado\n")

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
