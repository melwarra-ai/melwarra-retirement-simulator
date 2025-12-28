import streamlit as st
import pandas as pd
import altair as alt

# --- APP CONFIG ---
st.set_page_config(page_title="Retirement Architect Pro", layout="wide")
st.title("🏛️ Retirement Architect: Path to Age 55")
st.markdown("### Strategy: High-Income Optimization (2026 Estimates)")

# --- SIDEBAR: USER PROFILE ---
with st.sidebar:
    st.header("👤 Income & Goals")
    gross_income = st.number_input("Total Gross (Salary + Bonus) ($)", value=200000, step=5000)
    base_salary = st.number_input("Annual Base Salary ($)", value=180000, step=5000)
    
    st.header("💰 RRSP & TFSA")
    biweekly_pct = st.slider("Biweekly Contribution (% of Base)", 0.0, 18.0, 6.0)
    employer_match = st.slider("Employer Match (% of Base)", 0.0, 10.0, 4.0)
    rrsp_room = st.number_input("Unused RRSP Room ($)", value=146000)
    tfsa_room = st.number_input("Unused TFSA Room ($)", value=102000)

# --- 2026 ONTARIO/FEDERAL COMBINED TAX BRACKETS ---
BRACKETS = [
    {"Floor": "Floor 1", "top": 53891, "rate": 0.1905},
    {"Floor": "Floor 2", "top": 58523, "rate": 0.2315},
    {"Floor": "Floor 3", "top": 94907, "rate": 0.2965},
    {"Floor": "Floor 4", "top": 117045, "rate": 0.3148},
    {"Floor": "Floor 5", "top": 181440, "rate": 0.4497}, 
    {"Floor": "Penthouse", "top": 258482, "rate": 0.4829},
    {"Floor": "Skyline", "top": 1000000, "rate": 0.5353}
]

# --- CALCULATIONS ---
annual_rrsp_periodic = base_salary * ((biweekly_pct + employer_match) / 100)
taxable_income = gross_income - annual_rrsp_periodic
tax_cliff = 181440 # Everything above this is taxed at ~48%+

# --- FEATURE 1: DYNAMIC TAX BUILDING (ALTAIR) ---
st.header("🏢 The Tax Building Visualizer")
st.write("Blue segments are income **shielded** by RRSP. Orange segments are **taxed**.")

building_data = []
prev_top = 0
for b in BRACKETS:
    slice_amt = min(gross_income, b['top']) - prev_top
    if slice_amt <= 0: break
    
    # Shielding Logic
    is_shielded = (prev_top >= taxable_income)
    status = "Shielded" if is_shielded else "Taxed"
    
    building_data.append({
        "Floor": b['Floor'], 
        "Amount": slice_amt, 
        "Status": status,
        "Rate": f"{b['rate']*100:.1f}%"
    })
    prev_top = b['top']

df_building = pd.DataFrame(building_data)

# Create the Altair Chart for perfect color control
chart = alt.Chart(df_building).mark_bar().encode(
    x=alt.X('Floor:N', sort=None),
    y='Amount:Q',
    color=alt.Color('Status:N', scale=alt.Scale(domain=['Shielded', 'Taxed'], range=['#3b82f6', '#f59e0b'])),
    tooltip=['Floor', 'Amount', 'Rate', 'Status']
).properties(height=400)

st.altair_chart(chart, use_container_width=True)

# --- FEATURE 2: MARCH 2nd DEADLINE TOOLKIT ---
st.divider()
st.header("📅 Tax Season Action: March 2nd")
premium_lump_sum = max(0, taxable_income - tax_cliff)
actual_lump = min(premium_lump_sum, rrsp_room)
tax_refund = actual_lump * 0.4829

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Income in 'Penthouse'", f"${premium_lump_sum:,.0f}")
    st.caption("Taxed at 48.3%—Primary target for RRSP.")
with c2:
    st.metric("Lump Sum Target", f"${actual_lump:,.0f}")
    st.caption("Contribute this by March 2 to maximize ROI.")
with c3:
    st.success(f"Est. Refund: ${tax_refund:,.0f}")
    st.caption("Reinvest this refund into your TFSA.")

# --- FEATURE 3: RETIREMENT BRIDGE & STRATEGY ---
st.divider()
st.subheader("🌉 Retirement Bridge & Bonus Strategy")

# Bonus Shield Strategy
bonus_amt = gross_income - base_salary
tax_on_bonus = bonus_amt * 0.4829

col_a, col_b = st.columns(2)
with col_a:
    st.info(f"**Bonus Shield:** Your ${bonus_amt:,.0f} bonus/commissions will lose **${tax_on_bonus:,.0f}** to tax if taken as cash. Use a direct RRSP transfer to keep 100% of it.")
with col_b:
    st.warning(f"**TFSA Pivot:** You have ${tfsa_room:,.0f} room. Use your RRSP refunds to fill this. This provides the tax-free 'bridge' you need to retire at 55.")

# Summary Table
st.write("### Retirement Strategy Summary")
summary_df = pd.DataFrame({
    "Action": ["RRSP (High Value)", "RRSP (Low Value)", "TFSA"],
    "Income Target": [f"Above ${tax_cliff:,.0f}", f"Below ${tax_cliff:,.0f}", "Anywhere"],
    "Priority": ["1st - Immediate 48% ROI", "3rd - Tax Deferral only", "2nd - Tax-Free Growth"]
})
st.table(summary_df)
