#!/usr/bin/env python3
"""
Script para verificar la configuración del bot de Telegram
"""
import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def get_bot_info():
    """Obtiene información del bot"""
    print("🔍 Verificando configuración del bot de Telegram...")
    print("=" * 60)

    if not TELEGRAM_BOT_TOKEN:
        print("❌ ERROR: No se encontró TELEGRAM_BOT_TOKEN en .env")
        print("\nAsegúrate de crear un archivo .env con:")
        print("TELEGRAM_BOT_TOKEN=tu-token-aqui")
        return False

    # Verificar token
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"

    try:
        response = requests.get(url)
        data = response.json()

        if data.get('ok'):
            bot = data['result']
            print("✅ Bot configurado correctamente!")
            print("-" * 60)
            print(f"📱 Nombre del Bot: {bot['first_name']}")
            print(f"🔗 Username: @{bot['username']}")
            print(f"🆔 Bot ID: {bot['id']}")
            print(f"✓ Es Bot: {'Sí' if bot['is_bot'] else 'No'}")
            print("-" * 60)

            # Instrucciones
            print("\n📋 PRÓXIMOS PASOS:")
            print("-" * 60)
            print("\n1️⃣  Configurar el dominio en BotFather:")
            print("    • Abre Telegram y busca @BotFather")
            print("    • Envía: /mybots")
            print(f"    • Selecciona: @{bot['username']}")
            print("    • Selecciona: Bot Settings")
            print("    • Selecciona: Domain")
            print("    • Escribe: cococrm.onrender.com")

            print("\n2️⃣  Configurar en Render Dashboard:")
            print("    • Ve a: https://dashboard.render.com/")
            print("    • Selecciona tu servicio 'cococrm'")
            print("    • Ve a: Environment")
            print("    • Agrega estas variables:")
            print(f"\n    SECRET_KEY=coco-crm-production-key-{bot['id']}")
            print(f"    TELEGRAM_BOT_TOKEN={TELEGRAM_BOT_TOKEN}")

            print("\n3️⃣  Deploy a Render:")
            print("    • Opción A: Push a GitHub (deploy automático)")
            print("    • Opción B: Manual Deploy en Render Dashboard")

            print("\n4️⃣  Probar el login:")
            print("    • Ve a: https://cococrm.onrender.com/login")
            print("    • Click en 'Log in with Telegram'")
            print("    • Autoriza el bot")
            print("    • ¡Listo!")

            print("\n" + "=" * 60)
            print("✨ ¡Tu bot está listo para usar!")
            print("=" * 60)

            return True
        else:
            print(f"❌ ERROR: {data.get('description', 'Token inválido')}")
            return False

    except Exception as e:
        print(f"❌ ERROR de conexión: {e}")
        print("\nVerifica:")
        print("1. Tienes conexión a internet")
        print("2. El token es correcto")
        return False

if __name__ == "__main__":
    get_bot_info()
