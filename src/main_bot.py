import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
# IMPORTAMOS NUESTRA LÓGICA
from logicaBot import analizar_redirecciones

# Cargar entorno
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
TOKEN = os.getenv('TELEGRAM_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Soy VerificaChile.\n\n"
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
    await update.message.reply_text(f"🕵️‍♂️ Analizando redirecciones de: `{url_usuario}` ...", parse_mode='Markdown')

    # 2. LLAMAR AL CEREBRO (logic.py)
    # Ejecutamos la función que creamos en el otro archivo
    url_final, historial = analizar_redirecciones(url_usuario)

    # 3. Construir la respuesta
    if url_final:
        mensaje = f"✅ **Análisis completado**\n\n"
        
        if historial:
            mensaje += "🔄 **Redirecciones detectadas:**\n" + "\n".join(historial) + "\n\n"
        else:
            mensaje += "➡️ **Acceso Directo:** No hubo redirecciones ocultas.\n\n"
            
        mensaje += f"🏁 **Destino Final:** `{url_final}`"
        
        # Alerta visual si el destino es diferente al original
        if url_usuario not in url_final and len(historial) > 0:
            mensaje += "\n\n⚠️ **ADVERTENCIA:** El link original estaba enmascarado."
            
    else:
        mensaje = f"❌ No se pudo acceder al sitio.\nError: {historial[0]}"

    await update.message.reply_text(mensaje, parse_mode='Markdown')

if __name__ == '__main__':
    if not TOKEN:
        print("❌ ERROR: Falta el token.")
    else:
        application = ApplicationBuilder().token(TOKEN).build()
        
        # Agregamos los comandos
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('check', check))
        
        print("🤖 VerificaChile Bot corriendo...")
        application.run_polling()