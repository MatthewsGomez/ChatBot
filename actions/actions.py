from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, SessionStarted, ActionExecuted
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
                "⚠️ No pude leer tus credenciales. Asegúrate de usar el formato:\n\nusuario: tu_usuario, contraseña: tu_contraseña",
                "🔐 Faltan tus datos de acceso. Escríbelos así:\n\nusuario: tu_usuario, contraseña: tu_contraseña",
                "📝 Necesito tus credenciales en este formato:\n\nusuario: tu_usuario, contraseña: tu_contraseña"
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
                
                print(f"✅ DEBUG LOGIN - Usuario '{usuario}' autenticado con ID: {id_usuario} (tipo: {type(id_usuario)})")
                
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
                
                print(f"✅ DEBUG LOGIN - Guardando en slot id_usuario: '{id_usuario}' como string")
                
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
                "⚠️ Necesito tus credenciales en este formato:\n\nusuario: tu_usuario, contraseña: tu_contraseña",
                "📝 Para registrarte escribe así:\n\nusuario: tu_usuario, contraseña: tu_contraseña",
                "🔐 Faltan tus datos. Formato correcto:\n\nusuario: tu_usuario, contraseña: tu_contraseña"
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
                    f"❗ Registro fallido: {error_msg}",
                    f"🚫 No se pudo completar el registro: {error_msg}"
                ]
                dispatcher.utter_message(text=random.choice(mensajes_error))
                return [SlotSet("contraseña", None)]

        except requests.exceptions.RequestException as e:
            mensajes_error = [
                "🔴 Error al conectar con el servidor. Por favor, intenta más tarde.",
                "⚠️ Problema de conexión. Intenta registrarte nuevamente en unos momentos.",
                "❌ No pude comunicarme con el servidor. Reintenta pronto.",
                "🔌 Error de red. Por favor, verifica tu conexión e intenta de nuevo.",
                "🚫 Sin conexión al servidor. Intenta más tarde."
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


class ActionHacerPrediccion(Action):
    """Acción para hacer la predicción llamando a la API"""

    def name(self) -> Text:
        return "action_hacer_prediccion"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Verificar autenticación
        autenticado = tracker.get_slot("autenticado")
        id_usuario = tracker.get_slot("id_usuario")
        
        if not autenticado or not id_usuario:
            mensajes = [
                "🔐 Debes iniciar sesión para hacer predicciones.",
                "🔒 Primero necesitas autenticarte para usar esta función.",
                "⚠️ No has iniciado sesión. Por favor inicia sesión primero.",
                "� Acceso restringido. Debes estar autenticado.",
                "👤 Inicia sesión para acceder a las predicciones."
            ]
            dispatcher.utter_message(text=random.choice(mensajes))
            return []

        # Recopilar todos los datos del formulario
        try:
            print(f"📊 DEBUG PREDICCIÓN - id_usuario del slot: '{id_usuario}' (tipo: {type(id_usuario)})")
            
            datos_prediccion = {
                "id_usuario": int(id_usuario),
                "Day_of_Week": int(tracker.get_slot("day_of_week")),
                "Junction_Control": int(tracker.get_slot("junction_control")),
                "Junction_Detail": int(tracker.get_slot("junction_detail")),
                "Light_Conditions": int(tracker.get_slot("light_conditions")),
                "Local_Authority_(District)": int(tracker.get_slot("local_authority")),
                "Road_Surface_Conditions": int(tracker.get_slot("road_surface")),
                "Road_Type": int(tracker.get_slot("road_type")),
                "Speed_limit": int(tracker.get_slot("speed_limit")),
                "Urban_or_Rural_Area": int(tracker.get_slot("urban_rural")),
                "Weather_Conditions": int(tracker.get_slot("weather")),
                "Vehicle_Type": int(tracker.get_slot("vehicle_type")),
                "Number_of_Casualties": int(tracker.get_slot("casualties")),
                "Number_of_Vehicles": int(tracker.get_slot("num_vehicles"))
            }
            
            print(f"📊 DEBUG PREDICCIÓN - Enviando a API con id_usuario: {datos_prediccion['id_usuario']} (tipo: {type(datos_prediccion['id_usuario'])})")
            print(f"📊 DEBUG PREDICCIÓN - Datos completos: {datos_prediccion}")
            
            # Llamar a la API de predicción
            response = requests.post(
                f"{API_BASE_URL}/predict",
                json=datos_prediccion,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            print(f"📊 DEBUG PREDICCIÓN - Status Code: {response.status_code}")
            
            if response.status_code == 200:
                resultado = response.json()
                print(f"📊 DEBUG PREDICCIÓN - Respuesta: {resultado}")
                
                # Formatear el mensaje de respuesta - usar variaciones
                mensajes = [
                    f"""
🎯 **RESULTADOS DE LA PREDICCIÓN** 🎯

📊 **Modelos de IA:**
• Random Forest: {resultado.get('RandomForest', 'N/A')}
• SVM: {resultado.get('SVM', 'N/A')}
• KNN: {resultado.get('KNN', 'N/A')}

🏆 **Mejor Modelo:** {resultado.get('MejorModelo', 'Random Forest')}

✅ {resultado.get('Guardado', 'Predicción guardada')}

💡 **Recuerda:** Esta es una predicción basada en datos históricos. Siempre mantén precaución en las vías.
""",
                    f"""
✨ **ANÁLISIS COMPLETADO** ✨

🤖 **Predicciones por Modelo:**
🌳 Random Forest: {resultado.get('RandomForest', 'N/A')}
📊 SVM: {resultado.get('SVM', 'N/A')}
🔵 KNN: {resultado.get('KNN', 'N/A')}

🌟 **Modelo Destacado:** {resultado.get('MejorModelo', 'Random Forest')}

💾 {resultado.get('Guardado', 'Datos almacenados exitosamente')}

⚠️ **Nota:** Predicción basada en análisis de datos. Conduce siempre con precaución.
""",
                    f"""
🚨 **PREDICCIÓN FINALIZADA** 🚨

🔮 **Resultados de los Algoritmos:**
🎯 Random Forest → {resultado.get('RandomForest', 'N/A')}
🎯 SVM → {resultado.get('SVM', 'N/A')}
🎯 KNN → {resultado.get('KNN', 'N/A')}

🥇 **Algoritmo Más Preciso:** {resultado.get('MejorModelo', 'Random Forest')}

✅ {resultado.get('Guardado', 'Registro guardado en tu historial')}

👉 **Importante:** Resultados predictivos. Conduce con responsabilidad.
""",
                    f"""
📊 **REPORTE DE PREDICCIÓN** 📊

🔍 **Modelos Analizados:**
▪️ Random Forest: {resultado.get('RandomForest', 'N/A')}
▪️ SVM: {resultado.get('SVM', 'N/A')}
▪️ KNN: {resultado.get('KNN', 'N/A')}

🏅 **Modelo Óptimo:** {resultado.get('MejorModelo', 'Random Forest')}

📝 {resultado.get('Guardado', 'Predicción registrada correctamente')}

❗ **Advertencia:** Predicción estadística. Sigue las normas de tránsito.
""",
                    f"""
🔵 **RESULTADOS DEL ANÁLISIS** 🔵

🧠 **Predicciones IA:**
🎯 RF: {resultado.get('RandomForest', 'N/A')}
🎯 SVM: {resultado.get('SVM', 'N/A')}
🎯 KNN: {resultado.get('KNN', 'N/A')}

🥇 **Top Model:** {resultado.get('MejorModelo', 'Random Forest')}

✅ {resultado.get('Guardado', '¡Guardado en tu historial!')}

🔴 **Recuerda:** Análisis predictivo. La seguridad vial es responsabilidad de todos.
"""
                ]
                dispatcher.utter_message(text=random.choice(mensajes))
                
                # Limpiar los slots del formulario
                return [
                    SlotSet("day_of_week", None),
                    SlotSet("junction_control", None),
                    SlotSet("junction_detail", None),
                    SlotSet("light_conditions", None),
                    SlotSet("local_authority", None),
                    SlotSet("road_surface", None),
                    SlotSet("road_type", None),
                    SlotSet("speed_limit", None),
                    SlotSet("urban_rural", None),
                    SlotSet("weather", None),
                    SlotSet("vehicle_type", None),
                    SlotSet("casualties", None),
                    SlotSet("num_vehicles", None)
                ]
            else:
                error = response.json().get("error", "Error desconocido")
                mensajes_error = [
                    f"❌ Error al hacer la predicción: {error}",
                    f"🔴 No pude procesar la predicción: {error}",
                    f"⚠️ Problema al generar resultados: {error}",
                    f"🚫 Fallo en el análisis: {error}",
                    f"🔴 Error en el sistema de predicción: {error}"
                ]
                dispatcher.utter_message(text=random.choice(mensajes_error))
                return []
                
        except Exception as e:
            print(f"❌ ERROR en predicción: {e}")
            mensajes_error = [
                "🔴 Hubo un error al procesar la predicción. Por favor, intenta de nuevo.",
                "❌ Error procesando tu solicitud. Reintenta en un momento.",
                "⚠️ Ocurrió un error. Por favor intenta nuevamente.",
                "🚫 No pude completar la predicción. Intenta de nuevo.",
                "🔴 Error inesperado. Por favor, reintenta."
            ]
            dispatcher.utter_message(text=random.choice(mensajes_error))
            return []


class ActionEnviarHistorial(Action):
    """Acción para solicitar el email y enviar el historial por correo"""

    def name(self) -> Text:
        return "action_enviar_historial"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Verificar autenticación
        autenticado = tracker.get_slot("autenticado")
        id_usuario = tracker.get_slot("id_usuario")
        
        if not autenticado or not id_usuario:
            mensajes = [
                "🔐 Primero debes iniciar sesión para ver tu historial.",
                "🔒 Necesitas autenticarte para acceder a tu historial.",
                "👤 Por favor inicia sesión primero para consultar tu historial.",
                "⚠️ Debes estar autenticado para ver tus predicciones anteriores.",
                "🚫 Acceso restringido. Inicia sesión para ver el historial."
            ]
            dispatcher.utter_message(text=random.choice(mensajes))
            return []

        # Obtener email del slot
        email = tracker.get_slot("email")
        
        # Si no hay email, extraerlo del último mensaje
        if not email:
            ultimo_mensaje = tracker.latest_message.get('text', '')
            email = self.extraer_email(ultimo_mensaje)
        
        # Si aún no hay email, solicitarlo
        if not email:
            dispatcher.utter_message(response="utter_pedir_email")
            return []
        
        # Validar formato de email
        if not self.validar_email(email):
            mensajes = [
                "❌ El formato del email no es válido. Por favor, proporciona un correo válido.",
                "🔴 Email inválido. Verifica el formato (ejemplo@correo.com).",
                "⚠️ El correo que ingresaste no es válido. Intenta de nuevo.",
                "📧 Formato incorrecto. Escribe un email válido.",
                "🚫 Email no válido. Usa el formato: usuario@dominio.com"
            ]
            dispatcher.utter_message(text=random.choice(mensajes))
            return [SlotSet("email", None)]
        
        try:
            # Llamar a la API para enviar el historial
            print(f"📧 DEBUG HISTORIAL - id_usuario del slot: '{id_usuario}' (tipo: {type(id_usuario)})")
            print(f"📧 DEBUG HISTORIAL - Convirtiendo a int: {int(id_usuario)}")
            print(f"📧 DEBUG HISTORIAL - Enviando a: {email} para usuario: {id_usuario}")
            
            response = requests.post(
                f"{API_BASE_URL}/enviar_historial",
                json={"id_usuario": int(id_usuario), "email": email},
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            
            print(f"📧 DEBUG HISTORIAL - Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"📧 DEBUG HISTORIAL - Respuesta de error: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                total = data.get("total_predicciones", 0)
                
                mensajes_exitosos = [
                    f"✅ ¡Listo! He enviado tu historial con {total} predicciones a {email}. 📧\n\nRevisa tu bandeja de entrada (y spam si no lo ves).",
                    f"🎉 ¡Historial enviado! {total} predicciones han sido enviadas a {email}. 📬\n\nChequea tu correo.",
                    f"📨 ¡Perfecto! Tu PDF con {total} predicciones está en camino a {email}. ✉️\n\nRevisa tu correo en unos momentos.",
                    f"✨ ¡Hecho! He enviado {total} predicciones a tu correo {email}. 💌\n\nLlega en breve.",
                    f"🚀 ¡Envío exitoso! {total} predicciones en camino a {email}. 📩\n\nRevisa tu bandeja."
                ]
                
                dispatcher.utter_message(text=random.choice(mensajes_exitosos))
                return [SlotSet("email", None)]
                
            elif response.status_code == 404:
                mensajes_sin_datos = [
                    "📭 No tienes predicciones guardadas aún.\n\n¡Haz tu primera predicción para comenzar tu historial!",
                    "🤷 Todavía no has realizado ninguna predicción.\n\n¿Quieres hacer una ahora?",
                    "📊 Tu historial está vacío. ¡Empieza haciendo tu primera predicción!",
                    "📄 Sin datos aún. Haz una predicción primero.",
                    "🆕 Historial vacío. ¡Realiza tu primera predicción!"
                ]
                dispatcher.utter_message(text=random.choice(mensajes_sin_datos))
                return [SlotSet("email", None)]
                
            else:
                error_msg = response.json().get("error", "Error desconocido")
                mensajes_error = [
                    f"❌ No pude enviar el historial: {error_msg}",
                    f"🔴 Hubo un problema al enviar el correo: {error_msg}",
                    f"⚠️ Error al procesar tu solicitud: {error_msg}",
                    f"🚫 Fallo en el envío del historial: {error_msg}",
                    f"📧 No se pudo enviar el email: {error_msg}"
                ]
                dispatcher.utter_message(text=random.choice(mensajes_error))
                return [SlotSet("email", None)]
                
        except requests.exceptions.Timeout:
            mensajes_timeout = [
                "⏱️ La solicitud tomó demasiado tiempo. Por favor, intenta de nuevo.",
                "⏳ Tiempo de espera agotado. Reintenta en un momento.",
                "🕒 El servidor tardó mucho en responder. Intenta nuevamente.",
                "⚠️ Timeout. Por favor intenta de nuevo.",
                "⏰ Solicitud expirada. Reintenta por favor."
            ]
            dispatcher.utter_message(text=random.choice(mensajes_timeout))
            return [SlotSet("email", None)]
            
        except requests.exceptions.RequestException as e:
            mensajes_error = [
                "🔴 Error al conectar con el servidor. Por favor, intenta más tarde.",
                "⚠️ Problema de conexión. Intenta nuevamente en unos momentos.",
                "❌ No pude comunicarme con el servidor. Reintenta pronto.",
                "🔌 Error de red. Verifica tu conexión.",
                "🚫 Sin conexión al servidor. Intenta más tarde."
            ]
            dispatcher.utter_message(text=random.choice(mensajes_error))
            print(f"Error en envío de historial: {e}")
            return [SlotSet("email", None)]

    def extraer_email(self, texto: str) -> str:
        """Extrae el email del texto usando expresiones regulares"""
        # Patrón para detectar emails
        patron = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(patron, texto)
        
        if match:
            email = match.group(0)
            print(f"✅ DEBUG - Email extraído: {email}")
            return email
        
        print(f"❌ DEBUG - No se pudo extraer email del texto: '{texto}'")
        return None

    def validar_email(self, email: str) -> bool:
        """Valida el formato del email"""
        if not email:
            return False
        patron = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        return bool(re.match(patron, email))