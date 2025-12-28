import streamlit as st
import pandas as pd
import altair as alt
import streamlit.components.v1 as components

# --- CONFIGURATION ---
st.set_page_config(page_title="Retirement Architect Pro", layout="wide")

# --- CSS FOR CLEAN PRINTING ---
st.markdown("""
    <style>
    @media print {
        div[data-testid="stSidebar"], 
        div.stButton, 
        button,
        header,
        footer,
        .stDownloadButton {
            display: none !important;
        }
        .main .block-container {
            padding-top: 1rem !important;
            max-width: 100% !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Retirement Architect: Master Strategy Pro")

# --- SIDEBAR: ALL SETTINGS (Combined) ---
with st.sidebar:
    st.header("👤 Income Profile")
    # Feature: Manual Gross Entry
    gross_income = st.number_input("Total Annual Gross Income ($)", value=235000, step=5000, help="Base + Bonus + All other income")
    bonus_amt = st.number_input("Portion that is Bonus ($)", value=55000, step=1000)
    
    st.header("💰 RRSP Strategy")
    base_salary_calc = st.number_input("Base Salary for Biweekly Calc ($)", value=180000)
    biweekly_pct = st.slider("Biweekly Contribution (%)", 0.0, 18.0, 6.0)
    employer_match = st.slider("Employer Match (%)", 0.0, 10.0, 4.0)
    lump_sum = st.number_input("March 2nd Lump Sum ($)", value=10000, step=1000)
    
    st.header("📁 Room Status")
    initial_rrsp_room = st.number_input("Current RRSP Room ($)", value=146000)
    initial_tfsa_room = st.number_input("Current TFSA Room ($)", value=102000)

# --- CALCULATIONS (All Versions Merged) ---
# Total RRSP Impact
annual_rrsp_periodic = base_salary_calc * ((biweekly_pct + employer_match) / 100)
total_rrsp_contributions = annual_rrsp_periodic + lump_sum
taxable_income = gross_income - total_rrsp_contributions

# Room Logic
final_rrsp_room = max(0, initial_rrsp_room - total_rrsp_contributions)
est_refund = total_rrsp_contributions * 0.46 # Marginal rate for high earners
final_tfsa_room = max(0, initial_tfsa_room - est_refund)

# --- UI HEADER & SAVE BUTTON ---
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.header("📊 Strategy Execution & Room Tracking")
with col_h2:
    # Feature: Save UI (Print to PDF)
    print_btn = """
    <script>
    function save_ui() { window.print(); }
    </script>
    <button onclick="save_ui()" style="padding: 12px 24px; background-color: #3b82f6; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%;">
        💾 Save Strategy (PDF)
    </button>
    """
    components.html(print_btn, height=70)

# --- FEATURE: ROOM TRACKING TABLE ---
room_df = pd.DataFrame({
    "Account": ["RRSP Room", "TFSA Room"],
    "Starting Room": [f"${initial_rrsp_room:,.0f}", f"${initial_tfsa_room:,.0f}"],
    "Strategy Usage": [f"-${total_rrsp_contributions:,.0f}", f"-${est_refund:,.0f}"],
    "Post-Strategy Room": [f"${final_rrsp_room:,.0f}", f"${final_tfsa_room:,.0f}"]
})
st.table(room_df)
st.metric("Total Planned RRSP Contributions", f"${total_rrsp_contributions:,.0f}")

# --- FEATURE: TAX BUILDING VISUALIZER ---
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

# --- FEATURE: STRATEGIC ACTION ITEMS ---
st.divider()
st.header("🛡️ Strategic Action Items")
tax_saved_on_bonus = bonus_amt * 0.4829

# Feature: Correct Bonus Wording
st.warning(f"**Bonus Shield:** If you receive your **${bonus_amt:,.0f}** bonus as cash, you lose roughly **${tax_saved_on_bonus:,.0f}** to immediate tax. Execute the direct-to-RRSP transfer to keep the full amount.")

c1, c2 = st.columns(2)
with c1:
    # Feature: Checklist (from Version 2)
    with st.expander("📝 Implementation Checklist", expanded=True):
        st.write(f"- **March 2 Deadline:** Deposit **${lump_sum:,.0f}** as a lump sum.")
        st.write(f"- **T1213 Form:** Use **${total_rrsp_contributions:,.0f}** as your deduction target.")
        st.write("- **Employer Match:** Confirm your contribution matches the full employer cap.")
with c2:
    st.success(f"**TFSA Pivot:** Direct your estimated refund of **${est_refund:,.0f}** into the TFSA to build the Age 55 'Tax-Free Bridge'.")

# --- FEATURE: RETIREMENT BRIDGE ---
st.divider()
st.subheader("🌉 The Age 55 Retirement Bridge")
bridge_df = pd.DataFrame({
    "Asset": ["TFSA (The Bridge)", "RRSP (The Foundation)", "CPP/OAS (Gov)"],
    "Withdrawal Strategy": ["Income from Age 55-65", "Primary income Age 65+", "Supplemental income Age 65+"],
    "Tax Status": ["Tax-Free", "Taxable", "Taxable"]
})
st.table(bridge_df)
