#!/usr/bin/env python3
"""
Script para probar la funcionalidad del CRM
"""
import requests
from requests.sessions import Session

BASE_URL = "http://127.0.0.1:5000"

def test_pages():
    """Prueba que las páginas principales cargan correctamente"""
    print("🔍 Probando páginas...")

    # Test login page
    response = requests.get(f"{BASE_URL}/login")
    print(f"✓ Página de login: {response.status_code} OK" if response.status_code == 200 else f"✗ Login falló: {response.status_code}")

    # Test register page
    response = requests.get(f"{BASE_URL}/register")
    print(f"✓ Página de registro: {response.status_code} OK" if response.status_code == 200 else f"✗ Registro falló: {response.status_code}")

    return True

def test_registration():
    """Prueba el registro de un nuevo usuario"""
    print("\n📝 Probando registro de usuario...")

    session = Session()

    # Get the register page first to get any CSRF tokens if needed
    response = session.get(f"{BASE_URL}/register")

    # Try to register a new user
    data = {
        'username': 'demouser',
        'email': 'demo@cococrm.com',
        'password': 'demo123',
        'confirm_password': 'demo123'
    }

    response = session.post(f"{BASE_URL}/register", data=data, allow_redirects=False)

    if response.status_code == 302:  # Redirect after successful registration
        print("✓ Usuario registrado exitosamente")
        print(f"  Redirigiendo a: {response.headers.get('Location')}")
        return session
    else:
        print(f"✗ Registro falló con código: {response.status_code}")
        if 'already exists' in response.text:
            print("  (El usuario ya existe, esto es normal en pruebas repetidas)")
        return None

def test_login(session=None):
    """Prueba el inicio de sesión"""
    print("\n🔐 Probando inicio de sesión...")

    if session is None:
        session = Session()

    data = {
        'username': 'demouser',
        'password': 'demo123'
    }

    response = session.post(f"{BASE_URL}/login", data=data, allow_redirects=False)

    if response.status_code == 302:
        print("✓ Login exitoso")
        print(f"  Redirigiendo a: {response.headers.get('Location')}")
        return session
    else:
        print(f"✗ Login falló con código: {response.status_code}")
        return None

def test_dashboard(session):
    """Prueba el acceso al dashboard"""
    print("\n📊 Probando acceso al dashboard...")

    response = session.get(f"{BASE_URL}/dashboard", allow_redirects=False)

    if response.status_code == 200:
        print("✓ Dashboard accesible")
        if 'Welcome back' in response.text or 'demouser' in response.text:
            print("✓ Dashboard muestra información del usuario")
        return True
    elif response.status_code == 302:
        print("✗ Redirigido (no autenticado)")
        return False
    else:
        print(f"✗ Error al acceder al dashboard: {response.status_code}")
        return False

def main():
    print("=" * 60)
    print("🧪 PRUEBA DE FUNCIONALIDAD - CocoCRM")
    print("=" * 60)

    # Test 1: Pages load
    test_pages()

    # Test 2: User registration
    session = test_registration()

    # Test 3: User login (use existing session or create new one)
    if session is None:
        session = test_login()

    # Test 4: Dashboard access
    if session:
        test_dashboard(session)

    print("\n" + "=" * 60)
    print("✨ Pruebas completadas!")
    print("=" * 60)
    print("\n💡 Para usar la aplicación:")
    print(f"   1. Abre tu navegador en: {BASE_URL}")
    print("   2. Crea una cuenta o usa: usuario='demouser', password='demo123'")
    print("   3. ¡Disfruta del CRM!")
    print("\n🔧 Para configurar Telegram:")
    print("   1. Crea un bot con @BotFather en Telegram")
    print("   2. Copia el token a un archivo .env")
    print("   3. Ejecuta: /setdomain en BotFather")

if __name__ == "__main__":
    main()
