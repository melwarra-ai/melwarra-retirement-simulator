import streamlit as st
import pandas as pd
import altair as alt

# --- CONFIGURATION ---
st.set_page_config(page_title="Retirement Architect Pro", layout="wide")
st.title("🏢 Retirement Architect: Room & Strategy Tracker")

# --- SIDEBAR: PROFILE & INPUTS ---
with st.sidebar:
    st.header("👤 Income Profile")
    gross_income = st.number_input("Total Gross (Salary + Bonus) ($)", value=200000, step=5000)
    base_salary = st.number_input("Annual Base Salary ($)", value=180000, step=5000)
    
    st.header("💰 RRSP Contributions")
    biweekly_pct = st.slider("Biweekly Contribution (% of Base)", 0.0, 18.0, 6.0)
    employer_match = st.slider("Employer Match (% of Base)", 0.0, 10.0, 4.0)
    lump_sum = st.number_input("March 2nd Lump Sum ($)", value=10000, step=1000)
    
    st.header("📁 Room (Pre-Strategy)")
    # User inputs their current room as seen on CRA MyAccount
    initial_rrsp_room = st.number_input("Current Unused RRSP Room ($)", value=146000)
    initial_tfsa_room = st.number_input("Current Unused TFSA Room ($)", value=102000)

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
# 1. Periodic contributions (Year-long)
annual_rrsp_periodic = base_salary * ((biweekly_pct + employer_match) / 100)
# 2. Total RRSP Contributions for the tax year
total_rrsp_contributions = annual_rrsp_periodic + lump_sum
# 3. Taxable Income
taxable_income = gross_income - total_rrsp_contributions
# 4. Refund calculation (Conservative estimate based on marginal rate)
est_refund = total_rrsp_contributions * 0.45 

# --- UPDATED ROOM LOGIC ---
# RRSP Room: Reduced by both periodic and lump sum
final_rrsp_room = max(0, initial_rrsp_room - total_rrsp_contributions)
# TFSA Room Strategy: Assume user moves the Refund into TFSA
final_tfsa_room = max(0, initial_tfsa_room - est_refund)

# --- FEATURE: ROOM TRACKER TABLE ---
st.header("📊 Room & Strategy Execution")
room_data = {
    "Account": ["RRSP Room", "TFSA Room"],
    "Starting Room": [f"${initial_rrsp_room:,.0f}", f"${initial_tfsa_room:,.0f}"],
    "Strategy Usage": [f"-${total_rrsp_contributions:,.0f}", f"-${est_refund:,.0f}"],
    "Post-Strategy Room": [f"${final_rrsp_room:,.0f}", f"${final_tfsa_room:,.0f}"]
}
st.table(pd.DataFrame(room_data))

# --- TOTAL CONTRIBUTIONS SUMMARY ---
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Total RRSP Contributions", f"${total_rrsp_contributions:,.0f}")
    st.caption("Includes Periodic + Lump Sum")
with c2:
    st.metric("Annual Tax Shield", f"${total_rrsp_contributions:,.0f}")
    st.caption("Income removed from top brackets")
with c3:
    st.success(f"Strategy Refund: ${est_refund:,.0f}")
    st.caption("Target for TFSA injection")

# --- VISUALIZER: SPLIT-BAR TAX BUILDING ---
st.divider()
st.subheader("🏢 The Tax Building: Visual Impact")
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

# --- BONUS & ACTION ITEMS ---
st.divider()
st.subheader("🛡️ Strategic Action Items")
bonus_amt = gross_income - base_salary
st.info(f"**Bonus Shield:** If you receive your ${bonus_amt:,.0f} bonus as cash, you lose roughly **${bonus_amt * 0.48:,.0f}** to immediate tax. Execute the direct-to-RRSP transfer to keep the full amount.")

with st.expander("📝 March 2nd Checklist"):
    st.write(f"1. **Confirm Room:** Ensure your total ${total_rrsp_contributions:,.0f} doesn't exceed your NOA limit.")
    st.write(f"2. **Lump Sum:** Execute the ${lump_sum:,.0f} payment before March 2, 2026.")
    st.write(f"3. **TFSA Reinvestment:** Once the refund of ~${est_refund:,.0f} arrives, inject it into your TFSA.")
