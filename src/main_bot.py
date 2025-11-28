import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# IMPORTAMOS NUESTRA LÓGICA (Incluyendo la nueva función)
from logicaBot import (
    analizar_redirecciones, 
    verificar_fuente, 
    inicializar_inteligencia,
    analizar_contenido 
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Nota: la función `start` se define más abajo con botones interactivos.

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Envía una URL. Ej: `/check google.cl`", parse_mode='Markdown')
        return

    url_usuario = context.args[0]
    await update.message.reply_text(f"🕵️‍♂️ **Analizando:** `{url_usuario}` ...", parse_mode='Markdown')

    # 1. Redirecciones
    url_final, historial = analizar_redirecciones(url_usuario)
    if not url_final:
        await update.message.reply_text(f"❌ Error: Sitio inaccesible.\n{historial[0]}")
        return

    # 2. Reputación de Fuente
    estado, msg_fuente, emoji = verificar_fuente(url_final)

    # 3. Análisis de Contenido (SOLO si no es peligroso)
    info_contenido = None
    if estado != "PELIGROSO": # No leemos sitios de malware
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing") # Efecto "escribiendo..."
        info_contenido = analizar_contenido(url_final)

    # --- CONSTRUCCIÓN DEL REPORTE ---
    reporte = f"🛡️ **REPORTE DE ANÁLISIS**\n"
    reporte += f"────────────────\n\n"
    
    # A. Veredicto Fuente
    reporte += f"**Fuentes e Identidad:**\n"
    reporte += f"{emoji} **{estado}**\n"
    reporte += f"ℹ️ {msg_fuente}\n\n"

    # B. Análisis de Texto (NUEVO)
    if info_contenido and info_contenido["exito"]:
        reporte += f"**Análisis de Contenido:**\n"
        reporte += f"📰 **Título:** _{info_contenido['titulo']}_\n"
        
        # Semáforo de Clickbait
        score = info_contenido['clickbait_score']
        if score > 50:
            sem_click = "🔴 ALTO"
        elif score > 20:
            sem_click = "🟡 MEDIO"
        else:
            sem_click = "🟢 BAJO"
            
        reporte += f"🎣 **Nivel Clickbait:** {sem_click} ({score}%)\n"
        
        if info_contenido['etiquetas']:
            reporte += f"🏷️ **Alertas:** {', '.join(info_contenido['etiquetas'])}\n"
            
        reporte += f"📄 **Resumen:** {info_contenido['resumen']}\n\n"
    elif estado != "PELIGROSO":
        reporte += f"⚠️ **Contenido:** No se pudo extraer el texto (Sitio protegido o Paywall).\n\n"

    # C. Redirecciones (Si hubo)
    if len(historial) > 0:
        reporte += f"**Ruta Técnica:**\n"
        trace = "\n".join(historial[:3]) 
        reporte += f"`{trace}`\n"
    
    reporte += f"\n🔗 {url_final}"

    await update.message.reply_text(reporte, parse_mode='Markdown')
    
async def do_check_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, url_usuario: str):
    """Reutilizable: ejecuta el flujo de /check dado un URL y envía la respuesta al usuario."""
    await update.message.reply_text(f"🕵️‍♂️ **Analizando:** `{url_usuario}` ...", parse_mode='Markdown')

    url_final, historial = analizar_redirecciones(url_usuario)
    if not url_final:
        await update.message.reply_text(f"❌ Error: Sitio inaccesible.\n{historial[0]}")
        return

    estado, msg_fuente, emoji = verificar_fuente(url_final)

    info_contenido = None
    if estado != "PELIGROSO":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        info_contenido = analizar_contenido(url_final)

    reporte = f"🛡️ **REPORTE DE ANÁLISIS**\n"
    reporte += f"────────────────\n\n"
    reporte += f"**Fuentes e Identidad:**\n"
    reporte += f"{emoji} **{estado}**\n"
    reporte += f"ℹ️ {msg_fuente}\n\n"

    if info_contenido and info_contenido.get("exito"):
        reporte += f"**Análisis de Contenido:**\n"
        reporte += f"📰 **Título:** _{info_contenido['titulo']}_\n"
        score = info_contenido['clickbait_score']
        if score > 50:
            sem_click = "🔴 ALTO"
        elif score > 20:
            sem_click = "🟡 MEDIO"
        else:
            sem_click = "🟢 BAJO"
        reporte += f"🎣 **Nivel Clickbait:** {sem_click} ({score}%)\n"
        if info_contenido['etiquetas']:
            reporte += f"🏷️ **Alertas:** {', '.join(info_contenido['etiquetas'])}\n"
        reporte += f"📄 **Resumen:** {info_contenido['resumen']}\n\n"
    elif estado != "PELIGROSO":
        reporte += f"⚠️ **Contenido:** No se pudo extraer el texto (Sitio protegido o Paywall).\n\n"

    if len(historial) > 0:
        reporte += f"**Ruta Técnica:**\n"
        trace = "\n".join(historial[:3])
        reporte += f"`{trace}`\n"

    reporte += f"\n🔗 {url_final}"

    await update.message.reply_text(reporte, parse_mode='Markdown')


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detecta texto que parece una URL y la analiza automáticamente."""
    texto = update.message.text or ""
    # heurística simple: si tiene esquema o un punto y no es un comando
    if texto.startswith('/'):
        return
    if texto.startswith('http://') or texto.startswith('https://') or ('.' in texto and ' ' not in texto):
        await do_check_and_reply(update, context, texto.strip())
    else:
        await update.message.reply_text("❓ Envía una URL o usa /check <url>")
#Guardar búsquedas previas del usuario para acceso rápido.
async def historial_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from logicaBot import obtener_historial
    
    user_id = update.effective_user.id
    busquedas = obtener_historial(user_id)
    
    if not busquedas:
        await update.message.reply_text("📭 Sin historial aún")
        return
    
    msg = "📋 **Tu Historial:**\n"
    for i, item in enumerate(busquedas, 1):
        msg += f"{i}. {item['url']}\n"
    
    await update.message.reply_text(msg, parse_mode='Markdown')
    
    # Agregar botones para que usuarios naveguen sin escribir comandos.

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Analizar URL", callback_data='check_url')],
        [InlineKeyboardButton("📚 Tutorial", callback_data='tutorial')],
        [InlineKeyboardButton("⚙️ Configuración", callback_data='settings')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 Bienvenido a JackerCD-Fake New Bot\n\n¿Qué deseas hacer?",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'check_url':
        await query.edit_message_text(text="📎 Envíame la URL a analizar:")
    elif query.data == 'tutorial':
        await query.edit_message_text(text="📚 **Tutorial:**\n1. Envía `/check <url>`\n2. Espera el análisis\n...")



if __name__ == '__main__':
    if not TOKEN:
        print("❌ ERROR: Sin Token.")
    else:
        print("🧠 Cargando inteligencia...")
        inicializar_inteligencia()
        
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler('start', start))
        app.add_handler(CommandHandler('check', check))
        app.add_handler(CommandHandler('historial', historial_cmd))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
        
        print("🤖 JackerCD-Fake New Bot v2 corriendo...")
        app.run_polling()