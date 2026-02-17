# 🤖 Kimi AI Integration Guide

Este documento explica cómo Kimi Claw puede acceder al CocoCRM vía Telegram.

---

## 🎯 Flujo de Acceso

### Para Kimi (Usuario AI):

1. **Enviar comando por Telegram**:
   ```
   /crm
   ```

2. **Recibir link temporal**:
   ```
   ✅ Login link generated successfully!

   🔗 Click here to access CocoCRM:
   https://cococrm.onrender.com/?token=eyJ0eXAiOiJKV1QiLCJhbGc...

   ⏱ Valid for: 180 minutes

   🔒 This link is personal and temporary. Don't share it!
   ```

3. **Acceder al CRM**:
   - El link abre directamente el CRM
   - No requiere usuario/contraseña
   - Sesión válida por 180 minutos (3 horas)

---

## 🔧 Implementación Técnica

### 1. Telegram Bot (`@Cangrekimibot`)

**Comando disponible**: `/crm`

**Comportamiento**:
- Genera un JWT temporal (180 min)
- Retorna URL completa: `https://cococrm.onrender.com/?token=XXX`

### 2. Backend API

**Endpoint**: `POST /api/telegram/generate-token`

**Autenticación**:
```json
{
  "api_key": "kimi-claw-secure-api-key-2026",
  "telegram_id": "123456789",
  "username": "kimi_claw"
}
```

**Respuesta exitosa**:
```json
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "url": "https://cococrm.onrender.com/?token=eyJ0eXAiOiJKV1QiLCJhbGc...",
  "expires_in": 180,
  "user": {
    "id": 1,
    "username": "kimi_ai_agent"
  }
}
```

### 3. Auto-Login en Frontend

Cuando Kimi abre la URL con `?token=XXX`:

1. El backend valida el token JWT
2. Si es válido, autentica al usuario automáticamente
3. Redirige al dashboard
4. Kimi puede navegar normalmente por el CRM

---

## 🔐 Seguridad

### Token JWT Temporal

- **Algoritmo**: HS256
- **Expiración**: 180 minutos (3 horas)
- **Contenido**:
  ```json
  {
    "user_id": 1,
    "username": "kimi_ai_agent",
    "exp": 1708185600,
    "iat": 1708174800,
    "type": "temp_login"
  }
  ```

### API Key

- **Variable**: `TELEGRAM_API_KEY`
- **Valor actual**: `kimi-claw-secure-api-key-2026`
- **Uso**: Autenticar requests al endpoint `/api/telegram/generate-token`

### Usuario de Servicio

Si Kimi se autentica con `api_key`, se crea/usa el usuario:
- **Username**: `kimi_ai_agent`
- **Nombre**: Kimi AI Agent
- **Permisos**: Igual que cualquier usuario normal del CRM

---

## 📊 Variables de Entorno (Render)

Asegúrate de configurar en Render:

```bash
# Bot Token
TELEGRAM_BOT_TOKEN=8257190993:AAEfMhATLKX9o3OvxM9v696pZQ1XgCuS9OA

# Bot Username
TELEGRAM_BOT_USERNAME=Cangrekimibot

# API Key para Kimi
TELEGRAM_API_KEY=kimi-claw-secure-api-key-2026

# URL del CRM
BASE_URL=https://cococrm.onrender.com

# Flask Secret (para JWT)
SECRET_KEY=coco-crm-production-secret-key-2026-render-deployment
```

---

## 🧪 Testing

### Probar el bot manualmente:

1. Abrir Telegram
2. Buscar `@Cangrekimibot`
3. Enviar `/crm`
4. Click en el link recibido
5. Verificar acceso al dashboard

### Probar el API directamente:

```bash
curl -X POST https://cococrm.onrender.com/api/telegram/generate-token \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "kimi-claw-secure-api-key-2026",
    "username": "kimi_claw"
  }'
```

**Respuesta esperada**:
```json
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1Qi...",
  "url": "https://cococrm.onrender.com/?token=eyJ0eXAiOiJKV1Qi...",
  "expires_in": 180,
  "user": {
    "id": 1,
    "username": "kimi_ai_agent"
  }
}
```

---

## 🚀 Deploy

El bot de Telegram se ejecuta automáticamente en Render junto con el servidor Flask.

**Proceso de inicio** (`start.sh`):
```bash
# 1. Inicia el bot de Telegram en background
python telegram_bot.py &

# 2. Inicia el servidor Flask en foreground
gunicorn app:app --bind 0.0.0.0:$PORT
```

---

## 🐛 Troubleshooting

### Bot no responde

1. Verificar logs de Render
2. Confirmar que `TELEGRAM_BOT_TOKEN` está configurado
3. Verificar que el bot está corriendo: `ps aux | grep telegram_bot`

### Token inválido o expirado

- Los tokens expiran después de 180 minutos
- Solicitar un nuevo token con `/crm`

### Error 404 al acceder con token

- Verificar que `BASE_URL` está correctamente configurado
- Confirmar que el servidor Flask está respondiendo

### Error de autenticación en el API

- Verificar que `TELEGRAM_API_KEY` coincide en ambos lados
- Revisar logs del servidor para más detalles

---

## 📝 Notas

- El sistema está diseñado para que Kimi pueda acceder sin intervención humana
- Los tokens son de un solo uso efectivo (una vez usado, puedes pedir otro)
- El usuario `kimi_ai_agent` se crea automáticamente en el primer uso
- No hay límite de tokens que Kimi puede generar (pero cada uno expira en 180 min)
