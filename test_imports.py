"""
Script para verificar que todos los componentes de pagos se pueden importar
"""
import sys

print("=" * 60)
print("VERIFICACIÓN DE IMPORTS")
print("=" * 60)

try:
    print("\n1. Importando modelo PagoReporte...")
    from app.db.models.pago_reporte import PagoReporte
    print("   ✅ PagoReporte importado")
    print(f"   Tabla: {PagoReporte.__tablename__}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

try:
    print("\n2. Importando schemas...")
    from app.schemas.schemas import PagoReporteCreate, PagoReporteOut, RegistrarPagoResponse
    print("   ✅ PagoReporteCreate importado")
    print("   ✅ PagoReporteOut importado")
    print("   ✅ RegistrarPagoResponse importado")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

try:
    print("\n3. Importando service...")
    from app.services.cuenta_corriente_service import registrar_pago, listar_pagos_reporte
    print("   ✅ registrar_pago importado")
    print("   ✅ listar_pagos_reporte importado")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

try:
    print("\n4. Importando router...")
    from app.routers.cuenta_corriente_router import router
    print("   ✅ Router importado")
    print(f"   Prefix: {router.prefix}")

    # Buscar rutas de pagos
    rutas_pagos = [r for r in router.routes if hasattr(r, 'path') and 'pagos' in r.path]
    print(f"   Rutas de pagos encontradas: {len(rutas_pagos)}")
    for ruta in rutas_pagos:
        metodos = getattr(ruta, 'methods', set())
        print(f"     - {list(metodos)} {ruta.path}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n5. Verificando main.py...")
    from main import app
    print("   ✅ App importada")

    # Buscar rutas de pagos en la app
    rutas_app = []
    for route in app.routes:
        if hasattr(route, 'path') and 'pagos' in route.path and 'reportes' in route.path:
            metodos = getattr(route, 'methods', set())
            rutas_app.append(f"{list(metodos)} {route.path}")

    print(f"   Rutas de pagos en app: {len(rutas_app)}")
    for ruta in rutas_app:
        print(f"     - {ruta}")

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ TODAS LAS VERIFICACIONES PASARON")
print("=" * 60)
print("\nRutas esperadas:")
print("  POST /api/v1/cuenta-corriente/reportes/{reporte_id}/pagos")
print("  GET  /api/v1/cuenta-corriente/reportes/{reporte_id}/pagos")
print("\nSi los endpoints aún dan 404, verifica:")
print("  1. Que el código está deployado en el servidor")
print("  2. Que el servidor se reinició después del deploy")
print("  3. Que la tabla 'pagos_reportes' existe en la base de datos")
print("=" * 60)
