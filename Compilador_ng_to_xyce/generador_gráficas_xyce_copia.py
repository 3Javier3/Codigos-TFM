import pandas as pd
import matplotlib.pyplot as plt

# Archivo de datos de Xyce
file_name = "Celula_convertida.cir.prn"

try:
    # 1. Cargar datos
    df = pd.read_csv(file_name, sep=r"\s+", skiprows=1, on_bad_lines='skip', engine='python')
    
    # Identificar columnas: V es la segunda, I es la tercera
    V = df.iloc[:, 1]
    I = df.iloc[:, 2]
    
    # 2. Calcular Potencia (P = V * I)
    P = V * I
    
    # 3. Encontrar el Punto de Máxima Potencia (MPP)
    idx_mpp = P.idxmax()
    v_mpp = V[idx_mpp]
    i_mpp = I[idx_mpp]
    p_max = P[idx_mpp]

    # 4. Crear la gráfica con doble eje
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # --- Eje Izquierdo: Corriente ---
    ax1.set_xlabel('Voltaje (V)', fontsize=12)
    ax1.set_ylabel('Corriente (A)', color='tab:blue', fontsize=12)
    line1 = ax1.plot(V, I, color='tab:blue', label='Curva I-V', linewidth=2)
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # --- Eje Derecho: Potencia ---
    ax2 = ax1.twinx() 
    ax2.set_ylabel('Potencia (W)', color='tab:red', fontsize=12)
    line2 = ax2.plot(V, P, color='tab:red', label='Curva P-V', linestyle='--', linewidth=2)
    ax2.tick_params(axis='y', labelcolor='tab:red')

    # 5. Marcar el MPP con un punto y una anotación
    ax2.scatter(v_mpp, p_max, color='black', s=100, zorder=5)
    ax2.annotate(f'MPP: {p_max:.2f}W', 
                 xy=(v_mpp, p_max), 
                 xytext=(v_mpp-0.15, p_max-0.5),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=8))

    # Título y Leyendas
    plt.title('Curvas I-V y P-V Xyce (Compilador)', fontsize=14)
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='center left')

    plt.tight_layout()
    plt.savefig('celula_fotovoltaica_xyce_compilador.png', dpi=300)
    plt.show()

except Exception as e:
    print(f"Error: {e}")