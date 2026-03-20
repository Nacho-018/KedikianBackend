"""
Script para generar claves secretas seguras
Ejecutar: python generate_secrets.py
"""

import secrets


def generate_secret_key(length=32):
    """Genera una clave secreta hexadecimal"""
    return secrets.token_hex(length)


def main():
    print("\n" + "="*60)
    print("🔐 GENERADOR DE CLAVES SECRETAS - Kedikian API")
    print("="*60)

    print("\n📝 Claves generadas (copiar a .env):\n")

    # Generar JWT_SECRET_KEY
    jwt_secret = generate_secret_key(32)
    print(f"JWT_SECRET_KEY={jwt_secret}")

    # Generar EXTERNAL_SHARED_SECRET
    external_secret = generate_secret_key(24)
    print(f"EXTERNAL_SHARED_SECRET={external_secret}")

    print("\n" + "="*60)
    print("⚠️  IMPORTANTE:")
    print("   1. Copiar estas claves al archivo .env")
    print("   2. NUNCA compartir JWT_SECRET_KEY")
    print("   3. Compartir EXTERNAL_SHARED_SECRET solo con sistemas autorizados")
    print("   4. Reiniciar el servidor después de cambiar las claves")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
