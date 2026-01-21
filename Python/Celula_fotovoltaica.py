import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve

# --- 1. PARÁMETROS DE LA CELDA ---
Iph = 3.5        # Fotocorriente (A)
I0 = 1e-9        # Corriente de saturación inversa (A)
n = 1.5          # Factor de idealidad
Rs = 0.05        # Resistencia serie (Ohm)
Rsh = 500        # Resistencia Shunt (Ohm)
T = 300.15       # Temperatura (27°C)

q = 1.602e-19    # Carga del electrón
k = 1.381e-23    # Constante de Boltzmann
Vt = (k * T) / q # Voltaje térmico

# --- 2. FUNCIÓN DE LA ECUACIÓN CARACTERÍSTICA ---
def ecuacion_celda(I, V):
    termino_diodo = I0 * (np.exp((V + I * Rs) / (n * Vt)) - 1)
    termino_shunt = (V + I * Rs) / Rsh
    return Iph - termino_diodo - termino_shunt - I

# --- 3. SIMULACIÓN (Barrido de Voltaje) ---
v_puntos = np.linspace(0, 0.9, 100)
i_puntos = []

for v in v_puntos:
    i_solucion = fsolve(ecuacion_celda, x0=Iph, args=(v,))
    i_puntos.append(i_solucion[0])

i_puntos = np.array(i_puntos)
potencia = v_puntos * i_puntos

# --- 4. CÁLCULO DEL MPP ---
idx_mpp = np.argmax(potencia) 
v_mpp = v_puntos[idx_mpp]
i_mpp = i_puntos[idx_mpp]
p_mpp = potencia[idx_mpp]

# --- 5. GRÁFICAS ---
fig, ax1 = plt.subplots(figsize=(10, 6))

# Eje Corriente (I-V)
line_i = ax1.plot(v_puntos, i_puntos, 'b-', label='Corriente (I-V)', linewidth=2.5)
ax1.set_xlabel('Voltaje (V)', fontsize=12)
ax1.set_ylabel('Corriente (A)', color='b', fontsize=12)
ax1.grid(True, linestyle='--', alpha=0.6)

# Eje Potencia (P-V)
ax2 = ax1.twinx()
line_p = ax2.plot(v_puntos, potencia, 'r--', label='Potencia (P-V)', linewidth=2)
ax2.set_ylabel('Potencia (W)', color='r', fontsize=12)

# Marcar el punto MPP
ax2.scatter(v_mpp, p_mpp, color='black', s=100, zorder=5)
ax2.annotate(f'MPP: {p_mpp:.3f} W\n({v_mpp:.3f} V)', 
             xy=(v_mpp, p_mpp), 
             xytext=(v_mpp - 0.2, p_mpp - 0.4),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1))

plt.title('Modelo Matemático: Curvas I-V / P-V con MPP', fontsize=14)

# Unificar leyendas
lines = line_i + line_p
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='center left')

plt.tight_layout()

# --- ESTA ES LA LÍNEA QUE GUARDA LA IMAGEN ---
plt.savefig('grafica_mpp_matematica.png', dpi=300)
print("Archivo 'grafica_mpp_matematica.png' guardado con éxito.")

plt.show()