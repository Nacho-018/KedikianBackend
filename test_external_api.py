"""
Script de prueba para la API Externa de Kedikian
Ejecutar: python test_external_api.py
"""

import asyncio
import sys
from app.services.external_client import KedikianClient


async def test_authentication():
    """Prueba de autenticación"""
    print("\n" + "="*60)
    print("🔐 PRUEBA 1: Autenticación")
    print("="*60)

    try:
        client = await KedikianClient.authenticate(
            base_url="http://localhost:8000",
            system_name="terrasoftarg",
            shared_secret="terrasoft_kedikian_shared_secret_2025"
        )
        print("✅ Autenticación exitosa")
        await client.close()
        return True
    except Exception as e:
        print(f"❌ Error en autenticación: {e}")
        return False


async def test_get_all_resources():
    """Prueba de obtención de todos los recursos"""
    print("\n" + "="*60)
    print("📋 PRUEBA 2: Obtener todos los recursos")
    print("="*60)

    async with await KedikianClient.authenticate(
        base_url="http://localhost:8000",
        system_name="terrasoftarg",
        shared_secret="terrasoft_kedikian_shared_secret_2025"
    ) as client:

        recursos = ["maquinas", "proyectos", "contratos"]

        for recurso in recursos:
            try:
                response = await client.get(recurso)
                total = response.get("total", 0)
                print(f"✅ {recurso}: {total} registros encontrados")
            except Exception as e:
                print(f"❌ Error obteniendo {recurso}: {e}")


async def test_get_one_resource():
    """Prueba de obtención de un recurso específico"""
    print("\n" + "="*60)
    print("🔍 PRUEBA 3: Obtener recurso específico")
    print("="*60)

    async with await KedikianClient.authenticate(
        base_url="http://localhost:8000",
        system_name="terrasoftarg",
        shared_secret="terrasoft_kedikian_shared_secret_2025"
    ) as client:

        try:
            # Primero obtener todas las máquinas
            response = await client.get("maquinas")

            if response["total"] > 0:
                # Obtener el ID de la primera máquina
                primer_id = response["data"][0]["id"]

                # Obtener esa máquina específica
                response_one = await client.get("maquinas", id=primer_id)
                print(f"✅ Máquina ID {primer_id} obtenida exitosamente")
                print(f"   Nombre: {response_one['data'].get('nombre', 'N/A')}")
            else:
                print("⚠️  No hay máquinas en la base de datos para probar")

        except Exception as e:
            print(f"❌ Error obteniendo recurso específico: {e}")


async def test_create_resource():
    """Prueba de creación de recurso (comentado por seguridad)"""
    print("\n" + "="*60)
    print("➕ PRUEBA 4: Crear recurso (DESACTIVADA)")
    print("="*60)
    print("⚠️  Prueba de creación desactivada para no modificar la BD")
    print("   Para activarla, descomentar el código en test_external_api.py")

    # Descomentar para probar creación (CUIDADO: modifica la BD)
    """
    async with await KedikianClient.authenticate(
        base_url="http://localhost:8000",
        system_name="terrasoftarg",
        shared_secret="terrasoft_kedikian_shared_secret_2025"
    ) as client:

        try:
            response = await client.post("maquinas", {
                "nombre": "Máquina de Prueba API",
                "tipo": "Test",
                "modelo": "TEST-001",
                "horometro_inicial": 0
            })
            print(f"✅ Máquina creada exitosamente")
            print(f"   ID: {response['data']['id']}")
            print(f"   Nombre: {response['data']['nombre']}")
        except Exception as e:
            print(f"❌ Error creando recurso: {e}")
    """


async def test_invalid_token():
    """Prueba de token inválido"""
    print("\n" + "="*60)
    print("🚫 PRUEBA 5: Token inválido (esperado fallo)")
    print("="*60)

    client = KedikianClient(
        base_url="http://localhost:8000",
        token="token_invalido_para_prueba"
    )

    try:
        await client.get("maquinas")
        print("❌ ERROR: El token inválido debería fallar")
    except Exception as e:
        print(f"✅ Fallo esperado con token inválido: {type(e).__name__}")
    finally:
        await client.close()


async def test_invalid_resource():
    """Prueba de recurso no soportado"""
    print("\n" + "="*60)
    print("❓ PRUEBA 6: Recurso no soportado (esperado fallo)")
    print("="*60)

    async with await KedikianClient.authenticate(
        base_url="http://localhost:8000",
        system_name="terrasoftarg",
        shared_secret="terrasoft_kedikian_shared_secret_2025"
    ) as client:

        try:
            await client.get("recurso_inexistente")
            print("❌ ERROR: El recurso inexistente debería fallar")
        except Exception as e:
            print(f"✅ Fallo esperado con recurso inexistente: {type(e).__name__}")


async def main():
    """Ejecuta todas las pruebas"""
    print("\n" + "="*60)
    print("🚀 TEST SUITE - API EXTERNA KEDIKIAN")
    print("="*60)
    print("\nAsegúrate de que el servidor esté corriendo en http://localhost:8000")
    print("Comando: uvicorn main:app --reload")

    # Ejecutar pruebas
    tests = [
        test_authentication,
        test_get_all_resources,
        test_get_one_resource,
        test_create_resource,
        test_invalid_token,
        test_invalid_resource
    ]

    for test in tests:
        try:
            await test()
        except Exception as e:
            print(f"\n❌ Error inesperado en {test.__name__}: {e}")

    print("\n" + "="*60)
    print("✅ TODAS LAS PRUEBAS COMPLETADAS")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Pruebas interrumpidas por el usuario")
        sys.exit(0)
