# 🤖 Configuración de Telegram para @Cangrekimibot

## ✅ Ya Configurado

- ✅ Token del bot: `8257190993:AAEfMhATLKX9o3OvxM9v696pZQ1XgCuS9OA`
- ✅ Username del bot: `@Cangrekimibot`
- ✅ Código actualizado para usar el bot correctamente

## 📋 Pasos que DEBES Hacer en BotFather

### 1. Configurar el Dominio (MUY IMPORTANTE)

Abre Telegram y habla con **@BotFather**:

```
Tú: /mybots
BotFather: [muestra tu lista de bots]
Tú: [Selecciona @Cangrekimibot]
BotFather: [muestra el menú del bot]
Tú: Bot Settings
BotFather: [muestra opciones]
Tú: Domain
BotFather: Send me the domain name for your bot
Tú: cococrm.onrender.com
BotFather: Success! Domain cococrm.onrender.com has been set.
```

**⚠️ CRÍTICO:** Sin este paso, el botón de "Login with Telegram" NO funcionará.

## 🚀 Configurar Variables de Entorno en Render

### Ir al Dashboard de Render

1. Ve a: https://dashboard.render.com/
2. Busca y selecciona tu servicio **"cococrm"**
3. En el menú lateral, click en **"Environment"**

### Agregar/Verificar Variables de Entorno

Asegúrate de tener estas 3 variables:

**Variable 1:**
```
Key: SECRET_KEY
Value: coco-crm-production-secret-key-2026-render-deployment
```

**Variable 2:**
```
Key: TELEGRAM_BOT_TOKEN
Value: 8257190993:AAEfMhATLKX9o3OvxM9v696pZQ1XgCuS9OA
```

**Variable 3:**
```
Key: TELEGRAM_BOT_USERNAME
Value: Cangrekimibot
```

### Guardar y Redeploy

1. Click en **"Save Changes"**
2. Render automáticamente redeployará la aplicación
3. Espera 2-3 minutos

## 🧪 Probar que Funciona

### 1. Acceder al Sitio

Abre: **https://cococrm.onrender.com/login**

### 2. Verificar el Botón de Telegram

Deberías ver:
- ✅ Un botón azul que dice "Log in with Telegram"
- ✅ El botón tiene el logo de Telegram

Si no ves el botón:
- ❌ Revisa que las variables de entorno estén correctas
- ❌ Espera unos minutos más para que Render termine el deployment

### 3. Probar el Login

1. Click en **"Log in with Telegram"**
2. Se abrirá una ventana de Telegram
3. Click en **"Confirm"** para autorizar
4. Deberías ser redirigido al dashboard automáticamente

## 🎯 Checklist Final

Antes de probar, asegúrate de haber hecho TODO esto:

- [ ] Configuré el dominio `cococrm.onrender.com` en BotFather
- [ ] Agregué `SECRET_KEY` en Render Environment
- [ ] Agregué `TELEGRAM_BOT_TOKEN` en Render Environment
- [ ] Agregué `TELEGRAM_BOT_USERNAME` en Render Environment
- [ ] Guardé los cambios en Render
- [ ] Esperé a que termine el deployment (2-3 minutos)
- [ ] Probé acceder a https://cococrm.onrender.com/login

## 🐛 Troubleshooting

### El botón no aparece

**Causa:** Variables de entorno no configuradas

**Solución:**
1. Ve a Render Dashboard > Environment
2. Verifica que `TELEGRAM_BOT_USERNAME` esté presente
3. El valor debe ser exactamente: `Cangrekimibot` (sin @)
4. Guarda y redeploy

### El botón aparece pero da error al clickear

**Causa:** Dominio no configurado en BotFather

**Solución:**
1. Abre Telegram y busca @BotFather
2. `/mybots` > @Cangrekimibot > Bot Settings > Domain
3. Escribe: `cococrm.onrender.com`

### "Invalid authentication data"

**Causa:** Token o dominio incorrecto

**Solución:**
1. Verifica que el token en Render sea exactamente:
   `8257190993:AAEfMhATLKX9o3OvxM9v696pZQ1XgCuS9OA`
2. Verifica que el dominio en BotFather sea:
   `cococrm.onrender.com` (sin https://)

## 📱 Información del Bot

- **Bot ID:** 8257190993
- **Username:** @Cangrekimibot
- **Dominio:** cococrm.onrender.com
- **Sitio Web:** https://cococrm.onrender.com/

## ✨ ¡Todo Listo!

Una vez completados todos los pasos, tus usuarios podrán:

1. 🔐 Hacer login con su cuenta de Telegram con un solo click
2. 📝 O registrarse con usuario/contraseña tradicional
3. 📊 Acceder al dashboard del CRM

¡Disfruta de tu CRM con autenticación de Telegram! 🎉
