#!/usr/bin/env python3
"""
Script de migración para:
1. Crear tabla notas_maquinas para almacenar notas asociadas a máquinas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Ejecuta la migración para crear tabla de notas de máquinas"""

    # Crear conexión a la base de datos
    engine = create_engine(settings.DATABASE_URL)

    try:
        with engine.connect() as connection:
            # Iniciar transacción
            trans = connection.begin()

            try:
                # 1. Crear tabla notas_maquinas
                print("Creando tabla notas_maquinas...")
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS notas_maquinas (
                        id SERIAL PRIMARY KEY,
                        maquina_id INTEGER NOT NULL REFERENCES maquina(id) ON DELETE CASCADE,
                        texto TEXT NOT NULL,
                        usuario VARCHAR(100) DEFAULT 'Usuario',
                        fecha TIMESTAMP WITH TIME ZONE NOT NULL,
                        created TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated TIMESTAMP WITH TIME ZONE
                    )
                """))

                # 2. Crear índices para mejorar el rendimiento
                print("Creando índices...")
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_notas_maquina_id
                    ON notas_maquinas(maquina_id)
                """))

                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_notas_fecha
                    ON notas_maquinas(fecha)
                """))

                # Confirmar transacción
                trans.commit()
                print("✅ Migración completada exitosamente!")
                print("\n📋 Cambios aplicados:")
                print("   - Tabla 'notas_maquinas' creada")
                print("   - Índices creados para optimizar consultas")
                print("   - Relación con tabla 'maquina' configurada (CASCADE DELETE)")

            except Exception as e:
                # Revertir transacción en caso de error
                trans.rollback()
                print(f"❌ Error durante la migración: {e}")
                raise

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

    return True

if __name__ == "__main__":
    print("🚀 Iniciando migración de notas de máquinas...")
    print("=" * 60)
    success = run_migration()
    print("=" * 60)
    if success:
        print("🎉 Migración finalizada correctamente!")
        print("\n💡 Próximos pasos:")
        print("   1. Las notas se pueden crear desde los endpoints:")
        print("      - GET  /api/v1/maquinas/{maquina_id}/notas")
        print("      - POST /api/v1/maquinas/{maquina_id}/notas")
        print("      - DELETE /api/v1/maquinas/notas/{nota_id}")
        print("   2. Endpoint de próximo mantenimiento disponible:")
        print("      - PUT /api/v1/maquinas/{maquina_id}/proximo-mantenimiento")
    else:
        print("💥 La migración falló!")
        sys.exit(1)
