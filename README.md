# Procesador de Señales Digitales (Paradigma Funcional)

Este proyecto implementa un sistema de análisis de audio en tiempo real capaz de discriminar entre Voz Humana y Golpes Secos (percusiones).

Combina la versatilidad de Python para la captura de audio y visualización, con la robustez matemática de Racket para el procesamiento de señales bajo el Paradigma Funcional.

## Características Principales

- **Arquitectura**
  - **Python (Cliente):** Interfaz gráfica (Tkinter), captura de micrófono (SoundDevice) y visualización (Matplotlib).
  - **Racket (Núcleo):** Procesamiento matemático puro.
- **Paradigma Funcional Estricto:** El núcleo de procesamiento en Racket utiliza recursividad, inmutabilidad y funciones de orden superior.
- **FFT Manual:** Implementación propia del algoritmo Cooley-Tukey para la Transformada Rápida de Fourier (sin librerías externas).
- **Análisis Espectral:** Visualización en tiempo real del espectro de frecuencias centrado.
- **Discriminación Inteligente:** Algoritmo basado en Energía (RMS) y Tasa de Cruce por Cero (ZCR) para diferenciar vocales de ruidos percusivos.

## Requisitos Previos

### Software
1. Python 3.10 o superior.
2. Racket (Debe estar instalado en el sistema).

### Librerías de Python
Ejecuta el siguiente comando para instalar las dependencias necesarias:

pip install sounddevice numpy matplotlib

(Nota: En Linux/Debian, podría requerirse instalar 'libportaudio2' desde el gestor de paquetes del sistema).

## Configuración

Antes de ejecutar, asegúrate de que Python sepa dónde está instalado Racket.

1. Abre el archivo 'main_gui.py'.
2. Busca la variable 'RACKET_CMD' y ajusta la ruta según tu sistema operativo:

# Ejemplo para Windows
RACKET_CMD = r"C:\Program Files\Racket\racket.exe"

# Ejemplo para Linux
RACKET_CMD = "racket"

## Ejecución

Para iniciar la interfaz gráfica:

python main_gui.py

1. Se abrirá la ventana de control.
2. Presiona el botón "INICIAR SISTEMA".
3. Habla o aplaude cerca del micrófono para ver la clasificación en tiempo real.

## Lógica de Funcionamiento

El sistema funciona mediante un Pipeline de Comunicación vía JSON:

1. Python captura un bloque de audio (100ms / 4410 muestras).
2. Los datos crudos se envían a través de la entrada estándar (stdin) al proceso de Racket.
3. Racket calcula:
   - RMS (Root Mean Square): Para determinar el volumen/energía.
   - ZCR (Zero Crossing Rate): Para determinar la rugosidad de la señal.
   - FFT (Fast Fourier Transform): Recursivamente para obtener el espectro.
4. Racket devuelve un JSON con las métricas y el espectro calculado.
5. Python recibe los datos, actualiza la gráfica y muestra la etiqueta correspondiente (Voz vs Golpe).

## Estructura del Proyecto

- main_gui.py: Script principal. Maneja la GUI, Hilos y Audio.
- voice-processor.rkt: Script de Racket. Contiene toda la lógica matemática funcional.

---
Autor: Diego Domínguez Palacios
Materia: Lenguajes de programación
Fecha: 29 de noviembre del 2025