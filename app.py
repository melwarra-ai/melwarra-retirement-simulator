import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="Retirement Architect Pro", layout="wide")
st.title("🇨🇦 Retirement & Tax Building Architect")
st.markdown("### Strategy: Early Retirement (Age 55) | High-Income Optimization")

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
    tfsa_room = st.number_input("Unused TFSA Room ($)", value=102000)

# --- 2026 ONTARIO/FEDERAL TAX BRACKETS ---
BRACKETS = [
    {"name": "Floor 1: Basic", "top": 53891, "rate": 0.1905, "color": "#dcfce7"},
    {"name": "Floor 2: Lower-Mid", "top": 58523, "rate": 0.2315, "color": "#bbf7d0"},
    {"name": "Floor 3: Mid", "top": 94907, "rate": 0.2965, "color": "#86efac"},
    {"name": "Floor 4: Upper-Mid", "top": 117045, "rate": 0.3148, "color": "#4ade80"},
    {"name": "Floor 5: High Cliff", "top": 181440, "rate": 0.4497, "color": "#22c55e"},
    {"name": "The Penthouse: Peak", "top": 220000, "rate": 0.4829, "color": "#16a34a"},
    {"name": "Skyline: Ultra", "top": 1000000, "rate": 0.5353, "color": "#15803d"}
]

# --- CALCULATIONS ---
total_contrib_rate = (biweekly_pct + employer_match_pct) / 100
annual_rrsp_periodic = base_salary * total_contrib_rate
taxable_income_current = gross_income - annual_rrsp_periodic
tax_cliff = 181440 # The 48% Efficiency Floor

# --- VISUALIZER: THE TAX BUILDING ---
st.header("🏛️ The Tax Building Visualizer")
st.write("Blue segments represent income you've 'shielded' from tax using RRSP contributions.")

labels, values, colors, tooltips = [], [], [], []
prev_top = 0
for b in BRACKETS:
    slice_height = min(gross_income, b['top']) - prev_top
    if slice_height <= 0: break
    
    # Shielding logic: income is shielded from the highest bracket downward
    is_shielded = (prev_top >= taxable_income_current)
    
    labels.append(f"{b['name']} ({b['rate']*100:.1f}%)")
    values.append(slice_height)
    colors.append("#3b82f6" if is_shielded else b['color'])
    tooltips.append(f"Tax Rate: {b['rate']*100:.1f}%<br>Income in slice: ${slice_height:,.0f}")
    prev_top = b['top']

fig = go.Figure(go.Bar(
    x=labels, y=values,
    marker_color=colors,
    customdata=tooltips,
    hovertemplate="%{customdata}<extra></extra>"
))
fig.update_layout(yaxis_title="Income Dollars ($)", showlegend=False, height=450)
st.plotly_chart(fig, use_container_width=True)

# --- ACTIONABLE CHECKLIST ---
st.divider()
st.header("📅 Tax Season Checklist: March 2nd Deadline")

premium_lump_sum = max(0, taxable_income_current - tax_cliff)
actual_lump = min(premium_lump_sum, rrsp_room)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Income in 'Penthouse'", f"${premium_lump_sum:,.0f}")
    st.caption("Taxed at 48.3%. Priority to clear.")
with col2:
    st.metric("Recommended Lump Sum", f"${actual_lump:,.0f}")
    st.caption("Contribute this to maximize efficiency.")
with col3:
    refund = actual_lump * 0.4829
    st.success(f"Est. Extra Refund: **${refund:,.0f}**")
    st.caption("Deposit this refund to your TFSA.")

st.info(f"👉 **Strategic Insight:** Once your taxable income hits **${tax_cliff:,.0f}**, stop RRSP contributions and prioritize your **TFSA**. This ensures you don't 'waste' RRSP room on lower tax savings (~43%) when you can have tax-free growth instead.")
