@echo off
REM 🟢 Dispatch Agent - Servidor llama.cpp
REM ==========================================
REM Instrucciones:
REM 1. Asegúrate de tener llama-server.exe en esta carpeta.
REM 2. Pon tu modelo .gguf en la carpeta "models".
REM 3. Cambia "TU_MODELO.gguf" por el nombre real de tu archivo.
REM 4. Si tienes GPU NVIDIA, cambia "-ngl 0" a "-ngl 99".

echo.
echo  Iniciando servidor llama.cpp para Dispatch Agent...
echo 🌐 API: http://127.0.0.1:8080/v1
echo.

REM --- CONFIGURACIÓN ---
REM -m: Ruta del modelo
REM -c: Contexto (16384 es estándar, usa 8192 si tienes poca RAM)
REM -ngl: 0 para CPU, 99 para GPU (NVIDIA)
REM --temp: Creatividad (0.6 es equilibrado para agentes)

llama-server.exe ^
-m .\models\TU_MODELO.gguf ^
-c 16384 ^
-ngl 0 ^
--host 127.0.0.1 ^
--port 8080 ^
--temp 0.6 ^
--top-p 0.95 ^
--repeat-penalty 1.1 ^
--cache-type-k q4_0 ^
--cache-type-v q4_0 ^
--mmap

echo.
echo ⏹️ Servidor detenido.
pause