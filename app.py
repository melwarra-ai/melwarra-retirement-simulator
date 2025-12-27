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
    cagr = st.slider("Expected Annual Growth (CAGR %)", 0.0, 100.0, 7.0) / 100

# --- FINANCIAL ENGINE ---
def get_marginal_rate(inc):
    if inc > 246752: return 0.5353
    if inc > 173205: return 0.4548
    if inc > 111733: return 0.4341
    return 0.3148

current_rate = get_marginal_rate(income)
years_to_retire = retire_age - age

# Logic: Maximize Year 1 RRSP to a strategic bracket floor ($173,205)
optimal_rrsp_lump = min(rrsp_room, max(0, income - 173205), cash)
refund = optimal_rrsp_lump * current_rate
tfsa_contribution = min(tfsa_room, cash - optimal_rrsp_lump + refund)

# --- PROJECTION SIMULATION ---
data = []
current_rrsp_total = current_rrsp_balance + optimal_rrsp_lump
current_tfsa_total = tfsa_contribution

for y in range(years_to_retire + 1):
    # We assume a 25% tax rate for the bridge period meltdown
    after_tax_rrsp = current_rrsp_total * (1 - 0.25) 
    total_wealth = after_tax_rrsp + current_tfsa_total
    
    data.append({
        "Year": 2025 + y,
        "Age": age + y,
        "RRSP (Pre-Tax)": current_rrsp_total,
        "TFSA (Tax-Free)": current_tfsa_total,
        "Total After-Tax Wealth": total_wealth
    })
    current_rrsp_total *= (1 + cagr)
    current_tfsa_total *= (1 + cagr)

df = pd.DataFrame(data)
final_rrsp = df.iloc[-1]['RRSP (Pre-Tax)']
final_tfsa = df.iloc[-1]['TFSA (Tax-Free)']
final_nest_egg = df.iloc[-1]['Total After-Tax Wealth']

# --- OUTPUT DISPLAY ---
st.header(f"💰 Retirement Income at Age {retire_age}")
swr_pct = st.select_slider("Safe Withdrawal Rate (%)", options=[3.0, 3.5, 4.0, 4.5, 5.0], value=3.5)

total_annual_target = final_nest_egg * (swr_pct / 100)
monthly_income = total_annual_target / 12

# --- NEW: THE WITHDRAWAL BRIDGE LOGIC ---
# Goal: Pull RRSP up to the first tax bracket (~$55k) to minimize lifetime tax
annual_rrsp_draw = min(final_rrsp / 20, 55000) # Simple 20-year meltdown or $55k cap
annual_tfsa_draw = max(0, total_annual_target - (annual_rrsp_draw * 0.80)) # TFSA fills the gap

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("Monthly Paycheck", f"${monthly_income:,.0f}")
with col_b:
    st.metric("From RRSP (Taxable)", f"${(annual_rrsp_draw/12):,.0f}")
with col_c:
    st.metric("From TFSA (Tax-Free)", f"${(annual_tfsa_draw/12):,.0f}")

st.success(f"**Strategy:** We withdraw **${annual_rrsp_draw:,.0f}/year** from your RRSP. This stays in a low tax bracket. The TFSA provides the remaining **${annual_tfsa_draw:,.0f}** tax-free to keep your lifestyle high and your tax bill low.")

st.divider()
st.subheader("Wealth Trajectory")
st.area_chart(df.set_index("Age")[["RRSP (Pre-Tax)", "TFSA (Tax-Free)"]])

with st.expander("🔍 HOW THE WITHDRAWAL BRIDGE WORKS"):
    st.write("1. **RRSP Meltdown:** We withdraw from the RRSP first to 'exhaust' the lowest tax brackets (up to ~$55k). This prevents your RRSP from growing too large and being taxed at 50%+ later in life.")
    st.write("2. **TFSA Top-Up:** Since TFSA withdrawals don't count as 'income,' we use them to get you to your target spending level without pushing you into a higher tax bracket.")
    st.write("3. **OAS Protection:** By reducing your RRSP balance early (ages 55-65), you avoid 'OAS Clawbacks' when government benefits start at 65.")
