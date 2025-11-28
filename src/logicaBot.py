import requests
import json
import os
from urllib.parse import urlparse

# --- MEMORIA CACHÉ (Variables Globales) ---
# Guardamos los datos en memoria para no leer el archivo o descargar de internet en cada mensaje
CACHE_BLACKLIST_EXTERNA = set()
CACHE_MEDIOS_LOCAL = {}
YA_CARGADO = False

def inicializar_inteligencia():
    """
    Esta función se ejecuta UNA VEZ al iniciar el bot.
    1. Carga la lista blanca/negra de Chile desde el archivo JSON.
    2. Descarga la lista de Phishing mundial desde OpenPhish.
    """
    global CACHE_BLACKLIST_EXTERNA, CACHE_MEDIOS_LOCAL, YA_CARGADO
    
    if YA_CARGADO: 
        return # Si ya se cargó, no hacemos nada

    print("🔄 Inicializando motores de inteligencia...")

    # 1. Cargar JSON Local (Chile)
    ruta_json = os.path.join(os.path.dirname(__file__), '..', 'data', 'medios.json')
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            CACHE_MEDIOS_LOCAL = json.load(f)
        print(f"✅ Base de datos local cargada (Chile): {len(CACHE_MEDIOS_LOCAL.get('whitelist', []))} medios confiables.")
    except FileNotFoundError:
        print("⚠️ Advertencia: No se encontró 'data/medios.json'. Se usará memoria vacía para Chile.")
        CACHE_MEDIOS_LOCAL = {"whitelist": [], "blacklist": [], "satire": []}

    # 2. Cargar Feeds Externos (Automático)
    # Usamos OpenPhish (Gratuito, actualiza cada hora)
    url_feed = "https://openphish.com/feed.txt"
    try:
        print("🌍 Conectando con OpenPhish Feed para amenazas globales...")
        response = requests.get(url_feed, timeout=5)
        
        if response.status_code == 200:
            count = 0
            for linea in response.text.splitlines():
                # Limpiamos y extraemos dominio
                d = extraer_dominio(linea)
                if d: 
                    CACHE_BLACKLIST_EXTERNA.add(d)
                    count += 1
            print(f"✅ Base de datos global actualizada: {count} dominios de phishing importados.")
        else:
            print(f"⚠️ Error al descargar feed externo: Status {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Modo Offline: No se pudo cargar feed externo ({e}). Solo funcionará la base local.")

    YA_CARGADO = True

def extraer_dominio(url):
    """Limpia la URL para obtener solo el dominio principal (ej: biobiochile.cl)"""
    try:
        # Asegurar protocolo para que urlparse funcione bien
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Quitamos 'www.' si existe para estandarizar
        if domain.startswith("www."):
            domain = domain[4:]
            
        return domain.lower()
    except:
        return ""

def analizar_redirecciones(url_sospechosa):
    """
    Recibe una URL, sigue todos los saltos (redirecciones) y retorna:
    1. La URL final de destino.
    2. Una lista con el historial de saltos (Traza).
    """
    if not url_sospechosa.startswith(('http://', 'https://')):
        url_sospechosa = 'http://' + url_sospechosa

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # HEAD request es más rápido que GET porque no baja el cuerpo del sitio
        response = requests.head(url_sospechosa, allow_redirects=True, headers=headers, timeout=10)
        
        historial = []
        if response.history:
            for resp in response.history:
                historial.append(f"🔄 {resp.status_code} -> {resp.url}")
        
        url_final = response.url
        return url_final, historial

    except Exception as e:
        return None, [f"❌ Error de conexión: {str(e)}"]

def verificar_fuente(url):
    """
    Analiza si el dominio pertenece a listas conocidas (Local o Global).
    Retorna: (Estado, Mensaje, Emoji)
    """
    # Seguridad: Si por alguna razón no se inicializó antes, hacerlo ahora.
    if not YA_CARGADO:
        inicializar_inteligencia()

    dominio = extraer_dominio(url)
    
    if not dominio:
        return "ERROR", "No se pudo detectar el dominio", "❓"

    # 1. Chequeo Local (Prioridad: Medios Chilenos)
    if dominio in CACHE_MEDIOS_LOCAL.get("whitelist", []):
        return "CONFIABLE", f"Fuente chilena verificada: {dominio}", "✅"
    
    if dominio in CACHE_MEDIOS_LOCAL.get("blacklist", []):
        # Diferenciamos sátira de fake news maliciosa
        if dominio in CACHE_MEDIOS_LOCAL.get("satire", []):
            return "SÁTIRA / HUMOR", f"Sitio de parodia conocido: {dominio}", "🤡"
        return "NO CONFIABLE", f"Sitio en lista negra local: {dominio}", "⛔"

    # 2. Chequeo Global (OpenPhish - Phishing Reciente)
    if dominio in CACHE_BLACKLIST_EXTERNA:
        return "PELIGROSO", "Detectado en bases de datos internacionales de Phishing (Robo de datos)", "💀"

    # 3. Sin registros
    return "DESCONOCIDO", f"No registrado en bases de datos ({dominio}). Analizar con precaución.", "⚠️"