#!/usr/bin/env python3
"""
Script de migración para agregar el campo horas_maquina a la tabla maquina
y crear la tabla mantenimiento
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Ejecuta la migración para agregar horas_maquina y crear tabla mantenimiento"""
    
    # Crear conexión a la base de datos
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # Iniciar transacción
            trans = connection.begin()
            
            try:
                # 1. Agregar columna horas_maquina a la tabla maquina si no existe
                print("Agregando columna horas_maquina a la tabla maquina...")
                connection.execute(text("""
                    ALTER TABLE maquina 
                    ADD COLUMN IF NOT EXISTS horas_maquina INTEGER DEFAULT 0
                """))
                
                # 2. Crear tabla mantenimiento
                print("Creando tabla mantenimiento...")
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS mantenimiento (
                        id SERIAL PRIMARY KEY,
                        maquina_id INTEGER NOT NULL REFERENCES maquina(id),
                        tipo_mantenimiento VARCHAR(50) NOT NULL,
                        descripcion TEXT NOT NULL,
                        fecha_mantenimiento TIMESTAMP WITH TIME ZONE NOT NULL,
                        horas_maquina INTEGER NOT NULL,
                        costo FLOAT,
                        responsable VARCHAR(100),
                        observaciones TEXT,
                        created TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated TIMESTAMP WITH TIME ZONE
                    )
                """))
                
                # 3. Crear índices para mejorar el rendimiento
                print("Creando índices...")
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_mantenimiento_maquina_id 
                    ON mantenimiento(maquina_id)
                """))
                
                connection.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_mantenimiento_fecha 
                    ON mantenimiento(fecha_mantenimiento)
                """))
                
                # Confirmar transacción
                trans.commit()
                print("✅ Migración completada exitosamente!")
                
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
    print("🚀 Iniciando migración...")
    success = run_migration()
    if success:
        print("🎉 Migración finalizada correctamente!")
    else:
        print("💥 La migración falló!")
        sys.exit(1)
