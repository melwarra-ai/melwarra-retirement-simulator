import streamlit as st
import pandas as pd
import altair as alt
import json
import os

# --- 1. PERSISTENCE ENGINE (JSON FILE) ---
# This ensures that even if you refresh or close the browser, your data is safe.
SAVE_FILE = "retirement_history.json"

def load_all_data():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_year_data(year, data):
    all_data = load_all_data()
    all_data[str(year)] = data
    with open(SAVE_FILE, "w") as f:
        json.dump(all_data, f)

def delete_year_data(year):
    all_data = load_all_data()
    if str(year) in all_data:
        del all_data[str(year)]
        with open(SAVE_FILE, "w") as f:
            json.dump(all_data, f)

all_history = load_all_data()

# --- 2. SESSION STATE & NAVIGATION ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"
if "selected_year" not in st.session_state:
    st.session_state.selected_year = 2025

st.set_page_config(page_title="Strategic Tax Planner", layout="wide")

# --- 3. PAGE: HOME (NET WORTH & AGGREGATE DASHBOARD) ---
if st.session_state.current_page == "Home":
    st.title("🏠 Strategic Portfolio Dashboard")
    
    # AGGREGATE NET WORTH SUMMARY
    if all_history:
        st.subheader("💰 Total Tracked Portfolio")
        total_rrsp = 0
        total_tfsa = 0
        chart_data = []

        for yr, data in all_history.items():
            ann_rrsp = (data.get('base_salary', 0) * (data.get('biweekly_pct', 0) + data.get('employer_match', 0)) / 100) + data.get('rrsp_lump_sum', 0)
            ann_tfsa = data.get('tfsa_lump_sum', 0)
            total_rrsp += ann_rrsp
            total_tfsa += ann_tfsa
            chart_data.append({"Year": str(yr), "RRSP": ann_rrsp, "TFSA": ann_tfsa})

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Sheltered RRSP", f"${total_rrsp:,.0f}")
        m2.metric("Total Sheltered TFSA", f"${total_tfsa:,.0f}")
        m3.metric("Combined Progress", f"${total_rrsp + total_tfsa:,.0f}")

        st.divider()

    st.subheader("📅 Select Planning Year")
    cols = st.columns(4)
    for i, yr in enumerate(range(2024, 2028)):
        with cols[i % 4]:
            is_saved = str(yr) in all_history
            btn_label = f"📅 {yr} {'(SAVED)' if is_saved else '(EMPTY)'}"
            if st.button(btn_label, use_container_width=True):
                st.session_state.selected_year = yr
                st.session_state.current_page = "Year View"
                st.rerun()

# --- 4. PAGE: YEAR VIEW (TAX DRILLDOWN) ---
else:
    selected_year = st.session_state.selected_year
    year_data = all_history.get(str(selected_year), {})

    with st.sidebar:
        if st.button("⬅️ Back to Home"):
            st.session_state.current_page = "Home"
            st.rerun()
        
        st.header(f"⚙️ {selected_year} Inputs")
        gross = st.number_input("T4 Gross Income", value=float(year_data.get("t4_gross_income", 0)))
        base = st.number_input("Base Salary", value=float(year_data.get("base_salary", 0)))
        biweekly = st.slider("Biweekly RRSP %", 0.0, 18.0, value=float(year_data.get("biweekly_pct", 0.0)))
        match = st.slider("Employer Match %", 0.0, 10.0, value=float(year_data.get("employer_match", 0.0)))
        rrsp_bulk = st.number_input("RRSP Bulk Deposit", value=float(year_data.get("rrsp_lump_sum", 0)))
        tfsa_bulk = st.number_input("TFSA Bulk Deposit", value=float(year_data.get("tfsa_lump_sum", 0)))
        rrsp_r = st.number_input("Unused RRSP Room", value=float(year_data.get("rrsp_room", 0)))
        tfsa_r = st.number_input("Unused TFSA Room", value=float(year_data.get("tfsa_room", 0)))

        if st.button("💾 SAVE DATA FOR RELOAD", use_container_width=True, type="primary"):
            save_year_data(selected_year, {
                "t4_gross_income": gross, "base_salary": base, "biweekly_pct": biweekly,
                "employer_match": match, "rrsp_lump_sum": rrsp_bulk, "tfsa_lump_sum": tfsa_bulk,
                "rrsp_room": rrsp_r, "tfsa_room": tfsa_r
            })
            st.success("Data written to local JSON!")

    st.title(f"🏛️ {selected_year} Optimization")
    
    # CALCULATIONS
    total_rrsp = (base * (biweekly + match) / 100) + rrsp_bulk
    est_refund = total_rrsp * 0.46
    
    # TAX REFUND REINVESTMENT SECTION
    st.subheader("🔄 Refund Reinvestment Logic")
    rc1, rc2 = st.columns(2)
    with rc1:
        st.info(f"Generated RRSP Refund: **${est_refund:,.2f}**")
    with rc2:
        reinvested_total = est_refund + tfsa_bulk
        st.success(f"New TFSA Velocity: **${reinvested_total:,.2f}**")
        st.caption("This combines your bulk deposit + your reinvested tax refund.")

    # TAX BRACKET REFERENCE TABLE
    st.divider()
    st.subheader("📑 Ontario & Federal Combined Brackets")
    brackets = [
        {"Floor": "$0", "Rate": "20.05%"}, {"Floor": "$53,891", "Rate": "24.15%"},
        {"Floor": "$58,523", "Rate": "29.65%"}, {"Floor": "$94,907", "Rate": "31.48%"},
        {"Floor": "$117,045", "Rate": "33.89%"}, {"Floor": "$181,440 (Penthouse)", "Rate": "47.97%"}
    ]
    st.table(pd.DataFrame(brackets))
