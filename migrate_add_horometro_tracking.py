#!/usr/bin/env python3
"""
Script de migración para:
1. Agregar campo proximo_mantenimiento a la tabla maquina
2. Crear tabla horometro_historial para auditoría de cambios del horómetro
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Ejecuta la migración para tracking de horómetro"""

    # Crear conexión a la base de datos
    engine = create_engine(settings.DATABASE_URL)

    try:
        with engine.connect() as connection:
            # Iniciar transacción
            trans = connection.begin()

            try:
                # 1. Agregar columna proximo_mantenimiento a la tabla maquina
                print("Agregando columna proximo_mantenimiento a la tabla maquina...")
                connection.execute(text("""
                    ALTER TABLE maquina
                    ADD COLUMN IF NOT EXISTS proximo_mantenimiento FLOAT DEFAULT NULL
                """))

                # 2. Crear tabla horometro_historial para auditoría
                print("Creando tabla horometro_historial...")
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS horometro_historial (
                        id SERIAL PRIMARY KEY,
                        maquina_id INTEGER NOT NULL REFERENCES maquina(id) ON DELETE CASCADE,
                        valor_anterior FLOAT NOT NULL,
                        valor_nuevo FLOAT NOT NULL,
                        usuario_id INTEGER REFERENCES usuario(id),
                        motivo VARCHAR(255) NOT NULL,
                        reporte_laboral_id INTEGER REFERENCES reporte_laboral(id),
                        created TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated TIMESTAMP WITH TIME ZONE
                    )
                """))

                # 3. Crear índices para mejorar el rendimiento
                print("Creando índices...")
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_horometro_historial_maquina_id
                    ON horometro_historial(maquina_id)
                """))

                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_horometro_historial_usuario_id
                    ON horometro_historial(usuario_id)
                """))

                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_horometro_historial_reporte_id
                    ON horometro_historial(reporte_laboral_id)
                """))

                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_horometro_historial_created
                    ON horometro_historial(created)
                """))

                # Confirmar transacción
                trans.commit()
                print("✅ Migración completada exitosamente!")
                print("\n📋 Cambios aplicados:")
                print("   - Campo 'proximo_mantenimiento' agregado a tabla 'maquina'")
                print("   - Tabla 'horometro_historial' creada para auditoría")
                print("   - Índices creados para optimizar consultas")

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
    print("🚀 Iniciando migración de tracking de horómetro...")
    print("=" * 60)
    success = run_migration()
    print("=" * 60)
    if success:
        print("🎉 Migración finalizada correctamente!")
        print("\n💡 Próximos pasos:")
        print("   1. Configurar 'proximo_mantenimiento' en cada máquina")
        print("   2. Los cambios del horómetro se registrarán automáticamente")
    else:
        print("💥 La migración falló!")
        sys.exit(1)
