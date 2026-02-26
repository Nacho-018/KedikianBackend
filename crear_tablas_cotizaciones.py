"""
Script para crear las tablas de Cliente, Cotizacion y CotizacionItem
Ejecutar desde la raíz del proyecto: python3 crear_tablas_cotizaciones.py
"""
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
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_migration()
