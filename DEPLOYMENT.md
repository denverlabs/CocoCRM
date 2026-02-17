# 🚀 Guía de Deployment en Render

## Paso 1: Configurar tu Bot de Telegram

### 1.1 Obtener el Token del Bot

Si ya tienes tu bot, ve a Telegram y habla con **@BotFather**:

```
Tú: /mybots
BotFather: [muestra lista de tus bots]
Tú: [selecciona tu bot]
BotFather: [muestra opciones]
Tú: API Token
BotFather: [muestra tu token]
```

Copia el token. Se ve así: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### 1.2 Configurar el Dominio en BotFather

**MUY IMPORTANTE:** Para que el login de Telegram funcione, debes configurar el dominio:

```
Tú: /mybots
BotFather: [selecciona tu bot]
Tú: Bot Settings
Tú: Domain
Tú: cococrm.onrender.com
```

BotFather confirmará que el dominio fue configurado.

## Paso 2: Configurar Variables de Entorno en Render

### 2.1 Ir a tu Dashboard de Render

1. Ve a https://dashboard.render.com/
2. Encuentra tu servicio "cococrm" (o como se llame)
3. Click en el nombre del servicio

### 2.2 Configurar Environment Variables

1. En el menú lateral, click en **"Environment"**
2. Agrega las siguientes variables:

**Variable 1:**
- **Key:** `SECRET_KEY`
- **Value:** (genera una clave aleatoria segura, por ejemplo: `your-very-secure-random-secret-key-here`)
- Puedes generar una con: `openssl rand -hex 32`

**Variable 2:**
- **Key:** `TELEGRAM_BOT_TOKEN`
- **Value:** (pega aquí el token que copiaste de BotFather)

3. Click en **"Save Changes"**

### 2.3 Ejemplo de Configuración

```
SECRET_KEY = abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
TELEGRAM_BOT_TOKEN = 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

## Paso 3: Deploy

### Opción A: Desde el Dashboard de Render

1. Ve a tu servicio en Render
2. Click en **"Manual Deploy"** > **"Deploy latest commit"**
3. Espera a que termine el deployment (2-3 minutos)

### Opción B: Automatic Deploy (Recomendado)

Render detecta automáticamente cuando haces push a tu repositorio:

```bash
git add .
git commit -m "Configure for production"
git push origin main
```

Render deployará automáticamente.

## Paso 4: Verificar que Funciona

### 4.1 Acceder a tu Sitio

Abre tu navegador en: **https://cococrm.onrender.com/**

Deberías ver la página de login con:
- ✅ Formulario de usuario/contraseña
- ✅ Botón de "Login with Telegram"

### 4.2 Probar el Login

**Opción 1: Con Contraseña**
1. Click en "Create one" para registrarte
2. Crea una cuenta
3. Inicia sesión

**Opción 2: Con Telegram**
1. Click en el botón azul "Log in with Telegram"
2. Se abrirá Telegram
3. Autoriza el bot
4. Automáticamente entrarás al dashboard

## Troubleshooting

### El botón de Telegram no aparece

**Problema:** No configuraste el `TELEGRAM_BOT_TOKEN` en Render

**Solución:**
1. Ve a Render Dashboard > Environment
2. Agrega `TELEGRAM_BOT_TOKEN` con el valor de tu token
3. Redeploy

### Error: "Invalid authentication data"

**Problema:** No configuraste el dominio en BotFather

**Solución:**
1. Abre Telegram
2. Habla con @BotFather
3. Ejecuta: `/mybots` > [tu bot] > Bot Settings > Domain
4. Escribe: `cococrm.onrender.com`

### El sitio no carga

**Problema:** Error en el deployment

**Solución:**
1. Ve a Render Dashboard > Logs
2. Revisa los errores
3. Asegúrate que todas las dependencias estén en `requirements.txt`

## Comandos Útiles para BotFather

```
/mybots          - Ver todos tus bots
/setdomain       - Configurar dominio (método alternativo)
/setdescription  - Cambiar descripción del bot
/setabouttext    - Cambiar "About" del bot
/setuserpic      - Cambiar foto del bot
```

## Estructura de Archivos Importante

```
CocoCRM/
├── app.py              # Aplicación principal
├── requirements.txt    # Dependencias Python
├── Procfile           # Comando para iniciar en Render
├── render.yaml        # Configuración de Render
└── templates/         # Plantillas HTML
    ├── login.html
    ├── register.html
    └── dashboard.html
```

## URLs del Proyecto

- **Sitio Web:** https://cococrm.onrender.com/
- **Login:** https://cococrm.onrender.com/login
- **Register:** https://cococrm.onrender.com/register
- **Dashboard:** https://cococrm.onrender.com/dashboard (requiere login)

## Seguridad

⚠️ **IMPORTANTE:**
- NUNCA compartas tu `TELEGRAM_BOT_TOKEN` públicamente
- NUNCA hagas commit del archivo `.env` al repositorio
- Usa claves `SECRET_KEY` largas y aleatorias
- Habilita HTTPS (Render lo hace automáticamente)

## Próximos Pasos

1. ✅ Configura el bot en BotFather
2. ✅ Agrega las variables de entorno en Render
3. ✅ Deploy automático desde GitHub
4. 🎉 ¡Tu CRM está funcionando!

## Soporte

Si tienes problemas:
1. Revisa los logs en Render Dashboard
2. Verifica que el dominio esté configurado en BotFather
3. Asegúrate que las variables de entorno estén correctas
