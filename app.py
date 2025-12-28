import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="Retirement Architect Pro", layout="wide")
st.title("🏢 Retirement & Tax Building Architect (2025-2026)")
st.markdown("Optimize your path to retirement at age 55 by avoiding the 'Penthouse' tax floors.")

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

# --- 2026 ONTARIO/FEDERAL TAX DATA (ESTIMATED) ---
# Combined rates: Fed + ON + Surtax (Estimated indexed thresholds)
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
total_contribution_rate = (biweekly_pct + employer_match_pct) / 100
annual_rrsp_periodic = base_salary * total_contribution_rate
taxable_income_current = gross_income - annual_rrsp_periodic

# Target Floor Logic ($181,440 is the 2026 High-Tax Cliff)
tax_cliff = 181440
premium_lump_sum_needed = max(0, taxable_income_current - tax_cliff)
actual_lump_sum = min(premium_lump_sum_needed, rrsp_room)
estimated_refund = actual_lump_sum * 0.4829

# --- SECTION 1: THE TAX BUILDING VISUALIZER ---
st.header("🏛️ The Tax Building Visualizer")
st.write("Each floor represents a tax bracket. Blue indicates income you've 'shielded' with RRSP contributions.")

labels, values, colors, tooltips = [], [], [], []
prev_top = 0
for b in BRACKETS:
    # Amount of income that falls into this specific bracket
    slice_height = min(gross_income, b['top']) - prev_top
    if slice_height <= 0: break
    
    # Determine if this slice is currently being shielded
    # (Income is shielded from the top down)
    is_shielded = (prev_top >= (gross_income - annual_rrsp_periodic))
    
    labels.append(f"{b['name']} ({b['rate']*100:.1f}%)")
    values.append(slice_height)
    # Color logic: Blue if shielded, original color if taxed
    colors.append("#3b82f6" if is_shielded else b['color'])
    tooltips.append(f"Tax Rate: {b['rate']*100:.1f}%<br>Income in slice: ${slice_height:,.0f}")
    prev_top = b['top']

fig = go.Figure(go.Bar(
    x=labels, y=values,
    marker_color=colors,
    hovertemplate="%{customdata}<extra></extra>",
    customdata=tooltips
))
fig.update_layout(yaxis_title="Income Dollars ($)", showlegend=False, height=500)
st.plotly_chart(fig, use_container_width=True)

# --- SECTION 2: MARCH 2nd CHECKLIST ---
st.divider()
st.header("📅 Tax Season Checklist: March 2nd Deadline")
st.info("Contributions made by March 2nd can reduce your 2025 tax bill. This is your chance to clear the Penthouse.")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Income in 'Penthouse'", f"${max(0, taxable_income_current - tax_cliff):,.0f}")
    st.caption("This income is being taxed at 48.3%.")

with col2:
    st.metric("Recommended Lump Sum", f"${actual_lump_sum:,.0f}", delta_color="inverse")
    st.caption("Contribute this by March 2nd to drop to a lower floor.")

with col3:
    st.success(f"Estimated Extra Refund: **${estimated_refund:,.0f}**")
    st.caption("Move this immediately into your TFSA.")

# --- SECTION 3: STRATEGIC RECOMMENDATION ---
st.divider()
st.subheader("💡 Strategic Architecture Report")

if taxable_income_current > tax_cliff:
    st.error(f"**Inefficiency Detected:** You are currently paying **48.3% tax** on your top **${taxable_income_current - tax_cliff:,.0f}**. Fill this gap before doing anything else.")
else:
    st.success(f"**Efficiency Optimized:** Your current contributions have moved you below the 48% floor. Any further RRSP contributions are 'Low Value' (saving only ~43%).")

st.markdown(f"""
### **The 3-Step Plan for Retirement at 55**
1. **Direct Bonus Transfer:** Ask HR to move your next $20k bonus directly to your RRSP to avoid the 48% tax hit entirely.
2. **The RRSP Bracket-Floor:** Stop RRSP contributions once your taxable income hits **${tax_cliff:,.0f}**.
3. **TFSA Pivot:** Every dollar saved *after* hitting the floor should go to your TFSA. This creates the "Tax-Free Bridge" you'll need from age 55 to 65.
""")

# --- BONUS TOOL: T1213 GENERATOR DATA ---
with st.expander("📝 Data for CRA Form T1213 (Tax Waiver)"):
    st.write("Use these numbers to request your employer reduce tax withholdings at source:")
    st.write(f"- **Expected RRSP Contributions for 2026:** ${annual_rrsp_periodic:,.0f}")
    st.write(f"- **Estimated Annual Bonus/Commissions:** ${gross_income - base_salary:,.0f}")
    st.write("- **Reason:** To align tax deductions with anticipated RRSP tax credits.")
