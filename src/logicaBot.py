import requests

def analizar_redirecciones(url_sospechosa):
    """
    Recibe una URL, sigue todos los saltos (redirecciones) y retorna:
    1. La URL final de destino.
    2. Una lista con el historial de saltos (Traza).
    """
    # Si el usuario olvidó poner http/https, lo agregamos (usabilidad)
    if not url_sospechosa.startswith(('http://', 'https://')):
        url_sospechosa = 'http://' + url_sospechosa

    # User-Agent para parecer un navegador real y no un bot (Evita bloqueos básicos)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # allow_redirects=True es la clave aquí
        response = requests.head(url_sospechosa, allow_redirects=True, headers=headers, timeout=10)
        
        historial = []
        
        # Guardamos la ruta que siguió el link
        if response.history:
            for resp in response.history:
                historial.append(f"🔄 {resp.status_code} -> {resp.url}")
        
        url_final = response.url
        return url_final, historial

    except Exception as e:
        # Si falla (ej: dominio no existe), devolvemos None
        return None, [f"❌ Error de conexión: {str(e)}"]