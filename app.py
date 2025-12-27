import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Retirement Architect", layout="wide")
st.title("🇨🇦 Retirement Optimization Simulator")
st.markdown("### Strategy: Early Retirement (Age 55) | High-Income Laddering")

# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.header("Financial Profile")
    age = st.number_input("Current Age", value=42)
    retire_age = st.number_input("Retirement Age", value=55)
    income = st.number_input("Gross Income ($)", value=200000)
    cash = st.number_input("Initial Cash to Invest ($)", value=100000)
    rrsp_room = st.number_input("Existing RRSP Room ($)", value=146000)
    tfsa_room = st.number_input("Existing TFSA Room ($)", value=102000)
    cagr = st.slider("Expected CAGR (%)", 0.0, 12.0, 6.0) / 100

# --- FINANCIAL ENGINE ---
def get_marginal_rate(inc):
    # Simplified 2025 ON/FED Brackets
    if inc > 246752: return 0.5353
    if inc > 173205: return 0.4548
    if inc > 111733: return 0.4341
    return 0.3148

current_rate = get_marginal_rate(income)
years = retire_age - age

# Logic: Maximize RRSP to bracket floor ($173k) or use cash
optimal_rrsp_lump = min(rrsp_room, max(0, income - 173205), cash)
refund = optimal_rrsp_lump * current_rate
tfsa_contribution = min(tfsa_room, cash - optimal_rrsp_lump + refund)

# --- PROJECTION SIMULATION ---
data = []
current_rrsp = optimal_rrsp_lump
current_tfsa = tfsa_contribution

for y in range(years + 1):
    data.append({
        "Year": y + 2025,
        "Age": age + y,
        "RRSP Balance": current_rrsp,
        "TFSA Balance": current_tfsa,
        "Total (After-Tax)": (current_rrsp * (1-0.30)) + current_tfsa # Assuming 30% ret. tax
    })
    current_rrsp *= (1 + cagr)
    current_tfsa *= (1 + cagr)

df = pd.DataFrame(data)

# --- OUTPUT DISPLAY ---
col1, col2, col3 = st.columns(3)
col1.metric("Recommended RRSP (Year 1)", f"${optimal_rrsp_lump:,.0f}")
col2.metric("Estimated Refund", f"${refund:,.0f}")
col3.metric("TFSA Contribution", f"${tfsa_contribution:,.0f}")

st.divider()
st.subheader("Wealth Projection to Age 55")
st.area_chart(df.set_index("Age")[["RRSP Balance", "TFSA Balance"]])

st.markdown(f"""
### 💡 Architect's Explanation
* **Arbitrage:** We prioritized deducting **${optimal_rrsp_lump:,.0f}** because it sits in your top tax bracket (**{current_rate*100:.1f}%**). 
* **The Bridge:** By filling the TFSA to **${tfsa_contribution:,.0f}** early, you create a tax-free pool to live on between age 55 and 65.
* **Final Nest Egg:** At age {retire_age}, your estimated after-tax wealth is **${df.iloc[-1]['Total (After-Tax)']:,.0f}**.
""")
