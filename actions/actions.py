from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted, FollowupAction
import requests
import re
import random

# URL base de tu API Flask en Render
API_BASE_URL = "https://api-ia-o027.onrender.com"

class ActionSessionStart(Action):
    """Acción que se ejecuta al iniciar una nueva sesión"""

    def name(self) -> Text:
        return "action_session_start"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        # Obtener metadatos de la sesión si existen
        events = [SessionStarted()]

        # Verificar si el usuario ya está autenticado
        autenticado = tracker.get_slot("autenticado")
        
        if not autenticado:
            # Solicitar login inicial
            dispatcher.utter_message(response="utter_solicitar_login_inicial")
        
        # Mantener slots existentes si es una reconexión
        events.append(ActionExecuted("action_listen"))
        
        return events


class ActionLogin(Action):
    """Acción para realizar el login usando la API"""

    def name(self) -> Text:
        return "action_login"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Obtener las credenciales de los slots
        usuario = tracker.get_slot("usuario")
        contraseña = tracker.get_slot("contraseña")

        print(f"🔍 DEBUG - Slots: usuario='{usuario}', contraseña='{contraseña}'")

        # Si no hay credenciales, extraerlas del último mensaje
        if not usuario or not contraseña:
            ultimo_mensaje = tracker.latest_message.get('text', '')
            print(f"🔍 DEBUG - Mensaje del usuario: '{ultimo_mensaje}'")
            usuario, contraseña = self.extraer_credenciales(ultimo_mensaje)

        if not usuario or not contraseña:
            mensajes = [
                "❌ No pude obtener tus credenciales. Por favor, escribe en formato:\n\nusuario: tu_usuario, contraseña: tu_contraseña",
                "🔴 Ups, no encontré tus datos. Recuerda el formato:\n\nusuario: tu_usuario, contraseña: tu_contraseña",
                "⚠️ No pude leer tus credenciales. Asegúrate de usar el formato:\n\nusuario: tu_usuario, contraseña: tu_contraseña"
            ]
            dispatcher.utter_message(text=random.choice(mensajes))
            return []

        # Llamar a la API de login
        print(f"📡 DEBUG - Enviando petición a: {API_BASE_URL}/login")
        print(f"📡 DEBUG - Datos: usuario='{usuario}', contraseña='***'")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/login",
                json={"usuario": usuario, "contraseña": contraseña},
                timeout=60
            )
            
            print(f"📡 DEBUG - Status Code: {response.status_code}")
            print(f"📡 DEBUG - Respuesta: {response.json()}")

            if response.status_code == 200:
                data = response.json()
                id_usuario = data.get("id_usuario")
                
                # Mensajes variados de login exitoso
                mensajes_exitosos = [
                    f"✅ ¡Bienvenido de vuelta, {usuario}! Has iniciado sesión correctamente. 🎉",
                    f"🎊 ¡Hola {usuario}! Acceso concedido. ¡Qué bueno verte de nuevo!",
                    f"👋 ¡{usuario}! Login exitoso. ¡Listo para trabajar! ✨",
                    f"🔓 ¡Perfecto, {usuario}! Has ingresado al sistema correctamente. 🚀",
                    f"🌟 ¡{usuario} está en línea! Autenticación exitosa. 💯"
                ]
                
                dispatcher.utter_message(text=random.choice(mensajes_exitosos))
                
                # Enviar mensaje de bienvenida con información del bot
                dispatcher.utter_message(response="utter_bienvenida_post_login")
                
                return [
                    SlotSet("id_usuario", str(id_usuario)),
                    SlotSet("autenticado", True),
                    SlotSet("usuario", usuario),
                    SlotSet("contraseña", None)  # Limpiar contraseña por seguridad
                ]
            else:
                mensajes_fallidos = [
                    "❌ Usuario o contraseña incorrectos. Por favor, verifica tus datos e intenta de nuevo.",
                    "🔴 No pude autenticarte. Revisa que tu usuario y contraseña sean correctos.",
                    "⚠️ Credenciales inválidas. ¿Estás seguro de tus datos? Intenta nuevamente.",
                    "🚫 Login fallido. Verifica tu usuario y contraseña, por favor.",
                    "❗ No te pude identificar. Asegúrate de que tus credenciales sean correctas."
                ]
                dispatcher.utter_message(text=random.choice(mensajes_fallidos))
                return [SlotSet("autenticado", False), SlotSet("contraseña", None)]

        except requests.exceptions.RequestException as e:
            mensajes_error = [
                "🔴 Error al conectar con el servidor. Por favor, intenta más tarde.",
                "⚠️ No pude conectarme al sistema. Verifica tu conexión e intenta nuevamente.",
                "❌ Hubo un problema de conexión. Por favor, inténtalo en unos momentos.",
                "🔌 Error de comunicación con el servidor. Intenta de nuevo pronto.",
                "⚡ No hay respuesta del servidor. Por favor, espera un momento y reintenta."
            ]
            dispatcher.utter_message(text=random.choice(mensajes_error))
            print(f"Error en login: {e}")
            return [SlotSet("autenticado", False), SlotSet("contraseña", None)]

    def extraer_credenciales(self, texto: str) -> tuple:
        """Extrae usuario y contraseña del texto"""
        usuario = None
        contraseña = None

        # Limpiar el texto
        texto = texto.strip()
        
        print(f"🔍 DEBUG - Texto recibido: '{texto}'")

        # Intentar múltiples patrones
        patrones = [
            # Patrón 1: "usuario: xxx, contraseña: yyy"
            (r'usuario[:\s]+([^\s,]+).*contraseña[:\s]+([^\s,]+)', True),
            # Patrón 2: "usuario xxx contraseña yyy"
            (r'usuario\s+(\S+)\s+contraseña\s+(\S+)', True),
            # Patrón 3: "user: xxx pass: yyy"
            (r'user[:\s]+([^\s,]+).*pass[:\s]+([^\s,]+)', True),
            # Patrón 4: Solo dos palabras (asume usuario contraseña)
            (r'^(\S+)\s+(\S+)$', False)
        ]

        for patron, tiene_palabras_clave in patrones:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                if tiene_palabras_clave or (not usuario and not contraseña):
                    usuario = match.group(1)
                    contraseña = match.group(2)
                    print(f"✅ DEBUG - Extraído: usuario='{usuario}', contraseña='{contraseña}'")
                    break

        if not usuario or not contraseña:
            print(f"❌ DEBUG - No se pudo extraer credenciales del texto")

        return usuario, contraseña


