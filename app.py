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
    except:
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

# --- 2. CONFIGURATION & PDF PRINT STYLING ---
st.set_page_config(page_title="Retirement Architect Pro", layout="wide")

st.markdown("""
    <style>
    @media print {
        div[data-testid="stSidebar"], .stButton, button, header, footer, [data-testid="stToolbar"] {
            display: none !important;
        }
        .main .block-container {
            max-width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Retirement Architect: Master Strategy Pro")
st.write("This tool generates a comprehensive retirement strategy based on your T4 income and savings targets.")

# --- 3. SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("👤 Income Inputs")
    st.info("Input your T4 details. These numbers are used to calculate your 'Tax Building' height.")
    
    t4_gross_income = st.number_input(
        "T4 Gross Income (Total)", 
        value=float(saved_data.get("t4_gross_income", 0)), 
        step=5000.0,
        key="t4_gross_income"
    )
    
    base_salary = st.number_input(
        "Annual Base Salary ($)", 
        value=float(saved_data.get("base_salary", 0)), 
        step=5000.0, 
        key="base_salary"
    )
    
    st.header("💰 RRSP Payroll Setup")
    biweekly_pct = st.slider("Biweekly RRSP (%)", 0.0, 18.0, value=float(saved_data.get("biweekly_pct", 0.0)), key="biweekly_pct")
    employer_match = st.slider("Employer Match (%)", 0.0, 10.0, value=float(saved_data.get("employer_match", 0.0)), key="employer_match")
    
    st.header("📅 Bulk Contributions")
    rrsp_lump_sum = st.number_input("RRSP Lump Sum ($)", value=float(saved_data.get("rrsp_lump_sum", 0)), key="rrsp_lump_sum")
    tfsa_lump_sum = st.number_input("TFSA Lump Sum ($)", value=float(saved_data.get("tfsa_lump_sum", 0)), key="tfsa_lump_sum")
    
    st.header("📁 Room Registry")
    rrsp_room = st.number_input("Unused RRSP Room", value=float(saved_data.get("rrsp_room", 0)), key="rrsp_room")
    tfsa_room = st.number_input("Unused TFSA Room", value=float(saved_data.get("tfsa_room", 0)), key="tfsa_room")

    st.divider()
    
    c_save, c_reset = st.columns(2)
    with c_save:
        if st.button("💾 Save Inputs"):
            current_state = {
                "t4_gross_income": t4_gross_income, "base_salary": base_salary,
                "biweekly_pct": biweekly_pct, "employer_match": employer_match,
                "rrsp_lump_sum": rrsp_lump_sum, "tfsa_lump_sum": tfsa_lump_sum,
                "rrsp_room": rrsp_room, "tfsa_room": tfsa_room
            }
            save_to_file(current_state)
            st.success("Saved!")
    
    with c_reset:
        if st.button("🔄 Reset to 0"):
            if os.path.exists(SAVE_FILE): 
                os.remove(SAVE_FILE)
            st.session_state.clear()
            st.rerun()

# --- 4. CALCULATIONS ---
annual_rrsp_periodic = base_salary * ((biweekly_pct + employer_match) / 100)
total_rrsp_contributions = annual_rrsp_periodic + rrsp_lump_sum
taxable_income_for_chart = t4_gross_income - total_rrsp_contributions

final_rrsp_room = max(0.0, rrsp_room - total_rrsp_contributions)
final_tfsa_room = max(0.0, tfsa_room - tfsa_lump_sum)
est_refund = total_rrsp_contributions * 0.46

# --- 5. REPORT HEADER & PDF BUTTON ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.header("📋 Retirement Strategy Report")
with col_h2:
    components.html("""
        <button onclick="window.print()" style="
            width: 100%; height: 50px; background-color: #3b82f6; color: white; 
            border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">
            📄 Save as PDF
        </button>
    """, height=70)

# --- 6. ROOM TRACKER ---
st.divider()
st.subheader("🏦 Registration Room Status")
room_df = pd.DataFrame({
    "Account": ["RRSP Room", "TFSA Room"],
    "Starting": [f"${rrsp_room:,.0f}", f"${tfsa_room:,.0f}"],
    "Usage": [f"-${total_rrsp_contributions:,.0f}", f"-${tfsa_lump_sum:,.0f}"],
    "Remaining": [f"${final_rrsp_room:,.0f}", f"${final_tfsa_room:,.0f}"]
})
st.table(room_df)

# --- 7. ACTION PLAN ---
st.divider()
st.subheader("📅 March 1st Deadlines")
ac1, ac2, ac3 = st.columns(3)
with ac1:
    st.metric("RRSP Bulk Deposit", f"${rrsp_lump_sum:,.0f}")
with ac2:
    st.metric("TFSA Bulk Deposit", f"${tfsa_lump_sum:,.0f}")
with ac3:
    st.metric("Expected Tax Refund", f"${est_refund:,.0f}")

# --- 8. THE TAX BUILDING ---
st.divider()
st.subheader("🏢 The Tax Building Visualizer")

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
    total_in_bracket = min(t4_gross_income, b['top']) - b['low']
    if total_in_bracket <= 0: continue
    taxed_amt = max(0, min(b['top'], taxable_income_for_chart) - b['low'])
    shielded_amt = total_in_bracket - taxed_amt
    if shielded_amt > 0:
        building_data.append({"Floor": b['Floor'], "Amount": shielded_amt, "Status": "Shielded", "Rate": f"{b['rate']*100:.1f}%"})
    if taxed_amt > 0:
        building_data.append({"Floor": b['Floor'], "Amount": taxed_amt, "Status": "Taxed", "Rate": f"{b['rate']*100:.1f}%"})

# FIXED: Check if building_data is empty before rendering chart
if not building_data:
    st.info("Enter a T4 Gross Income in the sidebar to visualize your Tax Building.")
else:
    chart = alt.Chart(pd.DataFrame(building_data)).mark_bar().encode(
        x=alt.X('Floor:N', sort=None),
        y=alt.Y('Amount:Q', title="Income ($)"),
        color=alt.Color('Status:N', scale=alt.Scale(domain=['Shielded', 'Taxed'], range=['#3b82f6', '#f59e0b'])),
        tooltip=['Floor', 'Amount', 'Rate', 'Status']
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)
