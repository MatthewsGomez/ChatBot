# Guía de Configuración: Rasa + ngrok + WhatsApp Cloud API

Esta guía te ayudará a configurar tu chatbot de Rasa localmente y conectarlo con WhatsApp usando ngrok.

## 📋 Requisitos Previos

- Python 3.8 o superior instalado
- Rasa instalado (`pip install rasa`)
- Cuenta de Facebook Developer
- Aplicación de WhatsApp Business configurada

## 🚀 Paso 1: Instalar ngrok

### Opción A: Descarga Directa
1. Ve a [ngrok.com/download](https://ngrok.com/download)
2. Descarga la versión para Windows
3. Extrae el archivo `ngrok.exe` a una carpeta (ej: `C:\ngrok\`)
4. Agrega la carpeta al PATH de Windows o usa la ruta completa

### Opción B: Usando Chocolatey
```powershell
choco install ngrok
```

### Opción C: Usando Scoop
```powershell
scoop install ngrok
```

### Verificar instalación
```powershell
ngrok version
```

## 🔑 Paso 2: Configurar ngrok (Opcional pero Recomendado)

1. Crea una cuenta gratuita en [ngrok.com](https://ngrok.com)
2. Obtén tu authtoken desde el dashboard
3. Configura el authtoken:
```powershell
ngrok config add-authtoken TU_AUTHTOKEN_AQUI
```

**Beneficios de la cuenta gratuita:**
- URLs más estables
- Más conexiones simultáneas
- Estadísticas de uso

## 📝 Paso 3: Configurar Credenciales de WhatsApp

1. Ve a [Facebook Developers](https://developers.facebook.com/apps/)
2. Selecciona tu aplicación de WhatsApp Business
3. Obtén las siguientes credenciales:
   - **Verify Token**: Un token que tú defines (ej: "mi_token_secreto_123")
   - **App Secret**: En Configuración > Básica
   - **Page Access Token**: En WhatsApp > Configuración de API
   - **Phone Number ID**: En WhatsApp > Configuración de API

4. Copia el archivo de ejemplo `.env.example` a `.env`:
```powershell
copy .env.example .env
```

5. Edita el archivo `.env` y reemplaza los valores con tus credenciales:
```env
FACEBOOK_VERIFY_TOKEN=tu_verify_token_aqui
FACEBOOK_APP_SECRET=tu_app_secret_aqui
FACEBOOK_PAGE_ACCESS_TOKEN=tu_page_access_token_aqui
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id_aqui
```

> ⚠️ **IMPORTANTE**: El archivo `.env` está en `.gitignore` y NO se subirá a GitHub. Esto protege tus credenciales.

## 🎯 Paso 4: Iniciar Rasa Localmente

1. Abre una terminal en la carpeta del proyecto
2. Ejecuta el script de inicio:
```powershell
.\run_local.bat
```

Esto iniciará:
- Servidor de acciones en `http://localhost:5055`
- Servidor Rasa en `http://localhost:5005`

## 🌐 Paso 5: Exponer Rasa con ngrok

1. Abre una **nueva terminal** (deja la anterior corriendo)
2. Ejecuta ngrok para exponer el puerto 5005:
```powershell
ngrok http 5005
```

3. Verás una salida similar a:
```
ngrok

Session Status                online
Account                       tu_cuenta (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abcd-1234-5678.ngrok-free.app -> http://localhost:5005

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

4. **Copia la URL HTTPS** (ej: `https://abcd-1234-5678.ngrok-free.app`)

> 💡 **Tip**: Puedes ver las peticiones en tiempo real en `http://127.0.0.1:4040`

## 📱 Paso 6: Configurar Webhook en WhatsApp Cloud API

1. Ve a tu aplicación en [Facebook Developers](https://developers.facebook.com/apps/)
2. Navega a **WhatsApp > Configuración**
3. En la sección **Webhook**, haz clic en **Configurar**
4. Configura el webhook:
   - **URL de devolución de llamada**: `https://TU_URL_NGROK.ngrok-free.app/webhooks/whatsapp/webhook`
   - **Token de verificación**: El mismo que pusiste en `.env` (FACEBOOK_VERIFY_TOKEN)
5. Haz clic en **Verificar y guardar**

6. Suscríbete a los siguientes campos del webhook:
   - ✅ `messages`
   - ✅ `message_deliveries` (opcional)
   - ✅ `message_reads` (opcional)

## ✅ Paso 7: Probar la Conexión

1. Desde WhatsApp Cloud API, envía un mensaje de prueba a tu número
2. O agrega tu número personal a la lista de números de prueba y envía un mensaje

3. Verifica en las terminales:
   - **Terminal de Rasa**: Deberías ver logs de mensajes recibidos
   - **ngrok Web Interface** (`http://127.0.0.1:4040`): Verás las peticiones HTTP

4. El bot debería responder según tu configuración

## 🔧 Troubleshooting

### Problema: ngrok muestra "ERR_NGROK_108"
**Solución**: Tu authtoken no es válido. Verifica que lo hayas configurado correctamente.

### Problema: WhatsApp no puede verificar el webhook
**Posibles causas:**
- El servidor Rasa no está corriendo
- La URL de ngrok es incorrecta
- El FACEBOOK_VERIFY_TOKEN en `.env` no coincide con el configurado en WhatsApp
- El firewall está bloqueando ngrok

**Solución**: 
1. Verifica que Rasa esté corriendo: `http://localhost:5005`
2. Verifica que ngrok esté corriendo y la URL sea correcta
3. Revisa los logs de Rasa para ver si llega la petición de verificación

### Problema: El bot no responde a mensajes
**Posibles causas:**
- El servidor de acciones no está corriendo
- Error en las credenciales de WhatsApp
- El modelo no está entrenado

**Solución**:
1. Verifica que el servidor de acciones esté corriendo en puerto 5055
2. Revisa los logs de Rasa para ver errores
3. Verifica que las credenciales en `.env` sean correctas
4. Entrena el modelo si es necesario: `rasa train`

### Problema: ngrok se desconecta frecuentemente
**Solución**: 
- La versión gratuita de ngrok tiene límites de tiempo de sesión
- Considera usar una cuenta de pago para sesiones más largas
- O simplemente reinicia ngrok cuando se desconecte

### Problema: La URL de ngrok cambia cada vez
**Solución**: 
- Con la cuenta gratuita, la URL cambia cada vez que reinicias ngrok
- Necesitarás actualizar el webhook en WhatsApp cada vez
- Considera una cuenta de pago de ngrok para URLs estáticas

## 📊 Monitoreo

### Ver logs de Rasa
Los logs se muestran en la terminal donde ejecutaste `run_local.bat`

### Ver peticiones HTTP en ngrok
Abre en tu navegador: `http://127.0.0.1:4040`

Aquí puedes ver:
- Todas las peticiones HTTP entrantes
- Headers y body de las peticiones
- Respuestas enviadas
- Tiempos de respuesta

## 🔄 Flujo de Trabajo Diario

1. Inicia Rasa: `.\run_local.bat`
2. Inicia ngrok: `ngrok http 5005`
3. Si la URL de ngrok cambió, actualiza el webhook en WhatsApp
4. Desarrolla y prueba tu bot
5. Cuando termines, cierra las terminales (Ctrl+C)

## 💡 Tips Adicionales

### Mantener la misma URL de ngrok (Plan Gratuito)
No es posible con el plan gratuito, pero puedes:
- Crear un script que actualice automáticamente el webhook
- Usar la API de Facebook para actualizar el webhook programáticamente

### Desarrollo más rápido
- Usa `rasa shell` para probar conversaciones sin WhatsApp
- Usa `rasa interactive` para entrenar el modelo interactivamente
- Mantén abierta la interfaz web de ngrok para debug

### Seguridad
- Nunca compartas tu authtoken de ngrok
- El archivo `.env` está en `.gitignore` y no se subirá a GitHub
- Nunca compartas tu archivo `.env` con nadie

## 📚 Recursos Adicionales

- [Documentación de Rasa](https://rasa.com/docs/)
- [Documentación de ngrok](https://ngrok.com/docs)
- [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Rasa WhatsApp Connector](https://rasa.com/docs/rasa/connectors/whatsapp)

## 🆘 Soporte

Si tienes problemas:
1. Revisa los logs de Rasa
2. Revisa la interfaz web de ngrok
3. Verifica las credenciales en `.env`
4. Consulta la documentación oficial de Rasa y WhatsApp
