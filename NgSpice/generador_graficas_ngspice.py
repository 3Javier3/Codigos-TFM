import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

archivo = "resultados_ngspice.txt"

try:
    # Leer datos del archivo
    # Col 0: Voltaje, Col 1: Corriente
    df = pd.read_csv(archivo, sep=r"\s+", header=None)
    
    V = df[0].values
    I = -df[1].values

    # Solo nos interesan los puntos donde la corriente es positiva
    indices_validos = I >= 0
    V = V[indices_validos]
    I = I[indices_validos]

    P = V * I # Potencia generada
    
    # Encontrar el Punto de potencia mas alto
    indice_max_potencia = np.argmax(P)
    v_mp, p_max = V[indice_max_potencia], P[indice_max_potencia]

    # Graficar
    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(V, I, 'tab:blue', label='Corriente (I-V)', linewidth=2.5)
    ax1.set_xlabel('Voltaje (V)')
    ax1.set_ylabel('Corriente (A)', color='tab:blue')
    ax1.grid(True, linestyle='--', alpha=0.5)

    ax2 = ax1.twinx()
    ax2.plot(V, P, 'tab:red', label='Potencia (P-V)', linestyle='--', linewidth=2)
    ax2.set_ylabel('Potencia (W)', color='tab:red')

    ax2.scatter(v_mp, p_max, color='black', s=80, zorder=5)
    ax2.annotate(f'MP: {p_max:.3f}W', 
                 xy=(v_mp, p_max), 
                 xytext=(v_mp-0.2, p_max-0.4),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1))

    plt.title('Curvas I-V y P-V Ngspice')
    plt.savefig('celula_fotovoltaica_ngspice.png', dpi=300)
    plt.show()

except Exception as e:
    print(f"Error: {e}")