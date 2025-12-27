import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Retirement Architect Pro", layout="wide")
st.title("🇨🇦 Retirement Optimization Simulator")
st.markdown("### Strategy: Early Retirement (Age 55) | High-Income Laddering")

# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.header("1. Financial Profile")
    age = st.number_input("Current Age", value=42)
    retire_age = st.number_input("Target Retirement Age", value=55)
    income = st.number_input("Gross Annual Income ($)", value=200000)
    
    st.header("2. Existing Assets")
    current_rrsp_balance = st.number_input("Current RRSP Balance ($)", value=150000)
    rrsp_room = st.number_input("Available RRSP Room ($)", value=146000)
    tfsa_room = st.number_input("Available TFSA Room ($)", value=102000)
    
    st.header("3. New Capital")
    cash = st.number_input("Available Cash to Invest Now ($)", value=100000)
    
    st.header("4. Market Assumptions")
    # Updated CAGR slider to support up to 100%
    cagr = st.slider("Expected Annual Growth (CAGR %)", 0.0, 100.0, 7.0) / 100

# --- FINANCIAL ENGINE ---
def get_marginal_rate(inc):
    # 2025 Ontario/Federal Estimated Marginal Brackets
    if inc > 246752: return 0.5353
    if inc > 173205: return 0.4548
    if inc > 111733: return 0.4341
    return 0.3148

current_rate = get_marginal_rate(income)
years_to_retire = retire_age - age

# Logic: Maximize Year 1 RRSP to a strategic bracket floor ($173,205)
# This maximizes the 45.48% tax savings.
optimal_rrsp_lump = min(rrsp_room, max(0, income - 173205), cash)
refund = optimal_rrsp_lump * current_rate
tfsa_contribution = min(tfsa_room, cash - optimal_rrsp_lump + refund)

# --- PROJECTION SIMULATION ---
data = []
# Start with existing balance + new Year 1 contribution
current_rrsp_total = current_rrsp_balance + optimal_rrsp_lump
current_tfsa_total = tfsa_contribution

for y in range(years_to_retire + 1):
    # After-tax logic: We assume a 30% average tax on RRSP withdrawals at age 55
    after_tax_rrsp = current_rrsp_total * (1 - 0.30)
    total_wealth = after_tax_rrsp + current_tfsa_total
    
    data.append({
        "Year": 2025 + y,
        "Age": age + y,
        "RRSP (Pre-Tax)": current_rrsp_total,
        "TFSA (Tax-Free)": current_tfsa_total,
        "Total After-Tax Wealth": total_wealth
    })
    
    # Compound for next year
    current_rrsp_total *= (1 + cagr)
    current_tfsa_total *= (1 + cagr)

df = pd.DataFrame(data)

# --- OUTPUT DISPLAY ---
c1, c2, c3 = st.columns(3)
c1.metric("Year 1 RRSP Top-up", f"${optimal_rrsp_lump:,.0f}")
c2.metric("Estimated Tax Refund", f"${refund:,.0f}")
c3.metric("Year 1 TFSA Deposit", f"${tfsa_contribution:,.0f}")

st.divider()

# --- VISUALIZATION ---
st.subheader(f"Wealth Trajectory to Age {retire_age}")
st.area_chart(df.set_index("Age")[["RRSP (Pre-Tax)", "TFSA (Tax-Free)"]])

st.subheader("Summary Table")
st.dataframe(df.style.format({
    "RRSP (Pre-Tax)": "${:,.0f}",
    "TFSA (Tax-Free)": "${:,.0f}",
    "Total After-Tax Wealth": "${:,.0f}"
}), use_container_width=True)

# --- EXPLANATION ---
st.info(f"""
**Architect's Note:**
1. **Existing RRSP:** Your current balance of **${current_rrsp_balance:,.0f}** is included in the growth projection.
2. **Aggressive CAGR:** With a **{cagr*100:.0f}%** growth rate, your portfolio doubles rapidly. *Note: 100% CAGR is extreme and usually reserved for high-risk venture or crypto simulations.*
3. **Age 55 Result:** Your estimated after-tax liquid wealth at retirement is **${df.iloc[-1]['Total After-Tax Wealth']:,.0f}**.
""")
