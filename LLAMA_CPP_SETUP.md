#  Dispatch Agent + llama.cpp Backend

> ⚠️ **Disclaimer:** Esta es una adaptación comunitaria proporcionada "tal cual" (as-is). No está afiliada al repositorio oficial. No se garantizará mantenimiento a largo plazo; está pensada como una opción base para que la comunidad o los mantenedores originales la integren, ajusten o descarten según convenga.

## 📖 ¿Qué hace esta adaptación?
Reemplaza la dependencia de **Ollama** por **`llama-server` (llama.cpp)**.  
El agente se comunica mediante la API estándar compatible con OpenAI (`http://127.0.0.1:8080/v1`), lo que permite usar **cualquier modelo en formato `.gguf`** que soporte chat, llamadas a herramientas y razonamiento, sin instalar el daemon de Ollama.

## 🛠️ Requisitos Previos
| Componente | Requisito | Notas |
|------------|-----------|-------|
| **Python** | `3.10+` | Para ejecutar el agente |
| **llama.cpp** | Binarios compilados | Necesitas `llama-server.exe` |
| **Modelo** | `.gguf` (Q4_K_M recomendado) | Debe tener template de chat compatible |
| **Dispatch** | Repositorio original | Se modificarán archivos del núcleo |

## 📦 Instalación y Configuración

### 1️⃣ Instalar dependencias ligeras
```powershell
pip install requests typer rich prompt_toolkit httpx psutil duckduckgo-search trafilatura
```

### 2️ Configurar el Servidor Local
Usa `run_server.bat` (incluido en este fork) o crea uno con esta estructura:
```bat
llama-server.exe -m .\models\TU_MODELO.gguf -c 16384 -ngl 0 --host 127.0.0.1 --port 8080 --temp 0.6 --top-p 0.95 --repeat-penalty 1.1 --mmap
```
✅ `llama-server` expone automáticamente la API en `http://127.0.0.1:8080/v1`.

### 3️⃣ Reemplazar archivos del agente
Sustituye estos archivos en `dispatch/agent/` con las versiones de este fork:
- `agent/tools/session.py` → Compactación de contexto vía HTTP local
- `agent/cmd/arg_completers.py` → Lee modelo desde `config.json`
- `agent/cmd/plan.py` → Planificación y tool calling vía streaming SSE
- `agent/tools/web.py` → Import actualizado para `duckduckgo-search` v8+
- `agent/tools/__init__.py` → Reactiva módulos `web` y `shell`

*(Nota: Si el proyecto usa un adaptador LLM centralizado, aplica la lógica de reemplazo de `ollama.chat()` por `requests.post()` a `127.0.0.1:8080/v1/chat/completions`)*.

### 4️⃣ Actualizar `config.json`
```json
{
  "model": "GGUF-Local",
  "model_path": "Ruta/A/TU_MODELO.gguf",
  "context_limit": 16384,
  "auto_compact_tools": true,
  "server_url": "http://127.0.0.1:8080/v1"
}
```
> 🔍 `model_path` es referencial. El agente se conecta al servidor en ejecución, no carga el `.gguf` directamente.

## 🚀 Uso Básico
```powershell
# Terminal 1: Motor
.\run_server.bat
# Espera: "llama-server: listening on 127.0.0.1:8080"

# Terminal 2: Agente
dispatch-agent   # o python -m agent.main

# Verificación
/ctx info
/tools
Hola, ¿funciona la conexión local?
```

## 🧩 Compatibilidad y Hardware
| Característica | Requisito | Notas |
|----------------|-----------|-------|
| **Formato** | `.gguf` (Q4/Q5) | HuggingFace → Files & versions |
| **Chat Template** | Compatible OpenAI/ChatML | Auto-detectado por `llama-server` |
| **Tool Calling** | Soporte JSON Schema | Qwen2.5/3, Llama3.1+, Phi-3.5 nativos |
| **Razonamiento** | Tags `<think>` | Activa `--reasoning on` en el servidor |
| **RAM mínima** | ~4GB libres + CPU 4 núcleos | Modelos 3B Q4_K_M corren estables |

## 🧹 Desinstalación Limpia
```powershell
# 1. Borrar agente y motor
rmdir /s /q "ruta\dispatch"
rmdir /s /q "ruta\Llama.cpp"

# 2. Eliminar lanzador global (si existe)
del "%USERPROFILE%\AppData\Local\Programs\Python\Python314\Scripts\dispatch-agent.bat"

# 3. Desinstalar paquetes
pip uninstall -y requests typer rich prompt_toolkit httpx psutil duckduckgo-search trafilatura
```

## 📝 Notas para Mantenedores
- **Zero Ollama:** Elimina la dependencia externa. Usa solo `requests` + API estándar.
- **Drop-in:** Los archivos reemplazan directamente los originales sin romper la estructura.
- **Multi-modelo:** Funciona con cualquier `.gguf`. Solo se cambia la línea `-m` en el `.bat`.
- **Sugerencia de integración:** Podrías añadir un flag `--backend llama-cpp` que cargue este adaptador opcionalmente, manteniendo ambos backends.
- **Licencia:** Código entregado sin restricciones. Úsalo, modifícalo o intégralo como consideres.
```