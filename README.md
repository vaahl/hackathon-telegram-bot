# JackerCD-Fake New — Bot de Telegram

Bot para analizar redirecciones de URLs y detectar enlaces potencialmente peligrosos (proyecto de hackathon).

## 📋 Contenido

- `src/main_bot.py` — Punto de entrada del bot
- `src/logicaBot.py` — Lógica para seguir redirecciones y verificar URLs
- `requirements.txt` — Dependencias del proyecto
- `.env` — Variables de entorno (token del bot)

## 🔧 Requisitos

- **Python 3.11+** (probado con Python 3.14)
- **PowerShell** en Windows (para instrucciones de activación)
- **pip** y **virtualenv** (incluidos en Python por defecto)

## 📦 Instalación

### 1. Clonar o descargar el repositorio

```powershell
git clone https://github.com/vaahl/hackathon-telegram-bot
cd C:\Users\userpc\Desktop\hackathon-telegram-bot
```

### 2. Crear el entorno virtual

```powershell
python -m venv .venv
```

### 3. Activar el entorno virtual

En **PowerShell**:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
. .\.venv\Scripts\Activate.ps1
```

En **cmd.exe**:

```cmd
.venv\Scripts\activate.bat
```

### 4. Instalar dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configurar el token de Telegram

Crea o edita el archivo `.env` en la raíz del proyecto:

```
TELEGRAM_TOKEN=TU_TOKEN_AQUI
```

Reemplaza `TU_TOKEN_AQUI` con el token que obtuviste de [@BotFather](https://t.me/botfather) en Telegram.

**⚠️ Seguridad**: Nunca compartas tu token públicamente. Si crees que se filtró, revócalo en BotFather y genera uno nuevo.

## 🚀 Ejecución

Con el entorno virtual activado y `.env` configurado:

```powershell
python src\main_bot.py
```

Deberías ver en consola:

```
🤖 VerificaChile Bot corriendo...
```

## 🧩 Interactividad y comandos

1. **Botones interactivos** — Al enviar `/start` verás un teclado inline con opciones (por ejemplo, "🔍 Analizar URL", "📚 Tutorial"). Pulsa el botón para que el bot te indique el siguiente paso.

2. **Entrada inline (detección automática)** — Si pegas o escribes directamente una URL en el chat (por ejemplo `https://ejemplo.cl` o `bit.ly/xxx`), el bot la detecta automáticamente y ejecuta el análisis sin necesidad de usar `/check`.

3. **Comandos disponibles**:
- `/start` — Mostrar el menú con botones interactivos.
- `/check <url>` — Forzar análisis de una URL.
- `/historial` — (Experimental) Mostrar búsquedas previas del usuario si se ha configurado el almacenamiento local.

Ejemplos de uso:
```
/start
/check https://bit.ly/ejemplo
```

Qué muestra el bot:
- Redirecciones detectadas
- URL destino final
- Advertencias si el link fue enmascarado
 

## 🔍 Funcionalidades

- **Análisis de redirecciones**: Sigue todos los saltos HTTP (301, 302, etc.)
- **Detección de enlaces enmascarados**: Alerta si la URL original difiere del destino
- **User-Agent personalizado**: Evita bloqueos básicos de bots
- **Manejo de errores**: Reporta problemas de conexión de forma clara

## ⚙️ Solución de problemas

### Error: "Falta el token en el archivo .env"
- Verifica que el archivo `.env` esté en la raíz del proyecto (no en carpeta padre)
- Comprueba que la variable se llame exactamente `TELEGRAM_TOKEN`
- Ejemplo correcto:
  ```
  TELEGRAM_TOKEN="Token"
  ```

### Error: "No module named 'dotenv'"
- Asegúrate de tener el venv activado
- Reinstala las dependencias:
  ```powershell
  pip install -r requirements.txt
  ```

### PowerShell no ejecuta scripts
- Ejecuta primero:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```
- Luego activa el venv

### Problemas con caracteres Unicode (emojis)
- En PowerShell, configura UTF-8:
  ```powershell
  $env:PYTHONIOENCODING='utf-8'
  python src\main_bot.py
  ```

## 📝 Estructura del código

### `main_bot.py`
- Configura los comandos `/start` y `/check`
- Maneja la comunicación con Telegram
- Responde con análisis formateados

### `logicaBot.py`
- `analizar_redirecciones(url)`: Sigue redirecciones y retorna URL final + historial
- `verificar_fuente(url)`: Verifica información de la fuente (en desarrollo)
- `inicializar_inteligencia()`: Inicializa modelos de IA (en desarrollo)

## 🔐 Consideraciones de seguridad

- **Token**: No lo compartas ni lo subas a repositorios públicos
- **`.env`**: Añade `.env` al `.gitignore` antes de hacer commit
- **URLs**: El bot usa `requests.head()` con timeout de 10 segundos

## 🚧 Próximas mejoras

- [ ] Integración con base de datos de URLs maliciosas
- [ ] Análisis del contenido de la página de destino
- [ ] Historial de búsquedas por usuario
- [ ] Sistema de reporte de URLs sospechosas

## 📞 Soporte

Si encuentras problemas:
1. Verifica los logs de consola
2. Comprueba que todas las dependencias estén instaladas
3. Asegúrate de que el token es válido en BotFather

---

**Versión**: 1.0  
**Última actualización**: 28 de noviembre de 2025
