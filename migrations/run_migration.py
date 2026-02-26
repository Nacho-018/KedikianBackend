"""
Script para crear las tablas de Cliente, Cotizacion y CotizacionItem
usando SQLAlchemy directamente.
"""
import sys
import os

# Agregar el directorio raíz al path para poder importar los módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import engine, Base
from app.db.models import Cliente, Cotizacion, CotizacionItem

def run_migration():
    """Crea las tablas de cotizaciones en la base de datos"""
    try:
        print("🚀 Iniciando migración de tablas de Cotizaciones...")
        print(f"📊 Conectando a la base de datos...")

        # Crear las tablas
        # Esto solo crea las tablas que no existen, no sobrescribe las existentes
        Base.metadata.create_all(bind=engine)

        print("✅ Migración completada exitosamente!")
        print("\n📋 Tablas creadas:")
        print("   - cliente")
        print("   - cotizacion")
        print("   - cotizacion_item")
        print("\n🎉 El módulo de Cotizaciones está listo para usar!")

    except Exception as e:
        print(f"❌ Error durante la migración: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()
