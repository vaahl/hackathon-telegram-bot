import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **VerificaChile Bot v2.0**\n\n"
        "Ahora con Inteligencia Artificial básica para leer noticias.\n"
        "Envíame un link para:\n"
        "1. Detectar Phishing/Redirecciones\n"
        "2. Verificar la Fuente\n"
        "3. Analizar Clickbait y Contenido\n\n"
        "Ejemplo: `/check https://noticia-ejemplo.cl`",
        parse_mode='Markdown'
    )

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

if __name__ == '__main__':
    if not TOKEN:
        print("❌ ERROR: Sin Token.")
    else:
        print("🧠 Cargando inteligencia...")
        inicializar_inteligencia()
        
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler('start', start))
        app.add_handler(CommandHandler('check', check))
        
        print("🤖 VerificaChile Bot v2 corriendo...")
        app.run_polling()