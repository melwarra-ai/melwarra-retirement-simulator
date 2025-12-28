import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Retirement Architect Pro", layout="wide")
st.title("🏛️ Retirement & Tax Building Architect")

# --- SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("👤 Income Profile")
    gross_income = st.number_input("Total Gross Income (Salary + Bonus) ($)", value=200000, step=5000)
    base_salary = st.number_input("Annual Base Salary ($)", value=180000, step=5000)
    
    st.header("💰 RRSP Strategy")
    biweekly_pct = st.slider("Your Biweekly Contribution (% of Base)", 0.0, 18.0, 6.0)
    employer_match_pct = st.slider("Employer Match (% of Base)", 0.0, 10.0, 4.0)
    
    st.header("📁 Available Room")
    rrsp_room = st.number_input("Unused RRSP Room ($)", value=146000)

# --- 2026 ONTARIO/FEDERAL COMBINED TAX BRACKETS ---
BRACKETS = [
    {"name": "Floor 1: Basic", "top": 53891, "rate": 0.1905},
    {"name": "Floor 2: Lower-Mid", "top": 58523, "rate": 0.2315},
    {"name": "Floor 3: Mid", "top": 94907, "rate": 0.2965},
    {"name": "Floor 4: Upper-Mid", "top": 117045, "rate": 0.3148},
    {"name": "Floor 5: High Cliff", "top": 181440, "rate": 0.4497},
    {"name": "The Penthouse: Peak", "top": 258482, "rate": 0.4829},
    {"name": "Skyline: Ultra", "top": 1000000, "rate": 0.5353}
]

# --- CALCULATIONS ---
total_contrib_rate = (biweekly_pct + employer_match_pct) / 100
annual_rrsp_periodic = base_salary * total_contrib_rate
taxable_income_current = gross_income - annual_rrsp_periodic
tax_cliff = 181440 # 2026 High-Tax Bracket Floor

# --- VISUALIZER: THE TAX BUILDING ---
st.header("🏛️ The Tax Building Visualizer")
st.write("Bars show your income per tax floor. Blue indicates income shielded by RRSP.")

chart_data = []
prev_top = 0
for b in BRACKETS:
    slice_height = min(gross_income, b['top']) - prev_top
    if slice_height <= 0: break
    
    # Simple Logic: Is this floor shielded?
    is_shielded = (prev_top >= taxable_income_current)
    
    # We use a simple color string that any Streamlit version can handle
    color_hex = "#3b82f6" if is_shielded else "#22c55e"
    
    chart_data.append({
        "Floor": b['name'], 
        "Income ($)": slice_height,
        "Color": color_hex
    })
    prev_top = b['top']

df_chart = pd.DataFrame(chart_data)

# We pass 'Color' directly to the color argument to ensure compatibility
st.bar_chart(df_chart, x="Floor", y="Income ($)", color="Color")

# --- ACTIONABLE CHECKLIST ---
st.divider()
st.header("📅 Tax Season Checklist: March 2nd Deadline")

premium_lump_sum = max(0, taxable_income_current - tax_cliff)
actual_lump = min(premium_lump_sum, rrsp_room)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Income in 'Penthouse'", f"${premium_lump_sum:,.0f}")
with col2:
    st.metric("Recommended Lump Sum", f"${actual_lump:,.0f}")
with col3:
    refund = actual_lump * 0.4829
    st.success(f"Est. Extra Refund: **${refund:,.0f}**")

st.info(f"👉 **Strategic Insight:** Your 'Efficiency Floor' is **${tax_cliff:,.0f}**. Once you reach this level, stop RRSP contributions and move extra cash to your TFSA.")
