import streamlit as st
import pandas as pd
import altair as alt
import json
import os
import streamlit.components.v1 as components

# --- 1. PERSISTENCE ENGINE ---
SAVE_FILE = "retirement_data.json"

def save_to_file(data):
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)
        return True
    except Exception as e:
        return False

def load_from_file():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

saved_data = load_from_file()

# --- 2. CONFIGURATION & CSS ---
st.set_page_config(page_title="Retirement Architect Pro", layout="wide")

st.markdown("""
    <style>
    @media print {
        div[data-testid="stSidebar"], div.stButton, button, header, footer, .stDownloadButton { display: none !important; }
        .main .block-container { padding-top: 1rem !important; max-width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Retirement Architect: Master Strategy Pro")

# --- 3. SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("👤 Income Inputs")
    
    # LOGIC RULE 1: Used ONLY for Tax Building Visualizer
    t4_gross_income = st.number_input(
        "T4 Gross Income (Total)", 
        value=saved_data.get("t4_gross_income", 235000), 
        step=5000,
        help="This is the total T4 gross reported in your T4 document (Box 14). Used for visualizer only.",
        key="t4_gross_income"
    )
    
    # LOGIC RULE 2: Used ONLY for Biweekly Calculation
    base_salary = st.number_input(
        "Annual Base Salary ($)", 
        value=saved_data.get("base_salary", 180000), 
        step=5000, 
        help="Used strictly to calculate employer match and biweekly %.",
        key="base_salary"
    )
    
    st.header("💰 Periodic Contributions (RRSP Only)")
    biweekly_pct = st.slider(
        "Biweekly RRSP (%)", 0.0, 18.0, 
        value=saved_data.get("biweekly_pct", 6.0), 
        key="biweekly_pct"
    )
    
    employer_match = st.slider(
        "Employer Match (%)", 0.0, 10.0, 
        value=saved_data.get("employer_match", 4.0), 
        key="employer_match"
    )
    
    st.header("📅 March 1st Bulk Actions")
    rrsp_lump_sum = st.number_input(
        "RRSP Lump Sum ($)", 
        value=saved_data.get("rrsp_lump_sum", 10000),
        step=1000,
        key="rrsp_lump_sum"
    )
    
    tfsa_lump_sum = st.number_input(
        "TFSA Lump Sum ($)", 
        value=saved_data.get("tfsa_lump_sum", 7000),
        step=1000,
        key="tfsa_lump_sum"
    )
    
    st.header("📁 Available Room")
    rrsp_room = st.number_input("Unused RRSP Room", value=saved_data.get("rrsp_room", 146000), key="rrsp_room")
    tfsa_room = st.number_input("Unused TFSA Room", value=saved_data.get("tfsa_room", 102000), key="tfsa_room")

    st.divider()
    
    # SAVE / RESET BUTTONS
    c_save, c_reset = st.columns(2)
    with c_save:
        if st.button("💾 Save Inputs"):
            current_state = {
                "t4_gross_income": t4_gross_income,
                "base_salary": base_salary,
                "biweekly_pct": biweekly_pct,
                "employer_match": employer_match,
                "rrsp_lump_sum": rrsp_lump_sum,
                "tfsa_lump_sum": tfsa_lump_sum,
                "rrsp_room": rrsp_room,
                "tfsa_room": tfsa_room
            }
            if save_to_file(current_state):
                st.success("Saved!")
    
    with c_reset:
        if st.button("🔄 Reset"):
            if os.path.exists(SAVE_FILE): os.remove(SAVE_FILE)
            st.rerun()

# --- 4. CALCULATIONS ---
# RRSP Logic: Periodic is based on Base Salary, Total includes Lump Sum
annual_rrsp_periodic = base_salary * ((biweekly_pct + employer_match) / 100)
total_rrsp_contributions = annual_rrsp_periodic + rrsp_lump_sum

# Taxable Income for Chart: Based on T4 Gross
taxable_income_for_chart = t4_gross_income - total_rrsp_contributions
tax_cliff = 181440 

# Room Updates
final_rrsp_room = max(0, rrsp_room - total_rrsp_contributions)
final_tfsa_room = max(0, tfsa_room - tfsa_lump_sum)
est_refund = total_rrsp_contributions * 0.46

# --- 5. HEADER & PRINT ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.header("📊 Strategy Execution Dashboard")
with col_h2:
    print_btn = """<script>function print_page() { window.print(); }</script>
    <button onclick="print_page()" style="padding: 10px 20px; background-color: #3b82f6; color: white; border: none; border-radius: 5px; cursor: pointer; width: 100%; font-weight: bold;">🖨️ Print / Save PDF</button>"""
    components.html(print_btn, height=60)

# --- 6. ROOM TRACKER ---
room_df = pd.DataFrame({
    "Account": ["RRSP Room", "TFSA Room"],
    "Starting Room": [f"${rrsp_room:,.0f}", f"${tfsa_room:,.0f}"],
    "Strategy Usage": [f"-${total_rrsp_contributions:,.0f} (Periodic + Bulk)", f"-${tfsa_lump_sum:,.0f} (Bulk Only)"],
    "Post-Strategy Room": [f"${final_rrsp_room:,.0f}", f"${final_tfsa_room:,.0f}"]
})
st.table(room_df)

# --- 7. ACTION: BEFORE MARCH 1st ---
st.divider()
st.header("📅 Action Plan: Before March 1st")
st.markdown("These actions must be executed before the deadline to impact your 2025 tax return.")

ac1, ac2, ac3 = st.columns(3)
with ac1:
    st.subheader("1. RRSP Bulk")
    st.metric("Lump Sum Target", f"${rrsp_lump_sum:,.0f}")
    st.caption("Execute this transfer to clear your Penthouse tax bracket.")

with ac2:
    st.subheader("2. TFSA Bulk")
    st.metric("Lump Sum Target", f"${tfsa_lump_sum:,.0f}")
    st.caption("Invest this amount into your TFSA (No tax deduction, tax-free growth).")

with ac3:
    st.subheader("3. The Reward")
    st.metric("Est. Tax Refund", f"${est_refund:,.0f}")
    st.caption("Reinvest this refund immediately when it arrives in April/May.")

# --- 8. TAX BUILDING VISUALIZER ---
st.divider()
st.subheader("🏢 The Tax Building (Progressive Shielding)")
BRACKETS = [
    {"Floor": "Floor 1", "low": 0, "top": 53891, "rate": 0.1905},
    {"Floor": "Floor 2", "low": 53891, "top": 58523, "rate": 0.2315},
    {"Floor": "Floor 3", "low": 58523, "top": 94907, "rate": 0.2965},
    {"Floor": "Floor 4", "low": 94907, "top": 117045, "rate": 0.3148},
    {"Floor": "Floor 5", "low": 117045, "top": 181440, "rate": 0.4497}, 
    {"Floor": "Penthouse", "low": 181440, "top": 258482, "rate": 0.4829}
]

building_data = []
for b in BRACKETS:
    # Use T4 Gross for chart height
    total_in_bracket = min(t4_gross_income, b['top']) - b['low']
    if total_in_bracket <= 0: continue
    
    # Use Total RRSP (Periodic + Lump) to calculate shielding
    taxed_amt = max(0, min(b['top'], taxable_income_for_chart) - b['low'])
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

# --- 9. SUMMARY ---
st.divider()
st.subheader("📊 Retirement Strategy Summary")
summary_df = pd.DataFrame({
    "Action": ["RRSP (High Value)", "RRSP (Low Value)", "TFSA"],
    "Current Impact": [
        f"${max(0, taxable_income_for_chart - tax_cliff):,.0f} still in Penthouse",
        f"${min(taxable_income_for_chart, tax_cliff):,.0f} in lower floors",
        f"${final_tfsa_room:,.0f} available room"
    ],
    "Priority": ["1st - Immediate 48% ROI", "3rd - Tax Deferral only", "2nd - Tax-Free Growth"]
})
st.table(summary_df)
