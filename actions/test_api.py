import requests
import json

# Tu URL de Render
API_BASE_URL = "https://api-ia-o027.onrender.com"

print("=" * 60)
print("🧪 PRUEBA DE CONEXIÓN CON LA API")
print("=" * 60)

# Test 1: Verificar que la API esté funcionando
print("\n1️⃣ Test de conexión básica...")
try:
    response = requests.get(f"{API_BASE_URL}/", timeout=60)
    print(f"   ✅ Status Code: {response.status_code}")
    print(f"   📄 Respuesta: {response.json()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Verificar endpoint de registro
print("\n2️⃣ Test de REGISTRO...")
try:
    test_user = "test_usuario_123"
    test_pass = "test_password_123"
    
    response = requests.post(
        f"{API_BASE_URL}/register",
        json={"usuario": test_user, "contraseña": test_pass},
        headers={"Content-Type": "application/json"},
        timeout=60
    )
    print(f"   ✅ Status Code: {response.status_code}")
    print(f"   📄 Respuesta: {response.json()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Verificar endpoint de login
print("\n3️⃣ Test de LOGIN...")
try:
    response = requests.post(
        f"{API_BASE_URL}/login",
        json={"usuario": test_user, "contraseña": test_pass},
        headers={"Content-Type": "application/json"},
        timeout=60
    )
    print(f"   ✅ Status Code: {response.status_code}")
    print(f"   📄 Respuesta: {response.json()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Login con credenciales incorrectas
print("\n4️⃣ Test de LOGIN INCORRECTO...")
try:
    response = requests.post(
        f"{API_BASE_URL}/login",
        json={"usuario": "usuario_falso", "contraseña": "pass_falso"},
        headers={"Content-Type": "application/json"},
        timeout=60
    )
    print(f"   ✅ Status Code: {response.status_code}")
    print(f"   📄 Respuesta: {response.json()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("🔍 DIAGNÓSTICO:")
print("=" * 60)
print("""
Si todos los tests funcionan aquí pero no en Rasa:
1. Verifica que el Action Server esté corriendo
2. Revisa que la URL en actions.py sea correcta
3. Reinicia el Action Server
4. Verifica los logs del Action Server con --debug
""")
print("=" * 60)