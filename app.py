import streamlit as st
import pandas as pd
import altair as alt
import json

# --- CONFIGURATION ---
st.set_page_config(page_title="Retirement Architect Pro", layout="wide")
st.title("🏛️ Retirement Architect: Ultimate Strategy Pro")
st.markdown("### Strategy: High-Income Shielding & Early Retirement (2026)")

# --- SIDEBAR: PROFILE & INPUTS ---
with st.sidebar:
    st.header("👤 Income Profile")
    base_salary = st.number_input("Annual Base Salary ($)", value=180000, step=5000)
    bonus_pct = st.slider("Bonus Target (%)", 0, 50, 15)
    
    # Calculate Bonus and Gross
    bonus_amt = base_salary * (bonus_pct / 100)
    gross_income = base_salary + bonus_amt
    st.write(f"**Calculated Bonus:** ${bonus_amt:,.0f}")
    st.write(f"**Total Gross Income:** ${gross_income:,.0f}")
    
    st.header("💰 RRSP Contributions")
    biweekly_pct = st.slider("Biweekly Contribution (% of Base)", 0.0, 18.0, 6.0)
    employer_match = st.slider("Employer Match (% of Base)", 0.0, 10.0, 4.0)
    lump_sum = st.number_input("March 2nd Lump Sum ($)", value=10000, step=1000)
    
    st.header("📁 Initial Room (Before Strategy)")
    initial_rrsp_room = st.number_input("Current Unused RRSP Room ($)", value=146000)
    initial_tfsa_room = st.number_input("Current Unused TFSA Room ($)", value=102000)

# --- 2026 ONTARIO/FEDERAL TAX DATA ---
BRACKETS = [
    {"Floor": "Floor 1", "low": 0, "top": 53891, "rate": 0.1905},
    {"Floor": "Floor 2", "low": 53891, "top": 58523, "rate": 0.2315},
    {"Floor": "Floor 3", "low": 58523, "top": 94907, "rate": 0.2965},
    {"Floor": "Floor 4", "low": 94907, "top": 117045, "rate": 0.3148},
    {"Floor": "Floor 5", "low": 117045, "top": 181440, "rate": 0.4497}, 
    {"Floor": "Penthouse", "low": 181440, "top": 258482, "rate": 0.4829}
]

# --- CALCULATIONS ---
# 1. Total RRSP Contributions
annual_rrsp_periodic = base_salary * ((biweekly_pct + employer_match) / 100)
total_rrsp_contributions = annual_rrsp_periodic + lump_sum
taxable_income = gross_income - total_rrsp_contributions
tax_cliff = 181440 

# 2. Room Impact
final_rrsp_room = max(0, initial_rrsp_room - total_rrsp_contributions)
est_refund = total_rrsp_contributions * 0.46 
final_tfsa_room = max(0, initial_tfsa_room - est_refund)

# --- SAVE STRATEGY FUNCTION ---
strategy_export = {
    "Base Salary": base_salary,
    "Bonus %": bonus_pct,
    "Bonus Dollars": bonus_amt,
    "Total RRSP Contributions": total_rrsp_contributions,
    "Est Refund": est_refund,
    "Remaining RRSP Room": final_rrsp_room
}

# --- HEADER: ROOM TRACKER & SAVE ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.header("📊 Room & Strategy Execution")
with col_h2:
    st.download_button(
        label="💾 Save Strategy (JSON)",
        data=json.dumps(strategy_export, indent=4),
        file_name="retirement_strategy.json",
        mime="application/json"
    )

room_df = pd.DataFrame({
    "Account": ["RRSP Room", "TFSA Room"],
    "Starting Room": [f"${initial_rrsp_room:,.0f}", f"${initial_tfsa_room:,.0f}"],
    "Strategy Usage": [f"-${total_rrsp_contributions:,.0f}", f"-${est_refund:,.0f}"],
    "Post-Strategy Room": [f"${final_rrsp_room:,.0f}", f"${final_tfsa_room:,.0f}"]
})
st.table(room_df)

st.metric("Total RRSP Contributions", f"${total_rrsp_contributions:,.0f}")

# --- VISUALIZER: SPLIT-BAR TAX BUILDING ---
st.divider()
st.subheader("🏢 The Tax Building (Visual Impact)")
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

# --- STRATEGIC ACTION ITEMS ---
st.divider()
st.header("🛡️ Strategic Action Items")
tax_saved_on_bonus = bonus_amt * 0.4829

st.warning(f"**Bonus Shield:** If you receive your **${bonus_amt:,.0f}** bonus as cash, you lose roughly **${tax_saved_on_bonus:,.0f}** to immediate tax. Execute the direct-to-RRSP transfer to keep the full amount.")

c1, c2 = st.columns(2)
with c1:
    with st.expander("📝 March 2nd Checklist"):
        st.write(f"1. **Confirm Room:** Ensure your ${total_rrsp_contributions:,.0f} total is within limits.")
        st.write(f"2. **Lump Sum:** Submit ${lump_sum:,.0f} before March 2, 2026.")
        st.write(f"3. **T1213 Form:** Use total RRSP ${total_rrsp_contributions:,.0f} to reduce source tax.")
with c2:
    st.success(f"**TFSA Pivot:** Your refund of **${est_refund:,.0f}** should fill your TFSA to provide the tax-free 'bridge' needed for retirement at age 55.")

# --- RETIREMENT BRIDGE ---
st.divider()
st.subheader("🌉 The Age 55 Retirement Bridge")
bridge_df = pd.DataFrame({
    "Asset": ["TFSA (The Bridge)", "RRSP (The Foundation)", "CPP/OAS (Gov)"],
    "Role": ["Live on this Age 55-65", "Primary Income Age 65+", "Supporting Income Age 65+"],
    "Tax Status": ["Tax-Free", "Taxable", "Taxable"]
})
st.table(bridge_df)
