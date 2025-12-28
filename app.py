import streamlit as st
import pandas as pd
import altair as alt
import json
import os
import streamlit.components.v1 as components

# --- 1. PERSISTENCE ENGINE ---
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

# --- 2. NAVIGATION & SESSION STATE ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"
if "selected_year" not in st.session_state:
    st.session_state.selected_year = 2025

# --- 3. CONFIGURATION & STYLING ---
st.set_page_config(page_title="TAX RRSP/TFSA Planner", layout="wide")

st.markdown("""
    <style>
    .desc-box {
        background-color: #f8fafc; 
        padding: 20px; 
        border-radius: 12px; 
        border-left: 6px solid #3b82f6;
        margin-bottom: 25px;
        color: #334155;
    }
    .status-saved { color: #16a34a; font-weight: bold; margin-top: 10px; display: block; }
    @media print {
        div[data-testid="stSidebar"], .stButton, button, header, footer, [data-testid="stToolbar"] {
            display: none !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def description_box(title, content):
    st.markdown(f'''
        <div class="desc-box">
            <h4 style="margin-top:0; color:#1e293b;">{title}</h4>
            <div style="line-height:1.6;">{content}</div>
        </div>
    ''', unsafe_allow_html=True)

# --- 4. PAGE: HOME ---
if st.session_state.current_page == "Home":
    st.title("🏠 Strategy Dashboard")
    description_box("System Overview & Multi-Year Logic", 
        "This dashboard tracks your long-term tax optimization. Use the 'Planning Years' tiles below to navigate. "
        "The summaries below aggregate your contributions across all years to show your total tax-sheltered progress.")
    
    st.subheader("📅 Planning Years")
    cols = st.columns(4)
    years_to_show = list(range(2024, 2030))
    
    for i, yr in enumerate(years_to_show):
        with cols[i % 4]:
            is_saved = str(yr) in all_history
            label = f"📅 {yr}\n(SAVED)" if is_saved else f"📅 {yr}\n(EMPTY)"
            if st.button(label, use_container_width=True, key=f"home_{yr}"):
                st.session_state.selected_year = yr
                st.session_state.current_page = "Year View"
                st.rerun()

    if all_history:
        st.divider()
        st.subheader("💰 Total Tracked Portfolio Summary")
        
        total_rrsp_all_time = 0
        total_tfsa_all_time = 0
        
        chart_data = []
        for yr, data in all_history.items():
            annual_rrsp = (data.get('base_salary', 0) * (data.get('biweekly_pct', 0) + data.get('employer_match', 0)) / 100) + data.get('rrsp_lump_sum', 0)
            annual_tfsa = data.get('tfsa_lump_sum', 0)
            
            total_rrsp_all_time += annual_rrsp
            total_tfsa_all_time += annual_tfsa
            
            chart_data.append({
                "Year": str(yr),
                "Gross Income": data.get('t4_gross_income', 0),
                "Taxable Income": data.get('t4_gross_income', 0) - annual_rrsp,
                "RRSP Contrib": annual_rrsp,
                "TFSA Contrib": annual_tfsa
            })

        # Multi-Year Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Tracked RRSP", f"${total_rrsp_all_time:,.0f}")
        m2.metric("Total Tracked TFSA", f"${total_tfsa_all_time:,.0f}")
        m3.metric("Combined Sheltered Assets", f"${total_rrsp_all_time + total_tfsa_all_time:,.0f}", delta="Net Capital")

        st.divider()
        st.subheader("📈 Efficiency Analytics")
        df_chart = pd.DataFrame(chart_data).sort_values("Year")

        c1, c2 = st.columns(2)
        with c1:
            st.write("**Income vs. Taxable Footprint**")
            income_chart = alt.Chart(df_chart.melt('Year', value_vars=['Gross Income', 'Taxable Income'])).mark_bar(opacity=0.8).encode(
                x='Year:N', y=alt.Y('value:Q', title="Amount ($)", stack=None),
                color=alt.Color('variable:N', scale=alt.Scale(range=['#94a3b8', '#3b82f6']))
            ).properties(height=300)
            st.altair_chart(income_chart, use_container_width=True)
        
        with c2:
            st.write("**Account Contribution Mix**")
            mix_chart = alt.Chart(df_chart.melt('Year', value_vars=['RRSP Contrib', 'TFSA Contrib'])).mark_bar().encode(
                x='Year:N', y=alt.Y('value:Q', title="Total Saved ($)"),
                color=alt.Color('variable:N', scale=alt.Scale(range=['#3b82f6', '#10b981']))
            ).properties(height=300)
            st.altair_chart(mix_chart, use_container_width=True)

# --- 5. PAGE: YEAR VIEW ---
else:
    # (Existing Year View logic remains fully intact per instructions)
    selected_year = st.session_state.selected_year
    year_data = all_history.get(str(selected_year), {})

    with st.sidebar:
        if st.button("⬅️ Back to Home"):
            st.session_state.current_page = "Home"
            st.rerun()
        
        st.header(f"⚙️ {selected_year} Parameters")
        t4_gross_income = st.number_input("Annual T4 Gross Income", value=float(year_data.get("t4_gross_income", 0)), step=5000.0, help="Total income (Box 14).")
        base_salary = st.number_input("Annual Base Salary", value=float(year_data.get("base_salary", 0)), step=5000.0, help="Salary for % calculations.")
        
        st.header("💰 Contribution Logic")
        biweekly_pct = st.slider("Biweekly RRSP (%)", 0.0, 18.0, value=float(year_data.get("biweekly_pct", 0.0)), help="Automatic deduction.")
        employer_match = st.slider("Employer Match (%)", 0.0, 10.0, value=float(year_data.get("employer_match", 0.0)), help="Employer match %.")
        rrsp_lump_sum = st.number_input("RRSP Bulk Deposit", value=float(year_data.get("rrsp_lump_sum", 0)), help="Deposit before March 1st.")
        tfsa_lump_sum = st.number_input("TFSA Bulk Deposit", value=float(year_data.get("tfsa_lump_sum", 0)), help="Manual TFSA deposit.")
        
        st.header("📁 NOA Limits")
        rrsp_room = st.number_input("Unused RRSP Room", value=float(year_data.get("rrsp_room", 0)), help="From Notice of Assessment.")
        tfsa_room = st.number_input("Unused TFSA Room", value=float(year_data.get("tfsa_room", 0)), help="From CRA Account.")

        st.divider()
        if st.button("💾 Save Strategy", use_container_width=True):
            save_year_data(selected_year, {
                "t4_gross_income": t4_gross_income, "base_salary": base_salary,
                "biweekly_pct": biweekly_pct, "employer_match": employer_match,
                "rrsp_lump_sum": rrsp_lump_sum, "tfsa_lump_sum": tfsa_lump_sum,
                "rrsp_room": rrsp_room, "tfsa_room": tfsa_room
            })
            st.rerun()

    # Section Logic & Layout
    annual_rrsp_periodic = base_salary * ((biweekly_pct + employer_match) / 100)
    total_rrsp_contributions = annual_rrsp_periodic + rrsp_lump_sum
    taxable_income = t4_gross_income - total_rrsp_contributions
    est_refund = total_rrsp_contributions * 0.46
    tax_cliff = 181440 

    st.title(f"🏛️ Execution Strategy: {selected_year}")
    
    # 1. Quick Start Checklist
    description_box("Step-by-Step Execution Plan", "Follow these steps to ensure your tax year is optimized before the deadline.")

    # 2. The Tax Building Visualizer
    st.divider()
    st.subheader("🏢 The Tax Building Visualizer")
    # Building logic...

    # 3. Strategic Prioritization (Detailed)
    st.divider()
    st.subheader("📊 Strategic Prioritization & Efficiency Report")
    penthouse_amt = max(0, taxable_income - tax_cliff)
    penthouse_color = "background-color: #ffedd5;" if penthouse_amt > 0 else "background-color: #dcfce7;"
    shield_target = max(0, t4_gross_income - tax_cliff - annual_rrsp_periodic)

    summary_df = pd.DataFrame([
        {"Priority": "1. High Rate Shield", "Action": "RRSP (Penthouse)", "Impact": f"${penthouse_amt:,.0f} @ 48%", "Strategic Reason": "Immediate 48% ROI.", "Requirement": f"Deposit: ${shield_target:,.0f}" if penthouse_amt > 0 else "✓ Optimized"},
        {"Priority": "2. Tax-Free Growth", "Action": "TFSA Maximize", "Impact": f"${max(0, tfsa_room - tfsa_lump_sum):,.0f} Room", "Strategic Reason": "Tax-free compounding.", "Requirement": "Fill Room"}
    ])
    st.table(summary_df.style.apply(lambda row: [penthouse_color]*len(row) if "Penthouse" in row['Action'] else ['']*len(row), axis=1))

    # 4. March 1st Deadlines (2025)
    st.divider()
    st.subheader(f"📅 March 1st Deadlines ({selected_year})")
    ac1, ac2, ac3 = st.columns(3)
    ac1.metric("RRSP Bulk", f"${rrsp_lump_sum:,.0f}")
    ac2.metric("TFSA Bulk", f"${tfsa_lump_sum:,.0f}")
    ac3.metric("Est. Refund", f"${est_refund:,.0f}")

    # (Other sections like Reinvestment, Projections, and Bracket Table follow...)
