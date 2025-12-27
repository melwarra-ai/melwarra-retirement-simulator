import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(page_title="Retirement Architect Pro", layout="wide")
st.title("🇨🇦 Retirement Optimization Simulator")
st.markdown("### Strategy: Early Retirement (Age 55) | High-Income Laddering")

# --- SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("1. Income & Salary Profile")
    age = st.number_input("Current Age", value=42)
    retire_age = st.number_input("Target Retirement Age", value=55)
    
    base_salary = st.number_input("Annual Base Salary ($)", value=180000)
    gross_income = st.number_input("Total Gross Income ($)", value=200000)
    
    st.header("2. Periodic Contributions")
    biweekly_pct = st.slider("Your Biweekly RRSP Contribution (% of Base)", 0.0, 18.0, 6.0)
    employer_match_pct = st.slider("Employer Match (% of Base)", 0.0, 10.0, 4.0)
    
    st.header("3. Assets & Room")
    current_rrsp_balance = st.number_input("Current RRSP Balance ($)", value=150000)
    rrsp_room = st.number_input("Available RRSP Room ($)", value=146000)
    tfsa_room = st.number_input("Available TFSA Room ($)", value=102000)
    
    st.header("4. New Capital")
    cash = st.number_input("Available Cash to Invest Now ($)", value=100000)
    
    st.header("5. Market Assumptions")
    cagr = st.slider("Expected Annual Growth (CAGR %)", 0.0, 100.0, 7.0) / 100
    inflation = st.slider("Expected Inflation (%)", 0.0, 10.0, 2.2) / 100

# --- FINANCIAL CALCULATIONS ---
annual_self_contrib = base_salary * (biweekly_pct / 100)
annual_employer_contrib = base_salary * (employer_match_pct / 100)
total_annual_rrsp_flow = annual_self_contrib + annual_employer_contrib

def get_marginal_rate(inc):
    if inc > 246752: return 0.5353
    if inc > 173205: return 0.4548
    if inc > 111733: return 0.4341
    return 0.3148

current_rate = get_marginal_rate(gross_income)
years_to_retire = retire_age - age

# Optimization: Year 1 Lump Sum strategy
optimal_rrsp_lump = min(rrsp_room, max(0, gross_income - 173205), cash)
refund = optimal_rrsp_lump * current_rate
tfsa_contribution = min(tfsa_room, cash - optimal_rrsp_lump + refund)

# --- PROJECTION SIMULATION ---
data = []
current_rrsp_total = current_rrsp_balance + optimal_rrsp_lump
current_tfsa_total = tfsa_contribution
total_tax_saved_lump = refund
total_tax_saved_periodic = 0

for y in range(years_to_retire + 1):
    after_tax_rrsp = current_rrsp_total * (1 - 0.25) 
    total_wealth = after_tax_rrsp + current_tfsa_total
    purchasing_power = total_wealth / ((1 + inflation) ** y)
    
    # Track periodic tax savings (deductions at source)
    total_tax_saved_periodic += (annual_self_contrib * current_rate)
    
    data.append({
        "Year": 2025 + y,
        "Age": age + y,
        "RRSP (Pre-Tax)": current_rrsp_total,
        "TFSA (Tax-Free)": current_tfsa_total,
        "Total After-Tax Wealth": total_wealth,
        "Purchasing Power (Today's $)": purchasing_power
    })
    
    current_rrsp_total = (current_rrsp_total + total_annual_rrsp_flow) * (1 + cagr)
    current_tfsa_total *= (1 + cagr)

df = pd.DataFrame(data)
final_rrsp = df.iloc[-1]['RRSP (Pre-Tax)']
final_wealth = df.iloc[-1]['Total After-Tax Wealth']
lifetime_tax_savings = total_tax_saved_lump + total_tax_saved_periodic

# --- DASHBOARD LAYOUT ---
c1, c2, c3 = st.columns(3)
c1.metric("Annual Flow (You + Employer)", f"${total_annual_rrsp_flow:,.0f}")
c2.metric("Lump Sum Refund", f"${refund:,.0f}")
c3.metric("Lifetime Tax Savings", f"${lifetime_tax_savings:,.0f}")

st.divider()

# --- GROWTH ENGINE ---
st.header("📈 The Growth Engine Logic")
col_eng1, col_eng2 = st.columns(2)
with col_eng1:
    st.subheader("1. Internal Compounding")
    st.write(f"- Starting Base: ${current_rrsp_balance + optimal_rrsp_lump:,.0f}")
    st.write(f"- Compounded at **{cagr*100:.1f}%** annually.")
with col_eng2:
    st.subheader("2. External Contributions")
    st.write(f"- Biweekly Inflow: **${(total_annual_rrsp_flow/26):,.0f}**")
    st.write(f"- Includes Employer Match: **${(annual_employer_contrib/26):,.0f}**")

st.area_chart(df.set_index("Age")[["RRSP (Pre-Tax)", "TFSA (Tax-Free)"]])

st.divider()

# --- TAX SAVINGS DASHBOARD ---
st.header("🛡️ Lifetime Tax Alpha Dashboard")
st.markdown("This section calculates the wealth you've generated solely through tax avoidance.")
tx1, tx2, tx3 = st.columns(3)
tx1.write(f"**Immediate Refund:** ${refund:,.0f}")
tx2.write(f"**Annual Periodic Savings:** ${ (annual_self_contrib * current_rate):,.0f}/year")
tx3.write(f"**Cumulative 13-Year Savings:** **${lifetime_tax_savings:,.0f}**")
st.info(f"By age 55, you will have avoided **${lifetime_tax_savings:,.0f}** in income taxes. If this money were not sheltered, your final wealth would be significantly lower due to tax drag.")

st.divider()

# --- WITHDRAWAL STRATEGY ---
st.header(f"💰 Retirement Withdrawal Strategy (Age {retire_age})")
swr_pct = st.select_slider("Safe Withdrawal Rate (%)", options=[3.0, 3.5, 4.0, 4.5, 5.0], value=3.5)

total_annual_target = final_wealth * (swr_pct / 100)
monthly_income = total_annual_target / 12
annual_rrsp_draw = min(final_rrsp / 20, 55000) 
annual_tfsa_draw = max(0, total_annual_target - (annual_rrsp_draw * 0.75))

wa, wb, wc = st.columns(3)
wa.metric("Est. Monthly Paycheck", f"${monthly_income:,.0f}")
wb.metric("From RRSP (Taxable)", f"${(annual_rrsp_draw/12):,.0f}")
wc.metric("From TFSA (Tax-Free)", f"${(annual_tfsa_draw/12):,.0f}")

with st.expander("📝 Strategy Methodology & Account Meltdown"):
    st.write("1. **RRSP Priority:** Withdrawals are capped at ~$55k to utilize low brackets.")
    st.write("2. **TFSA Supplement:** Tax-free top-ups maintain lifestyle without increasing tax rates.")
    st.write("3. **Bracket Protection:** Prevents high-tax RRIF forced withdrawals later in life.")
