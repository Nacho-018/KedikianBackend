import psycopg2
from dotenv import load_dotenv
import os
from urllib.parse import urlparse

# Cargar variables de entorno
load_dotenv()

# Obtener DATABASE_URL y parsear
database_url = os.getenv('DATABASE_URL')
if database_url:
    # Parsear DATABASE_URL (formato: postgresql+psycopg2://user:pass@host:port/dbname)
    url = urlparse(database_url)
    DB_CONFIG = {
        'host': url.hostname or 'localhost',
        'port': url.port or 5432,
        'database': url.path[1:],  # Remover el / inicial
        'user': url.username,
        'password': url.password
    }
else:
    # Fallback a variables individuales
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }

def ejecutar_migracion():
    """Ejecuta la migración para crear las tablas de items de reportes"""
    try:
        # Conectar a la base de datos
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("🔄 Ejecutando migración: add_reporte_items_tables.sql")

        # Leer y ejecutar el archivo SQL
        with open('migrations/add_reporte_items_tables.sql', 'r') as f:
            sql = f.read()
            cursor.execute(sql)

        # Commit de cambios
        conn.commit()

        print("✅ Migración ejecutada exitosamente")
        print("\nTablas creadas:")
        print("  - reporte_items_aridos")
        print("  - reporte_items_horas")

        # Verificar que las tablas se crearon
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name IN ('reporte_items_aridos', 'reporte_items_horas')
            ORDER BY table_name
        """)
        tablas = cursor.fetchall()

        print("\n📊 Tablas verificadas:")
        for tabla in tablas:
            print(f"  ✓ {tabla[0]}")

        # Cerrar conexión
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error al ejecutar la migración: {e}")
        raise

if __name__ == "__main__":
    ejecutar_migracion()
