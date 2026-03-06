import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Симуляція руху поїзда", layout="wide")
st.title("Побудова кривих швидкості та часу (Метод МПС)")

# ==========================================
# 1. ІНТЕРФЕЙС КОРИСТУВАЧА (Введення даних)
# ==========================================
st.sidebar.header("Параметри поїзда")
MASS_COEFF = st.sidebar.number_input("Еквівалентна маса (кг/т)", value=1060, step=10)
STEP_S = st.sidebar.number_input("Крок інтегрування (м)", value=10, step=5)

st.sidebar.header("Профіль колії")
st.sidebar.write("Редагуйте довжину та ухил (+ підйом, - спуск):")

# Таблиця для редагування профілю
default_profile = pd.DataFrame({
    "Довжина (м)": [2000, 1500, 1000, 1500],
    "Ухил (‰)": [0, 6, -4, 2]
})
edited_profile = st.sidebar.data_editor(default_profile, num_rows="dynamic")

# Перетворення таблиці у формат для розрахунку
track_profile = [
    {'length': row["Довжина (м)"], 'gradient': row["Ухил (‰)"]} 
    for _, row in edited_profile.iterrows()
]

# ==========================================
# 2. ФУНКЦІЇ СИЛ
# ==========================================
def specific_traction(v_kmh):
    if v_kmh > 100: return 0
    return max(0, 120 - 0.8 * v_kmh - 0.005 * v_kmh**2)

def specific_resistance(v_kmh):
    return 15 + 0.1 * v_kmh + 0.003 * v_kmh**2

def get_gradient_at_s(s_current):
    accumulated_s = 0
    for segment in track_profile:
        accumulated_s += segment['length']
        if s_current <= accumulated_s:
            return segment['gradient']
    return 0

# ==========================================
# 3. РОЗРАХУНОК ТА ВІЗУАЛІЗАЦІЯ
# ==========================================
if st.sidebar.button("Почати розрахунок", type="primary"):
    total_distance = sum(seg['length'] for seg in track_profile)

    S_data, V_data, T_data, Elevation_data = [0.0], [0.0], [0.0], [0.0]
    current_v, current_t, current_elevation = 0.0, 0.0, 0.0

    # Інтегрування
    for s in range(STEP_S, int(total_distance) + STEP_S, STEP_S):
        v_kmh = current_v * 3.6
        fk = specific_traction(v_kmh)
        wk = specific_resistance(v_kmh)
        gradient = get_gradient_at_s(s)
        ik = gradient * 9.81 
        
        net_force = fk - wk - ik 
        a = net_force / MASS_COEFF
        
        v_sq = current_v**2 + 2 * a * STEP_S
        if v_sq < 0:
            current_v = 0.0
        else:
            current_v = np.sqrt(v_sq)
            
        v_avg = (V_data[-1] + current_v) / 2
        dt = STEP_S / v_avg if v_avg > 0 else 0
        current_t += dt
        current_elevation += (gradient / 1000) * STEP_S
        
        S_data.append(s)
        V_data.append(current_v)
        T_data.append(current_t)
        Elevation_data.append(current_elevation)

    # Побудова графіка
    S_km = np.array(S_data) / 1000
    V_kmh = np.array(V_data) * 3.6
    T_min = np.array(T_data) / 60

    fig, (ax1, ax_prof) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
    fig.subplots_adjust(hspace=0.3)

    # Верхній графік
    color_v = 'tab:blue'
    ax1.set_ylabel('Швидкість v, км/год', color=color_v, fontsize=12)
    line_v, = ax1.plot(S_km, V_kmh, color=color_v, linewidth=2.5, label='Швидкість v(S)')
    ax1.tick_params(axis='y', labelcolor=color_v)
    ax1.grid(True, linestyle='--', alpha=0.6)

    ax2 = ax1.twinx()  
    color_t = 'tab:red'
    ax2.set_ylabel('Час t, хв', color=color_t, fontsize=12)
    line_t, = ax2.plot(S_km, T_min, color=color_t, linestyle='--', linewidth=2.5, label='Час t(S)')
    ax2.tick_params(axis='y', labelcolor=color_t)
    
    lines = [line_v, line_t]
    ax1.legend(lines, [l.get_label() for l in lines], loc='upper left')

    # Нижній графік (Профіль)
    ax_prof.set_xlabel('Шлях S, км', fontsize=12)
    ax_prof.set_ylabel('Висота, м', fontsize=10)
    ax_prof.plot(S_km, Elevation_data, color='saddlebrown', linewidth=2)
    ax_prof.fill_between(S_km, Elevation_data, min(Elevation_data)-5, color='saddlebrown', alpha=0.3)
    ax_prof.set_ylim(bottom=min(Elevation_data)-5)
    ax_prof.grid(True, linestyle='--', alpha=0.6)

    st.pyplot(fig)
else:
    st.info("👈 Налаштуйте параметри в меню зліва та натисніть 'Почати розрахунок'.")
