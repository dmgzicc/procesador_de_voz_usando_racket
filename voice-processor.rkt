#lang racket

(require json)

;; --- CONSTANTES ---
(define RMS-THRESHOLD 0.015)   ; Umbral de silencio
(define ZCR-THRESHOLD 120)     ; Umbral de cruces por cero 
(define PEAK-THRESHOLD 0.06)   ; Umbral de volumen para considerar algo "Fuerte"
(define FFT-SIZE 512)          ; Tamaño de ventana para el espectro

;; --- FFT MANUAL (Algoritmo Cooley-Tukey Funcional) ---
;; Implementación sin math/fft
(define (pure-fft input-vector)
  (define n (vector-length input-vector))
  (if (= n 1)
      input-vector
      (let* ([half (quotient n 2)]
             [evens (build-vector half (lambda (i) (vector-ref input-vector (* 2 i))))]
             [odds  (build-vector half (lambda (i) (vector-ref input-vector (+ (* 2 i) 1))))]
             [even-fft (pure-fft evens)]
             [odd-fft  (pure-fft odds)])
        (build-vector n
          (lambda (k)
            (if (< k half)
                (let* ([angle (* -2.0 pi (/ k n))]
                       [w (make-polar 1.0 angle)]
                       [e (vector-ref even-fft k)]
                       [o (vector-ref odd-fft k)])
                  (+ e (* w o)))
                (let* ([k2 (- k half)]
                       [angle (* -2.0 pi (/ k2 n))]
                       [w (make-polar 1.0 angle)]
                       [e (vector-ref even-fft k2)]
                       [o (vector-ref odd-fft k2)])
                  (- e (* w o)))))))))

;; --- FUNCIONES DE ANÁLISIS ---

(define (calculate-rms signal-list)
  (if (empty? signal-list) 0.0
      (let ([squared-sum (foldl (lambda (x acc) (+ acc (* x x))) 0.0 signal-list)])
        (sqrt (/ squared-sum (length signal-list))))))

(define (calculate-zcr signal-list)
  (if (or (empty? signal-list) (< (length signal-list) 2)) 0
      (let loop ([lst (cdr signal-list)] [prev (car signal-list)] [count 0])
        (if (empty? lst) count
            (let ([curr (car lst)])
              (if (< (* curr prev) 0) 
                  (loop (cdr lst) curr (+ count 1))
                  (loop (cdr lst) curr count)))))))

;; LÓGICA DE DETECCIÓN
;; Voz: 
(define (detect-voice rms zcr) 
  (if (and (> rms RMS-THRESHOLD) (< zcr ZCR-THRESHOLD)) 1 0))

;; Posible golpe
(define (detect-loud-peak rms) 
  (if (> rms PEAK-THRESHOLD) 1 0))

;; Helper para preparar vector FFT
(define (prepare-fft-vector data-list size)
  (let ([vec (list->vector (map (lambda (x) (make-rectangular x 0.0)) data-list))]
        [len (length data-list)])
    (if (> len size) (vector-take vec size) (vector-append vec (make-vector (- size len) 0.0+0.0i)))))

;; --- LOOP PRINCIPAL ---
(define (process-loop)
  (let ([input-data (read-json)])
    (unless (eof-object? input-data)
      
      ;; 1. Calcular métricas básicas
      (define rms (calculate-rms input-data))
      (define zcr (calculate-zcr input-data))
      
      ;; 2. Calcular Espectro (Para la gráfica)
      (define fft-input (prepare-fft-vector input-data FFT-SIZE))
      (define spectrum-complex (pure-fft fft-input))
      ;; Tomamos magnitud de la primera mitad
      (define spectrum-mags 
        (map magnitude (vector->list (vector-take spectrum-complex (quotient FFT-SIZE 2)))))

      ;; 3. Lógica de Decisión
      (define is_voice (detect-voice rms zcr))
      (define is_loud (detect-loud-peak rms))
      
      (define final_is_peak 
        (if (and (= is_loud 1) (= is_voice 0)) 
            1 
            0))

      ;; 4. Empaquetar y enviar
      (define result (hasheq 'rms rms 
                             'zcr zcr 
                             'is_voice is_voice 
                             'is_peak final_is_peak 
                             'spectrum spectrum-mags))
      
      (write-json result) 
      (newline) 
      (flush-output)
      
      (process-loop))))

(process-loop)