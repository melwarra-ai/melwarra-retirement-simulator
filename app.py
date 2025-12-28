import streamlit as st
import pandas as pd
import altair as alt

# --- CONFIGURATION & PERSISTENCE ---
st.set_page_config(page_title="Retirement Architect Pro", layout="wide")

# Initialization of Session State
if 'init' not in st.session_state:
    st.session_state.init = True

st.title("🏛️ Retirement Architect: Master Strategy Pro")

# --- SIDEBAR: ALL INPUTS ---
with st.sidebar:
    st.header("👤 Income Profile")
    
    # 1. Manual T4 Gross Entry (Other)
    t4_gross_other = st.number_input(
        "T4 Gross Income (Other)", 
        value=0, 
        help="Additional taxable income NOT including base salary or bonus.",
        key="t4_gross_other"
    )
    
    base_salary = st.number_input("Annual Base Salary ($)", value=180000, step=5000, key="base_salary")
    bonus_pct = st.slider("Target Bonus (%)", 0, 50, 15, key="bonus_pct")
    
    # Combined Income Calculation
    bonus_amt = base_salary * (bonus_pct / 100)
    gross_income = base_salary + bonus_amt + t4_gross_other
    
    st.info(f"**Total Gross Income:** ${gross_income:,.0f}")
    
    st.header("💰 RRSP & TFSA")
    biweekly_pct = st.slider("Biweekly Contribution (%)", 0.0, 18.0, 6.0, key="biweekly_pct")
    employer_match = st.slider("Employer Match (%)", 0.0, 10.0, 4.0, key="employer_match")
    rrsp_room = st.number_input("Unused RRSP Room ($)", value=146000, key="rrsp_room")
    tfsa_room = st.number_input("Unused TFSA Room ($)", value=102000, key="tfsa_room")

    st.divider()
    # Feature: Reset Button
    if st.button("🔄 Reset to Defaults"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

# --- 2026 TAX BRACKETS ---
BRACKETS = [
    {"Floor": "Floor 1", "low": 0, "top": 53891, "rate": 0.1905},
    {"Floor": "Floor 2", "low": 53891, "top": 58523, "rate": 0.2315},
    {"Floor": "Floor 3", "low": 58523, "top": 94907, "rate": 0.2965},
    {"Floor": "Floor 4", "low": 94907, "top": 117045, "rate": 0.3148},
    {"Floor": "Floor 5", "low": 117045, "top": 181440, "rate": 0.4497}, 
    {"Floor": "Penthouse", "low": 181440, "top": 258482, "rate": 0.4829}
]

# --- CALCULATIONS ---
annual_rrsp_periodic = base_salary * ((biweekly_pct + employer_match) / 100)
taxable_income = gross_income - annual_rrsp_periodic
tax_cliff = 181440 

# --- VISUALIZER: TAX BUILDING ---
st.header("🏢 The Tax Building Visualizer")
st.write("Blue segments are income **shielded** by RRSP. Orange segments are **taxed**.")

building_data = []
for b in BRACKETS:
    total_in_bracket = min(gross_income, b['top']) - b['low']
    if total_in_bracket <= 0: continue
    
    taxed_amt = max(0, min(b['top'], taxable_income) - b['low'])
    shielded_amt = total_in_bracket - taxed_amt
    
    if shielded_amt > 0:
        building_data.append({"Floor": b['Floor'], "Amount": shielded_amt, "Status": "Shielded", "Rate": f"{b['rate']*100:.1f}%"})
    if taxed_amt > 0:
        building_data.append({"Floor": b['Floor'], "Amount": taxed_amt, "Status": "Taxed", "Rate": f"{b['rate']*100:.1f}%"})

chart = alt.Chart(pd.DataFrame(building_data)).mark_bar().encode(
    x=alt.X('Floor:N', sort=None),
    y=alt.Y('Amount:Q', title="Income ($)"),
    color=alt.Color('Status:N', scale=alt.Scale(domain=['Shielded', 'Taxed'], range=['#3b82f6', '#f59e0b'])),
    tooltip=['Floor', 'Amount', 'Rate', 'Status']
).properties(height=400)
st.altair_chart(chart, use_container_width=True)

# --- FEATURE: MARCH 2nd DEADLINE TOOLKIT ---
st.divider()
st.header("📅 Tax Season Action: March 2nd")
premium_lump_sum = max(0, taxable_income - tax_cliff)
actual_lump = min(premium_lump_sum, rrsp_room)
tax_refund = (annual_rrsp_periodic + actual_lump) * 0.46

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Income in 'Penthouse'", f"${premium_lump_sum:,.0f}")
    st.caption("Income currently exposed to 48.3% tax.")
with c2:
    st.metric("Lump Sum Target", f"${actual_lump:,.0f}")
    st.caption("Max efficient contribution for March 2.")
with c3:
    st.success(f"Est. Strategy Refund: ${tax_refund:,.0f}")
    st.caption("Total tax recovered from this strategy.")

# --- FEATURE: STRATEGY SUMMARY & ACTION ITEMS ---
st.divider()
st.subheader("📊 Retirement Strategy Summary")
summary_df = pd.DataFrame({
    "Action": ["RRSP (High Value)", "RRSP (Low Value)", "TFSA"],
    "Current Impact": [
        f"${max(0, taxable_income - tax_cliff):,.0f} still in Penthouse",
        f"${min(taxable_income, tax_cliff):,.0f} in lower floors",
        f"${tfsa_room:,.0f} available room"
    ],
    "Priority": ["1st - Immediate 48% ROI", "3rd - Tax Deferral only", "2nd - Tax-Free Growth"]
})
st.table(summary_df)

# --- BONUS SHIELD & T1213 ---
tax_on_bonus = bonus_amt * 0.4829
col_a, col_b = st.columns(2)
with col_a:
    st.info(f"**Bonus Shield:** Your ${bonus_amt:,.0f} bonus will lose **${tax_on_bonus:,.0f}** to tax if taken as cash.")
with col_b:
    with st.expander("📝 Data for T1213 (Tax Waiver)"):
        st.write(f"- Total Planned RRSP: **${annual_rrsp_periodic + actual_lump:,.0f}**")
        st.write(f"- Monthly Refund Boost: ~**${((annual_rrsp_periodic + actual_lump) * 0.45)/12:,.0f}/mo**")
