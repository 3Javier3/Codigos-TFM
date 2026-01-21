import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Cargar los datos de ngspice
archivo = "resultados_ngspice.txt"

try:
    # 1. Leer datos (ngspice separa por espacios)
    # Col 0: Voltaje, Col 1: Corriente (suele ser negativa en SPICE)
    df = pd.read_csv(archivo, sep=r"\s+", header=None)
    
    V = df[0].values
    I = -df[1].values # Invertimos para que la generación sea positiva
    
    # --- FILTRO CRÍTICO ---
    # Solo nos interesan los puntos donde la corriente es positiva (Generación)
    indices_validos = I >= 0
    V = V[indices_validos]
    I = I[indices_validos]
    P = V * I # Potencia generada real
    
    # 2. Encontrar el MPP real
    idx_mpp = np.argmax(P)
    v_mpp, p_max = V[idx_mpp], P[idx_mpp]

    # 3. Graficar
    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(V, I, 'tab:blue', label='Corriente (I-V)', linewidth=2.5)
    ax1.set_xlabel('Voltaje (V)')
    ax1.set_ylabel('Corriente (A)', color='tab:blue')
    ax1.grid(True, linestyle='--', alpha=0.5)

    ax2 = ax1.twinx()
    ax2.plot(V, P, 'tab:red', label='Potencia (P-V)', linestyle='--', linewidth=2)
    ax2.set_ylabel('Potencia (W)', color='tab:red')

    # Marcar el MPP real sin el pico de error
    ax2.scatter(v_mpp, p_max, color='black', s=80, zorder=5)
    ax2.annotate(f'MPP: {p_max:.3f}W', 
                 xy=(v_mpp, p_max), 
                 xytext=(v_mpp-0.2, p_max-0.4),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1))

    plt.title('Curvas Fotovoltaicas Limpias (Sin efectos de polarización directa)')
    plt.savefig('grafica_final_limpia.png', dpi=300)
    plt.show()

except Exception as e:
    print(f"Error: {e}")