import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_option('deprecation.showPyplotGlobalUse', False)

# ------------------------------------------------------
# YIELD + BIOMASS MODELS
# ------------------------------------------------------

def lint_yield(N, year):
    if year == 2023:
        a, b, c = -0.0281, 10.306, 605.08
    else:
        a, b, c = -0.0335, 6.8355, 1104.6
    return a*N**2 + b*N + c

def biomass(N, year):
    if year == 2023:
        a, b, c = -0.1274, 44.332, 8360.9
    else:
        a, b, c = -0.1471, 62.958, 2597.7
    return a*N**2 + b*N + c

def agronomic_optimum_N(year):
    if year == 2023:
        a, b = -0.0281, 10.306
    else:
        a, b = -0.0335, 6.8355
    return -b / (2*a)

def economic_optimum_N(year, lint_price, N_cost):
    if year == 2023:
        a, b, c = -0.0281, 10.306, 605.08
    else:
        a, b, c = -0.0335, 6.8355, 1104.6
    return max(0, (N_cost - b*lint_price) / (2*a*lint_price))

def nfue(N, year):
    if N <= 0:
        return 0
    return (lint_yield(N, year) - lint_yield(0, year)) / N

# ------------------------------------------------------
# SENSOR ADJUSTMENTS
# ------------------------------------------------------

def spad_adjustment(spad):
    if spad >= 44:
        return -20
    elif spad >= 40:
        return 0
    else:
        return +20

def soil_N_adjustment(no3, nh4):
    total = no3 + nh4
    if total >= 40:
        return -30
    elif total <= 10:
        return +30
    else:
        return 0

# ------------------------------------------------------
# STREAMLIT LAYOUT
# ------------------------------------------------------

st.title(" Cotton Nitrogen DSS (NFREC Quincy)")
st.write("""
This decision support tool helps determine the **optimal nitrogen rate**
for cotton based on yield curves, SPAD readings, soil nitrogen, and economics.
""")

st.sidebar.header("Input Parameters")

year = st.sidebar.selectbox("Select Year", [2023, 2024])
current_N = st.sidebar.slider("Current N applied (kg/ha)", 0, 220, 100)
spad = st.sidebar.slider("SPAD reading", 25.0, 55.0, 42.0)
no3 = st.sidebar.slider("Soil Nitrate (NO₃⁻ ppm)", 0, 80, 5)
nh4 = st.sidebar.slider("Soil Ammonium (NH₄⁺ ppm)", 0, 80, 2)
lint_price = st.sidebar.slider("Lint Price ($/kg)", 0.5, 2.5, 1.43)
N_cost = st.sidebar.slider("Nitrogen Cost ($/kg N)", 0.5, 5.0, 1.5)
goal = st.sidebar.radio("Goal", ["Maximize Yield (AONR)", "Maximize Profit (EONR)"])

# ------------------------------------------------------
# MAIN CALCULATION
# ------------------------------------------------------

AONR = agronomic_optimum_N(year)
EONR = economic_optimum_N(year, lint_price, N_cost)

base_optimum = AONR if goal == "Maximize Yield (AONR)" else EONR

adj_spad = spad_adjustment(spad)
adj_soil = soil_N_adjustment(no3, nh4)

final_N = np.clip(base_optimum + adj_spad + adj_soil, 0, 220)

# Yields
y_current = lint_yield(current_N, year)
y_recommend = lint_yield(final_N, year)

# Profits
profit_current = lint_price * y_current - N_cost * current_N
profit_recommend = lint_price * y_recommend - N_cost * final_N

# NFUE
nfue_current = nfue(current_N, year)
nfue_recommend = nfue(final_N, year)

# ------------------------------------------------------
# OUTPUT DISPLAY
# ------------------------------------------------------

st.subheader(" Nitrogen Recommendation")

st.write(f"###  Final Recommended Nitrogen: **{final_N:.1f} kg/ha**")

st.write("####  Sensor Adjustments")
st.write(f"- SPAD adjustment: **{adj_spad:+.0f} kg/ha**")
st.write(f"- Soil N adjustment: **{adj_soil:+.0f} kg/ha**")

st.write("####  Yield & Profit Comparison")
st.write(f"- Yield at current N: **{y_current:.0f} kg/ha**")
st.write(f"- Yield at recommended N: **{y_recommend:.0f} kg/ha**")
st.write(f"- Profit at current N: **${profit_current:.0f}/ha**")
st.write(f"- Profit at recommended N: **${profit_recommend:.0f}/ha**")

st.write("#### 📉 NFUE (Nitrogen Fertilizer Use Efficiency)")
st.write(f"- At current N: **{nfue_current:.2f} kg lint/kg N**")
st.write(f"- At recommended N: **{nfue_recommend:.2f} kg lint/kg N**")

# ------------------------------------------------------
# YIELD CURVE PLOT
# ------------------------------------------------------

st.subheader(" Yield Response Curve")

N_vals = np.linspace(0, 220, 200)
y_vals = lint_yield(N_vals, year)

plt.figure(figsize=(8,4))
plt.plot(N_vals, y_vals, label="Yield Curve")
plt.scatter(current_N, y_current, color='red', label="Current N")
plt.scatter(final_N, y_recommend, color='green', s=80, label="Recommended N")
plt.xlabel("Nitrogen (kg/ha)")
plt.ylabel("Yield (kg/ha)")
plt.grid(True)
plt.legend()
st.pyplot()
