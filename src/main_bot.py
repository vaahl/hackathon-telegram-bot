import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# IMPORTAMOS NUESTRA LÓGICA
# Agregamos 'inicializar_inteligencia' a la importación
from logicaBot import analizar_redirecciones, verificar_fuente, inicializar_inteligencia

# Configuración de Logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Cargar entorno
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('TELEGRAM_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Soy VerificaChile.\n\n"
        "Estoy conectado a bases de datos globales (Phishing) y locales (Chile).\n"
        "Usa el comando /check seguido de un link para analizarlo.\n"
        "Ejemplo: `/check https://bit.ly/oferta-falsa`",
        parse_mode='Markdown'
    )

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Validar que el usuario envió un link
    if not context.args:
        await update.message.reply_text("⚠️ Debes enviar una URL. Ejemplo: `/check google.cl`", parse_mode='Markdown')
        return

    url_usuario = context.args[0]
    await update.message.reply_text(f"🕵️‍♂️ Analizando: `{url_usuario}` ...", parse_mode='Markdown')

    # 2. LLAMAR AL CEREBRO (logicaBot.py)
    
    # A. Análisis de Redirecciones
    url_final, historial = analizar_redirecciones(url_usuario)

    if not url_final:
        # Si falla la conexión, cortamos aquí
        await update.message.reply_text(f"❌ No se pudo acceder al sitio.\nError: {historial[0]}")
        return

    # B. Análisis de Fuente (Whitelist/Blacklist Local + Global)
    estado_fuente, msg_fuente, emoji_fuente = verificar_fuente(url_final)

    # 3. CONSTRUIR EL REPORTE FINAL
    mensaje = f"🛡️ **REPORTE DE CIBERSEGURIDAD**\n"
    mensaje += f"───────────────────────\n\n"
    
    # Sección: Veredicto de Fuente
    mensaje += f"**Fuentes e Identidad:**\n"
    mensaje += f"{emoji_fuente} **Veredicto:** {estado_fuente}\n"
    mensaje += f"📝 {msg_fuente}\n\n"

    # Sección: Detalles Técnicos (Redirecciones)
    if len(historial) > 0:
        mensaje += f"**Rastreo de Redirecciones:**\n"
        mensaje += f"⚠️ **Link Enmascarado:** El link original no muestra el destino real.\n"
        trace = "\n".join(historial[:5]) 
        mensaje += f"`{trace}`\n\n"
    elif url_usuario != url_final:
        mensaje += f"**Nota:** Hubo un pequeño cambio en la URL (ej. HTTP -> HTTPS)\n\n"
    else:
        mensaje += f"✅ **Conexión Directa:** Sin intermediarios sospechosos.\n\n"
    
    mensaje += f"🔗 **URL Final:** {url_final}"

    # Enviar respuesta
    await update.message.reply_text(mensaje, parse_mode='Markdown')

if __name__ == '__main__':
    if not TOKEN:
        print("❌ ERROR: Falta el token en el archivo .env")
    else:
        # --- NUEVO: Cargamos la inteligencia antes de encender el bot ---
        print("🧠 Cargando cerebro del bot...")
        inicializar_inteligencia()
        # -------------------------------------------------------------

        application = ApplicationBuilder().token(TOKEN).build()
        
        # Agregamos los comandos
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('check', check))
        
        print("🤖 VerificaChile Bot corriendo...")
        application.run_polling()