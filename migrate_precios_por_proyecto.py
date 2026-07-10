"""
Migración: tablas precio_arido_proyecto y tarifa_maquina_proyecto.
Guardan precios/tarifas configurados por proyecto para reemplazar los diccionarios
hardcodeados PRECIOS_ARIDOS y TARIFAS_MAQUINAS del servicio cuenta_corriente.

Ejecutar: python migrate_precios_por_proyecto.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import engine, SessionLocal
from sqlalchemy import text, inspect


def crear_precio_arido_proyecto(db, inspector):
    if 'precio_arido_proyecto' in inspector.get_table_names():
        print("📋 precio_arido_proyecto ya existe, saltando.")
        return
    print("📝 Creando precio_arido_proyecto...")
    db.execute(text("""
        CREATE TABLE precio_arido_proyecto (
            id SERIAL PRIMARY KEY,
            proyecto_id INTEGER NOT NULL REFERENCES proyecto(id) ON DELETE CASCADE,
            tipo_arido VARCHAR(100) NOT NULL,
            precio_unitario NUMERIC(14, 2) NOT NULL,
            created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated TIMESTAMP WITH TIME ZONE,
            CONSTRAINT uq_precio_arido_proyecto UNIQUE (proyecto_id, tipo_arido)
        )
    """))
    db.commit()
    print("✅ precio_arido_proyecto creada")


def crear_tarifa_maquina_proyecto(db, inspector):
    if 'tarifa_maquina_proyecto' in inspector.get_table_names():
        print("📋 tarifa_maquina_proyecto ya existe, saltando.")
        return
    print("📝 Creando tarifa_maquina_proyecto...")
    db.execute(text("""
        CREATE TABLE tarifa_maquina_proyecto (
            id SERIAL PRIMARY KEY,
            proyecto_id INTEGER NOT NULL REFERENCES proyecto(id) ON DELETE CASCADE,
            maquina_id INTEGER NOT NULL REFERENCES maquina(id) ON DELETE CASCADE,
            tarifa_hora NUMERIC(14, 2) NOT NULL,
            created TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated TIMESTAMP WITH TIME ZONE,
            CONSTRAINT uq_tarifa_maquina_proyecto UNIQUE (proyecto_id, maquina_id)
        )
    """))
    db.commit()
    print("✅ tarifa_maquina_proyecto creada")


def migrar():
    db = SessionLocal()
    try:
        print("🔄 Iniciando migración de precios por proyecto...")
        inspector = inspect(engine)
        crear_precio_arido_proyecto(db, inspector)
        crear_tarifa_maquina_proyecto(db, inspector)
        print("🎉 Migración completada")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrar()
