"""
Backfill: poblar precio_arido_proyecto y tarifa_maquina_proyecto con los valores
que antes vivían hardcodeados en cuenta_corriente_service (PRECIOS_ARIDOS,
TARIFAS_MAQUINAS). Se insertan para todos los proyectos activos.

Idempotente: usa upsert. Registros existentes NO se pisan (respeta configuración
manual previa).

Ejecutar UNA VEZ después de migrate_precios_por_proyecto.py:
    ./venv/bin/python backfill_precios_por_proyecto.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.database import SessionLocal


# Snapshot de los defaults hardcodeados históricos.
PRECIOS_ARIDOS_HISTORICOS = {
    "Arena Fina": 54000.0,
    "Granza": 54000.0,
    "Arena Común": 33680.0,
    "Relleno": 16000.0,
    "Tierra Negra": 16000.0,
    "Piedra": 12000.0,
    "0.20": 8000.0,
    "Blinder": 10000.0,
    "Arena Lavada": 33680.0,
}

TARIFAS_MAQUINAS_HISTORICAS = {
    "BOBCAT 2018 S650.": 700000.0,
    "BOBCAT S530 2017": 700000.0,
    "EXCAVADORA 2020 SANY EU50.": 100000.0,
    "EXCAVADORA 2023 XCMG E60.": 100000.0,
    "EXCAVADORA 2022 LONKING 6150.": 150000.0,
    "EXCAVADORA 2015 LONKING 6150.": 150000.0,
    "PALA 2022 SINOMACH 933.": 100000.0,
}


def backfill():
    db = SessionLocal()
    insertados_aridos = 0
    insertados_maquinas = 0
    saltados_aridos = 0
    saltados_maquinas = 0
    try:
        proyecto_ids = [row[0] for row in db.execute(
            text("SELECT id FROM proyecto WHERE estado = true")
        ).fetchall()]
        print(f"🔍 Proyectos activos encontrados: {len(proyecto_ids)}")

        maquinas_rows = db.execute(text("SELECT id, nombre FROM maquina")).fetchall()
        maquinas_por_nombre = {row[1]: row[0] for row in maquinas_rows}
        print(f"🔍 Máquinas en BD: {len(maquinas_rows)}")

        for proyecto_id in proyecto_ids:
            for tipo_arido, precio in PRECIOS_ARIDOS_HISTORICOS.items():
                existente = db.execute(
                    text("SELECT id FROM precio_arido_proyecto WHERE proyecto_id = :p AND tipo_arido = :t"),
                    {"p": proyecto_id, "t": tipo_arido},
                ).fetchone()
                if existente:
                    saltados_aridos += 1
                    continue
                db.execute(
                    text("INSERT INTO precio_arido_proyecto (proyecto_id, tipo_arido, precio_unitario) VALUES (:p, :t, :pr)"),
                    {"p": proyecto_id, "t": tipo_arido, "pr": precio},
                )
                insertados_aridos += 1

            for nombre_maquina, tarifa in TARIFAS_MAQUINAS_HISTORICAS.items():
                maquina_id = maquinas_por_nombre.get(nombre_maquina)
                if not maquina_id:
                    print(f"⚠️  Máquina '{nombre_maquina}' no existe en BD, salteando en proyecto {proyecto_id}")
                    continue
                existente = db.execute(
                    text("SELECT id FROM tarifa_maquina_proyecto WHERE proyecto_id = :p AND maquina_id = :m"),
                    {"p": proyecto_id, "m": maquina_id},
                ).fetchone()
                if existente:
                    saltados_maquinas += 1
                    continue
                db.execute(
                    text("INSERT INTO tarifa_maquina_proyecto (proyecto_id, maquina_id, tarifa_hora) VALUES (:p, :m, :t)"),
                    {"p": proyecto_id, "m": maquina_id, "t": tarifa},
                )
                insertados_maquinas += 1

        db.commit()
        print("✅ Backfill completado")
        print(f"   Precios árido insertados: {insertados_aridos} (saltados por existentes: {saltados_aridos})")
        print(f"   Tarifas máquina insertadas: {insertados_maquinas} (saltadas por existentes: {saltados_maquinas})")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    backfill()