class ActionRegistro(Action):
    """Acción para realizar el registro de un nuevo usuario"""

    def name(self) -> Text:
        return "action_registro"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Obtener las credenciales
        usuario = tracker.get_slot("usuario")
        contraseña = tracker.get_slot("contraseña")

        print(f"🔍 DEBUG REGISTRO - Slots: usuario='{usuario}', contraseña='{contraseña}'")

        # Si no hay credenciales, extraerlas del último mensaje
        if not usuario or not contraseña:
            ultimo_mensaje = tracker.latest_message.get('text', '')
            print(f"🔍 DEBUG REGISTRO - Mensaje del usuario: '{ultimo_mensaje}'")
            usuario, contraseña = self.extraer_credenciales(ultimo_mensaje)

        if not usuario or not contraseña:
            mensajes = [
                "❌ No pude obtener tus credenciales. Por favor, escribe en formato:\n\nusuario: tu_usuario, contraseña: tu_contraseña",
                "🔴 No encontré tus datos. Usa el formato:\n\nusuario: tu_usuario, contraseña: tu_contraseña",
                "⚠️ Necesito tus credenciales en este formato:\n\nusuario: tu_usuario, contraseña: tu_contraseña"
            ]
            dispatcher.utter_message(text=random.choice(mensajes))
            return []

        # Llamar a la API de registro
        print(f"📡 DEBUG REGISTRO - Enviando petición a: {API_BASE_URL}/register")
        print(f"📡 DEBUG REGISTRO - Datos: usuario='{usuario}', contraseña='***'")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/register",
                json={"usuario": usuario, "contraseña": contraseña},
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            print(f"📡 DEBUG REGISTRO - Status Code: {response.status_code}")
            print(f"📡 DEBUG REGISTRO - Respuesta: {response.json()}")

            if response.status_code == 201:
                data = response.json()
                mensajes_exitosos = [
                    f"✅ ¡Registro exitoso! Tu cuenta '{usuario}' ha sido creada. 🎉\n\nAhora puedes iniciar sesión escribiendo:\n'quiero iniciar sesión'",
                    f"🎊 ¡Bienvenido {usuario}! Tu cuenta está lista. Ya puedes hacer login. 🔐",
                    f"🌟 ¡Perfecto! Usuario '{usuario}' creado exitosamente. Procede a iniciar sesión. ✨",
                    f"👤 ¡Cuenta '{usuario}' activada! Ahora inicia sesión para comenzar. 🚀",
                    f"✨ ¡Registrado! Ya eres parte del sistema, {usuario}. Haz login para continuar. 🎯"
                ]
                dispatcher.utter_message(text=random.choice(mensajes_exitosos))
                return [SlotSet("usuario", usuario), SlotSet("contraseña", None)]
            else:
                error_msg = response.json().get("error", "Error desconocido")
                mensajes_error = [
                    f"❌ Error en el registro: {error_msg}",
                    f"🔴 No pude crear tu cuenta: {error_msg}",
                    f"⚠️ Hubo un problema: {error_msg}",
                    f"❗ Registro fallido: {error_msg}"
                ]
                dispatcher.utter_message(text=random.choice(mensajes_error))
                return [SlotSet("contraseña", None)]

        except requests.exceptions.RequestException as e:
            mensajes_error = [
                "🔴 Error al conectar con el servidor. Por favor, intenta más tarde.",
                "⚠️ Problema de conexión. Intenta registrarte nuevamente en unos momentos.",
                "❌ No pude comunicarme con el servidor. Reintenta pronto.",
                "🔌 Error de red. Por favor, verifica tu conexión e intenta de nuevo."
            ]
            dispatcher.utter_message(text=random.choice(mensajes_error))
            print(f"Error en registro: {e}")
            return [SlotSet("contraseña", None)]

    def extraer_credenciales(self, texto: str) -> tuple:
        """Extrae usuario y contraseña del texto"""
        usuario = None
        contraseña = None

        # Limpiar el texto
        texto = texto.strip()
        
        print(f"🔍 DEBUG - Texto recibido para registro: '{texto}'")

        # Intentar múltiples patrones
        patrones = [
            # Patrón 1: "usuario: xxx, contraseña: yyy"
            (r'usuario[:\s]+([^\s,]+).*contraseña[:\s]+([^\s,]+)', True),
            # Patrón 2: "usuario xxx contraseña yyy"
            (r'usuario\s+(\S+)\s+contraseña\s+(\S+)', True),
            # Patrón 3: "user: xxx pass: yyy"
            (r'user[:\s]+([^\s,]+).*pass[:\s]+([^\s,]+)', True),
            # Patrón 4: Solo dos palabras (asume usuario contraseña)
            (r'^(\S+)\s+(\S+)$', False)
        ]

        for patron, tiene_palabras_clave in patrones:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                if tiene_palabras_clave or (not usuario and not contraseña):
                    usuario = match.group(1)
                    contraseña = match.group(2)
                    print(f"✅ DEBUG - Extraído: usuario='{usuario}', contraseña='{contraseña}'")
                    break

        if not usuario or not contraseña:
            print(f"❌ DEBUG - No se pudo extraer credenciales del texto")

        return usuario, contraseña


class ActionVerificarAutenticacion(Action):
    """Acción para verificar si el usuario está autenticado"""

    def name(self) -> Text:
        return "action_verificar_autenticacion"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        autenticado = tracker.get_slot("autenticado")
        
        if not autenticado:
            mensajes = [
                "🔐 Primero debes iniciar sesión para usar esta función. ¿Deseas hacer login?",
                "🔒 Necesitas autenticarte para continuar. ¿Quieres iniciar sesión?",
                "👤 No has iniciado sesión aún. ¿Te gustaría hacer login?",
                "⚠️ Debes estar autenticado para acceder a esto. ¿Iniciar sesión?",
                "🚫 Acceso restringido. Por favor inicia sesión primero."
            ]
            dispatcher.utter_message(text=random.choice(mensajes))
        
        return []