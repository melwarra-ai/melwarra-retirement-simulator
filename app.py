import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(page_title="Retirement Architect Pro", layout="wide")
st.title("🇨🇦 Retirement Optimization Simulator")
st.markdown("### Strategy: Early Retirement (Age 55) | High-Income Laddering")

# --- SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("1. Financial Profile")
    age = st.number_input("Current Age", value=42)
    retire_age = st.number_input("Target Retirement Age", value=55)
    income = st.number_input("Gross Annual Income ($)", value=200000)
    
    st.header("2. Periodic Contributions")
    biweekly_pct = st.slider("Your Biweekly RRSP Contribution (%)", 0.0, 18.0, 5.0)
    employer_match_pct = st.slider("Employer Match (%)", 0.0, 10.0, 4.0)
    
    st.header("3. Existing Assets")
    current_rrsp_balance = st.number_input("Current RRSP Balance ($)", value=150000)
    rrsp_room = st.number_input("Available RRSP Room ($)", value=146000)
    tfsa_room = st.number_input("Available TFSA Room ($)", value=102000)
    
    st.header("4. New Capital")
    cash = st.number_input("Available Cash to Invest Now ($)", value=100000)
    
    st.header("5. Market Assumptions")
    cagr = st.slider("Expected Annual Growth (CAGR %)", 0.0, 100.0, 7.0) / 100
    inflation = st.slider("Expected Inflation (%)", 0.0, 10.0, 2.2) / 100

# --- FINANCIAL CALCULATIONS ---
# Annualize the biweekly contributions
annual_self_contrib = income * (biweekly_pct / 100)
annual_employer_contrib = income * (employer_match_pct / 100)
total_annual_rrsp_flow = annual_self_contrib + annual_employer_contrib

def get_marginal_rate(inc):
    if inc > 246752: return 0.5353
    if inc > 173205: return 0.4548
    if inc > 111733: return 0.4341
    return 0.3148

current_rate = get_marginal_rate(income)
years_to_retire = retire_age - age

# Optimization: Year 1 Lump Sum strategy
optimal_rrsp_lump = min(rrsp_room, max(0, income - 173205), cash)
refund = optimal_rrsp_lump * current_rate
tfsa_contribution = min(tfsa_room, cash - optimal_rrsp_lump + refund)

# --- PROJECTION SIMULATION ---
data = []
current_rrsp_total = current_rrsp_balance + optimal_rrsp_lump
current_tfsa_total = tfsa_contribution

for y in range(years_to_retire + 1):
    after_tax_rrsp = current_rrsp_total * (1 - 0.25) 
    total_wealth = after_tax_rrsp + current_tfsa_total
    purchasing_power = total_wealth / ((1 + inflation) ** y)
    
    data.append({
        "Year": 2025 + y,
        "Age": age + y,
        "RRSP (Pre-Tax)": current_rrsp_total,
        "TFSA (Tax-Free)": current_tfsa_total,
        "Total After-Tax Wealth": total_wealth,
        "Purchasing Power (Today's $)": purchasing_power
    })
    
    # Add annual flow and grow the pot
    current_rrsp_total = (current_rrsp_total + total_annual_rrsp_flow) * (1 + cagr)
    current_tfsa_total *= (1 + cagr)

df = pd.DataFrame(data)
final_rrsp = df.iloc[-1]['RRSP (Pre-Tax)']
final_wealth = df.iloc[-1]['Total After-Tax Wealth']

# --- TOP METRICS ---
c1, c2, c3 = st.columns(3)
c1.metric("Annual RRSP Inflow", f"${total_annual_rrsp_flow:,.0f}")
c2.metric("Employer 'Free Money'", f"${annual_employer_contrib:,.0f}")
c3.metric("Year 1 Tax Refund", f"${refund:,.0f}")

st.divider()

# --- GROWTH TRAJECTORY LOGIC ---
st.header("📈 The Growth Trajectory Engine")
st.markdown(f"""
Your trajectory is powered by **Periodic Dollar-Cost Averaging**. Every two weeks, you are adding 
**${(annual_self_contrib/26):,.0f}** of your own money, which is matched by 
**${(annual_employer_contrib/26):,.0f}** from your company.
""")



col_logic1, col_logic2 = st.columns(2)
with col_logic1:
    st.subheader("1. Compounding Mechanics")
    st.write(f"- **Starting Base:** Initial assets + ${optimal_rrsp_lump:,.0f} lump sum.")
    st.write(f"- **Annual Contribution:** ${total_annual_rrsp_flow:,.0f} total inflow.")
    st.write(f"- **Yield:** Compounded at **{cagr*100:.1f}%** annually.")

with col_logic2:
    st.subheader("2. Strategic Advantages")
    st.write("- **The Match:** Your employer match represents an immediate 100% return on that portion of your savings.")
    st.write("- **Tax Efficiency:** Your biweekly contributions reduce your taxable income at source, lowering your paycheque tax immediately.")

st.area_chart(df.set_index("Age")[["RRSP (Pre-Tax)", "TFSA (Tax-Free)"]])

st.divider()

# --- WITHDRAWAL STRATEGY ---
st.header(f"💰 Retirement Withdrawal Strategy (Age {retire_age})")
swr_pct = st.select_slider("Safe Withdrawal Rate (%)", options=[3.0, 3.5, 4.0, 4.5, 5.0], value=3.5)

total_annual_target = final_wealth * (swr_pct / 100)
monthly_income = total_annual_target / 12

annual_rrsp_draw = min(final_rrsp / 20, 55000) 
annual_tfsa_draw = max(0, total_annual_target - (annual_rrsp_draw * 0.75))

wa, wb, wc = st.columns(3)
wa.metric("Total Monthly Paycheck", f"${monthly_income:,.0f}")
wb.metric("From RRSP (Taxable)", f"${(annual_rrsp_draw/12):,.0f}")
wc.metric("From TFSA (Tax-Free)", f"${(annual_tfsa_draw/12):,.0f}")

with st.expander("📝 Strategy Methodology"):
    st.write("**Account Meltdown:** We withdraw from the RRSP first to utilize low tax brackets (up to ~$55k).")
    st.write("**TFSA Bridge:** The TFSA tops up your income tax-free, keeping you out of high tax brackets.")
    st.write("**OAS Protection:** Early RRSP drawdown prevents high-income 'clawbacks' after age 65.")
