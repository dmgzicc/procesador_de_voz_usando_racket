import tkinter as tk
from tkinter import ttk
import sounddevice as sd
import subprocess
import json
import threading
import queue
import sys
import os
import numpy as np

# Para graficar en Tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# --- CONFIGURACIÓN ---
# Ajusta esta ruta a tu instalación de Racket en Windows
RACKET_CMD = r"C:\Program Files\Racket\racket.exe" 
RACKET_SCRIPT = "voice-processor.rkt"

RATE = 44100
CHUNK = 4410 # 100ms

class AudioAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Procesador de señales (voz) - proyecto final (Racket)")
        self.root.geometry("800x600")
        
        # Estado del sistema
        self.is_running = False
        self.queue = queue.Queue() # Para comunicar Audio -> GUI
        
        # --- INTERFAZ GRÁFICA ---
        
        # 1. Título
        lbl_title = tk.Label(root, text="Análisis Espectral en tiempo Real", font=("Arial", 16, "bold"))
        lbl_title.pack(pady=10)

        # 2. Gráfica (Matplotlib embed)
        self.fig = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_ylim(0, 50) # Altura fija para evitar saltos
        self.ax.set_xlabel("Frecuencia")
        self.ax.set_title("Espectro FFT (desde Racket)")
        self.line, = self.ax.plot([], [], color="#fbff00", lw=1) # Línea verde estilo osciloscopio
        
        # Fondo negro para look "hacker"
        self.ax.set_facecolor('black')
        self.fig.patch.set_facecolor('#f0f0f0')

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 3. Etiqueta de Predicción (La parte clave)
        self.lbl_prediction = tk.Label(root, text="Esperando...", font=("Courier", 24, "bold"), fg="gray")
        self.lbl_prediction.pack(pady=20)
        
        self.lbl_stats = tk.Label(root, text="RMS: 0.000 | ZCR: 0", font=("Arial", 10))
        self.lbl_stats.pack(pady=5)

        # 4. Botón Start/Stop
        self.btn_toggle = tk.Button(root, text="INICIAR SISTEMA", command=self.toggle_audio, 
                                    bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), height=2, width=20)
        self.btn_toggle.pack(pady=20)

        # Iniciar el loop de actualización de GUI
        self.root.after(100, self.update_gui)

    def toggle_audio(self):
        if not self.is_running:
            self.is_running = True
            self.btn_toggle.config(text="DETENER SISTEMA", bg="#F44336")
            # Iniciar hilo de audio
            threading.Thread(target=self.audio_process_loop, daemon=True).start()
        else:
            self.is_running = False
            self.btn_toggle.config(text="INICIAR SISTEMA", bg="#4CAF50")
            self.lbl_prediction.config(text="Detenido", fg="gray")

    def audio_process_loop(self):
        # Iniciar subproceso Racket
        if not os.path.exists(RACKET_SCRIPT):
            print("Error: No encuentro el script Racket")
            return

        try:
            process = subprocess.Popen(
                [RACKET_CMD, RACKET_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=sys.stderr,
                text=True,
                bufsize=1
            )
        except Exception as e:
            print(f"Error lanzando Racket: {e}")
            return

        try:
            with sd.InputStream(samplerate=RATE, channels=1, blocksize=CHUNK, dtype='float32') as stream:
                while self.is_running:
                    # Leer audio
                    data, _ = stream.read(CHUNK)
                    data_list = data.flatten().tolist()
                    
                    # Enviar a Racket
                    try:
                        process.stdin.write(json.dumps(data_list) + "\n")
                        process.stdin.flush()
                        
                        # Leer respuesta
                        response = process.stdout.readline()
                        if response:
                            metrics = json.loads(response)
                            self.queue.put(metrics) # Enviar datos a la GUI
                    except (BrokenPipeError, json.JSONDecodeError):
                        break
        finally:
            process.terminate()

    def update_gui(self):
        # Revisar si hay nuevos datos en la cola
        try:
            # Sacar todos los datos pendientes (para no tener lag visual)
            data = None
            while not self.queue.empty():
                data = self.queue.get_nowait()
            
            if data:
                # 1. Actualizar Gráfica
                spectrum = data.get('spectrum', [])
                if spectrum:
                    # --- CAMBIO PARA CENTRAR EL ESPECTRO ---
                    
                    # Creamos un efecto espejo: invertimos la lista y la pegamos al principio
                    # Así tenemos: [Frecuencias Negativas] <--- 0 ---> [Frecuencias Positivas]
                    full_spectrum = spectrum[::-1] + spectrum 
                    
                    # El eje X ahora va desde -22050 Hz hasta +22050 Hz
                    half_freq = RATE / 2
                    x_data = np.linspace(-half_freq, half_freq, len(full_spectrum))
                    
                    # Actualizamos la línea con los datos centrados
                    self.line.set_data(x_data, full_spectrum)
                    
                    # Ajustamos los límites de la gráfica para que el 0 esté al centro
                    self.ax.set_xlim(-half_freq, half_freq)
                    
                    # Auto-escala Y (igual que antes)
                    self.ax.set_ylim(0, max(max(spectrum)*1.2, 10)) 
                    self.canvas.draw_idle()

                # 2. Actualizar Labels
                rms = data.get('rms', 0)
                zcr = data.get('zcr', 0)
                is_voice = data.get('is_voice', 0)
                is_peak = data.get('is_peak', 0)

                self.lbl_stats.config(text=f"RMS: {rms:.4f} | ZCR: {zcr}")

                if is_peak == 1:
                    self.lbl_prediction.config(text="GOLPE DETECTADO", fg="red")
                elif is_voice == 1:
                    self.lbl_prediction.config(text="VOZ HUMANA", fg="green")
                else:
                    self.lbl_prediction.config(text="... Escuchando ...", fg="black")

        except queue.Empty:
            pass
        
        # Volver a llamar a esta función en 50ms
        self.root.after(50, self.update_gui)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioAnalyzerGUI(root)
    root.mainloop()