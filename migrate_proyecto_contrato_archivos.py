#!/usr/bin/env python3
"""
Script de migración para actualizar el modelo Proyecto y agregar ContratoArchivo
Ejecutar con: python migrate_proyecto_contrato_archivos.py
"""

import sqlite3
import os
from pathlib import Path

def run_migration():
    """Ejecuta la migración para actualizar proyecto y agregar contrato_archivos"""
    
    # Ruta a la base de datos
    db_path = "app/db/database.db"  # Ajustar según tu configuración
    
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return False
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Iniciando migración...")
        
        # 1. Verificar si la columna contrato_file_path ya existe
        cursor.execute("PRAGMA table_info(proyecto)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'contrato_file_path' not in columns:
            print("📝 Agregando columna contrato_file_path a tabla proyecto...")
            cursor.execute("ALTER TABLE proyecto ADD COLUMN contrato_file_path VARCHAR(500) NULL")
        else:
            print("✅ Columna contrato_file_path ya existe en proyecto")
        
        # 2. Verificar si la tabla contrato_archivos ya existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contrato_archivos'")
        if not cursor.fetchone():
            print("📝 Creando tabla contrato_archivos...")
            cursor.execute("""
                CREATE TABLE contrato_archivos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proyecto_id INTEGER NOT NULL,
                    nombre_archivo VARCHAR(255) NOT NULL,
                    ruta_archivo VARCHAR(500) NOT NULL,
                    tipo_archivo VARCHAR(50) NOT NULL,
                    tamaño_archivo BIGINT NOT NULL,
                    fecha_subida DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (proyecto_id) REFERENCES proyecto(id)
                )
            """)
            
            # Crear índices
            print("📝 Creando índices...")
            cursor.execute("CREATE INDEX idx_contrato_archivos_proyecto_id ON contrato_archivos(proyecto_id)")
            cursor.execute("CREATE INDEX idx_contrato_archivos_fecha_subida ON contrato_archivos(fecha_subida)")
        else:
            print("✅ Tabla contrato_archivos ya existe")
        
        # 3. Crear directorio de uploads si no existe
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        print(f"📁 Directorio uploads creado/verificado: {upload_dir.absolute()}")
        
        # Confirmar cambios
        conn.commit()
        print("✅ Migración completada exitosamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Ejecutando migración de proyecto y contrato_archivos...")
    success = run_migration()
    
    if success:
        print("🎉 ¡Migración completada exitosamente!")
    else:
        print("💥 Error en la migración")
        exit(1)
