import requests
import json
import os
from urllib.parse import urlparse
from newspaper import Article, Config # IMPORTACIÓN NUEVA

# --- MEMORIA CACHÉ (Variables Globales) ---
CACHE_BLACKLIST_EXTERNA = set()
CACHE_MEDIOS_LOCAL = {}
YA_CARGADO = False

def inicializar_inteligencia():
    """Carga listas locales y descarga listas globales al iniciar."""
    global CACHE_BLACKLIST_EXTERNA, CACHE_MEDIOS_LOCAL, YA_CARGADO
    if YA_CARGADO: return 

    print("🔄 Inicializando motores de inteligencia...")

    # 1. Cargar JSON Local
    ruta_json = os.path.join(os.path.dirname(__file__), '..', 'data', 'medios.json')
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            CACHE_MEDIOS_LOCAL = json.load(f)
        print(f"✅ Base local cargada: {len(CACHE_MEDIOS_LOCAL.get('whitelist', []))} medios.")
    except FileNotFoundError:
        CACHE_MEDIOS_LOCAL = {"whitelist": [], "blacklist": [], "satire": []}

    # 2. Cargar Feeds Externos
    url_feed = "https://openphish.com/feed.txt"
    try:
        print("🌍 Descargando amenazas globales (OpenPhish)...")
        response = requests.get(url_feed, timeout=5)
        if response.status_code == 200:
            for linea in response.text.splitlines():
                d = extraer_dominio(linea)
                if d: CACHE_BLACKLIST_EXTERNA.add(d)
            print(f"✅ Base global actualizada.")
    except Exception as e:
        print(f"⚠️ Modo Offline (Global): {e}")

    YA_CARGADO = True

def extraer_dominio(url):
    try:
        if not url.startswith(('http://', 'https://')): url = 'http://' + url
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."): domain = domain[4:]
        return domain.lower()
    except:
        return ""

def analizar_redirecciones(url_sospechosa):
    if not url_sospechosa.startswith(('http://', 'https://')):
        url_sospechosa = 'http://' + url_sospechosa
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.head(url_sospechosa, allow_redirects=True, headers=headers, timeout=5)
        historial = [f"🔄 {r.status_code} -> {r.url}" for r in response.history]
        return response.url, historial
    except Exception as e:
        return None, [f"Error: {str(e)}"]

def verificar_fuente(url):
    if not YA_CARGADO: inicializar_inteligencia()
    dominio = extraer_dominio(url)
    if not dominio: return "ERROR", "Dominio inválido", "❓"

    if dominio in CACHE_MEDIOS_LOCAL.get("whitelist", []):
        return "CONFIABLE", f"Fuente reconocida: {dominio}", "✅"
    if dominio in CACHE_MEDIOS_LOCAL.get("blacklist", []):
        if dominio in CACHE_MEDIOS_LOCAL.get("satire", []):
            return "SÁTIRA", f"Sitio de parodia: {dominio}", "🤡"
        return "NO CONFIABLE", f"Lista negra local: {dominio}", "⛔"
    if dominio in CACHE_BLACKLIST_EXTERNA:
        return "PELIGROSO", "Sitio de Phishing Global", "💀"
    return "DESCONOCIDO", f"Fuente no registrada: {dominio}", "⚠️"

# --- NUEVA FUNCIÓN: ANÁLISIS DE CONTENIDO (NLP) ---
def analizar_contenido(url):
    """
    Descarga la noticia y busca patrones de Clickbait y Sensacionalismo.
    """
    resultado = {
        "titulo": "No detectado",
        "resumen": "",
        "clickbait_score": 0, # 0 a 100
        "etiquetas": [],
        "exito": False
    }

    try:
        # Configuración para evitar bloqueos (User-Agent real)
        conf = Config()
        conf.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        conf.request_timeout = 10

        article = Article(url, config=conf)
        article.download()
        article.parse()

        resultado["titulo"] = article.title
        resultado["resumen"] = article.text[:200] + "..." if article.text else "Sin texto extraíble."
        resultado["exito"] = True

        # --- LÓGICA DE DETECCIÓN DE CLICKBAIT ---
        score = 0
        titulo_upper = article.title.upper()

        # 1. Gritos (Exceso de Mayúsculas en título)
        mayusculas = sum(1 for c in article.title if c.isupper())
        total = len(article.title)
        if total > 0 and (mayusculas / total) > 0.4: # Más del 40% es mayúscula
            score += 40
            resultado["etiquetas"].append("🗣️ GRITOS (Mayúsculas)")

        # 2. Palabras Gatillo (Contexto Chileno/Sensacionalista)
        palabras_alarma = ["URGENTE", "IMPACTO", "SECRETO", "CENSURA", "INCREIBLE", "MILAGRO", "FINALMENTE", "SHOCK"]
        for p in palabras_alarma:
            if p in titulo_upper:
                score += 15
                resultado["etiquetas"].append(f"⚠️ Palabra: {p}")

        # 3. Puntuación excesiva
        if "!!" in article.title or "??" in article.title:
            score += 20
            resultado["etiquetas"].append("⁉️ Puntuación Excesiva")

        resultado["clickbait_score"] = min(score, 100) # Tope 100%

        return resultado

    except Exception as e:
        print(f"Error scraping: {e}")
        return resultado # Devuelve exito=False