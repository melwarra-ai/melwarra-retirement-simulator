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
        "This dashboard acts as your financial flight recorder. Use the 'Planning Years' tiles to toggle between years. "
        "The charts aggregate your data to show your wealth velocity and tax-shielding momentum.")
    
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
        st.subheader("📈 Strategic Performance & Room Burn-Down")
        
        chart_data = []
        room_data = []
        for yr, data in all_history.items():
            annual_rrsp = (data.get('base_salary', 0) * (data.get('biweekly_pct', 0) + data.get('employer_match', 0)) / 100) + data.get('rrsp_lump_sum', 0)
            chart_data.append({
                "Year": str(yr),
                "Gross Income": data.get('t4_gross_income', 0),
                "Taxable Income": data.get('t4_gross_income', 0) - annual_rrsp,
                "Total Savings": annual_rrsp + data.get('tfsa_lump_sum', 0)
            })
            room_data.append({"Year": str(yr), "Account": "RRSP", "Remaining Room": max(0, data.get('rrsp_room', 0) - annual_rrsp)})
            room_data.append({"Year": str(yr), "Account": "TFSA", "Remaining Room": max(0, data.get('tfsa_room', 0) - data.get('tfsa_lump_sum', 0))})

        df_chart = pd.DataFrame(chart_data).sort_values("Year")
        df_room = pd.DataFrame(room_data).sort_values("Year")

        c1, c2 = st.columns(2)
        with c1:
            st.write("**Income vs. Taxable Footprint**")
            income_chart = alt.Chart(df_chart.melt('Year', value_vars=['Gross Income', 'Taxable Income'])).mark_bar(opacity=0.8).encode(
                x='Year:N', y=alt.Y('value:Q', title="Amount ($)", stack=None),
                color=alt.Color('variable:N', scale=alt.Scale(range=['#94a3b8', '#3b82f6']))
            ).properties(height=300)
            st.altair_chart(income_chart, use_container_width=True)
        
        with c2:
            st.write("**Contribution Room Burn-Down**")
            burn_chart = alt.Chart(df_room).mark_area(opacity=0.6).encode(
                x='Year:N', y=alt.Y('Remaining Room:Q', stack=None),
                color=alt.Color('Account:N', scale=alt.Scale(range=['#3b82f6', '#10b981']))
            ).properties(height=300)
            st.altair_chart(burn_chart, use_container_width=True)

# --- 5. PAGE: YEAR VIEW ---
else:
    selected_year = st.session_state.selected_year
    year_data = all_history.get(str(selected_year), {})

    with st.sidebar:
        if st.button("⬅️ Back to Home"):
            st.session_state.current_page = "Home"
            st.rerun()
        
        st.header(f"⚙️ {selected_year} Parameters")
        t4_gross_income = st.number_input("Annual T4 Gross Income", value=float(year_data.get("t4_gross_income", 0)), step=5000.0, help="Total income from Box 14.")
        base_salary = st.number_input("Annual Base Salary", value=float(year_data.get("base_salary", 0)), step=5000.0, help="Core salary for % contributions.")
        
        st.header("💰 Contribution Logic")
        biweekly_pct = st.slider("Biweekly RRSP (%)", 0.0, 18.0, value=float(year_data.get("biweekly_pct", 0.0)), help="Paycheck deduction %.")
        employer_match = st.slider("Employer Match (%)", 0.0, 10.0, value=float(year_data.get("employer_match", 0.0)), help="Free money from employer.")
        rrsp_lump_sum = st.number_input("RRSP Bulk Deposit", value=float(year_data.get("rrsp_lump_sum", 0)), help="Manual deposit before March 1st.")
        tfsa_lump_sum = st.number_input("TFSA Bulk Deposit", value=float(year_data.get("tfsa_lump_sum", 0)), help="Manual TFSA deposit.")
        
        st.header("📁 NOA Limits")
        rrsp_room = st.number_input("Unused RRSP Room", value=float(year_data.get("rrsp_room", 0)), help="From latest NOA.")
        tfsa_room = st.number_input("Unused TFSA Room", value=float(year_data.get("tfsa_room", 0)), help="From CRA MyAccount.")

        st.divider()
        c_save, c_reset = st.columns(2)
        with c_save:
            if st.button("💾 Save Strategy", use_container_width=True):
                save_year_data(selected_year, {
                    "t4_gross_income": t4_gross_income, "base_salary": base_salary,
                    "biweekly_pct": biweekly_pct, "employer_match": employer_match,
                    "rrsp_lump_sum": rrsp_lump_sum, "tfsa_lump_sum": tfsa_lump_sum,
                    "rrsp_room": rrsp_room, "tfsa_room": tfsa_room
                })
                st.session_state.saved_flag = True
            
            if st.session_state.get("saved_flag"):
                st.markdown('<p class="status-saved">✓ Saved!</p>', unsafe_allow_html=True)
                st.session_state.saved_flag = False
        
        with c_reset:
            if st.button("🔄 Reset", use_container_width=True):
                delete_year_data(selected_year)
                st.rerun()

    # Calculations
    annual_rrsp_periodic = base_salary * ((biweekly_pct + employer_match) / 100)
    total_rrsp_contributions = annual_rrsp_periodic + rrsp_lump_sum
    taxable_income = t4_gross_income - total_rrsp_contributions
    tax_cliff = 181440 

    st.title(f"🏛️ Execution Strategy: {selected_year}")
    
    # 1. QUICK START CHECKLIST
    description_box("Step-by-Step Execution Plan", 
        "Follow these steps to ensure your tax year is optimized before the deadline.")

    # 2. THE TAX BUILDING VISUALIZER
    st.divider()
    st.subheader("🏢 The Tax Building Visualizer")
    
    
    BRACKETS = [
        {"Floor": "Floor 1", "low": 0, "top": 53891, "rate": "20.05%"},
        {"Floor": "Floor 2", "low": 53891, "top": 58523, "rate": "24.15%"},
        {"Floor": "Floor 3", "low": 58523, "top": 94907, "rate": "29.65%"},
        {"Floor": "Floor 4", "low": 94907, "top": 117045, "rate": "31.48%"},
        {"Floor": "Floor 5", "low": 117045, "top": 181440, "rate": "33.89%"}, 
        {"Floor": "Penthouse", "low": 181440, "top": 258482, "rate": "47.97%"}
    ]

    building_data = []
    for b in BRACKETS:
        total_in_bracket = min(t4_gross_income, b['top']) - b['low']
        if total_in_bracket <= 0: continue
        taxed_amt = max(0, min(b['top'], taxable_income) - b['low'])
        shielded_amt = total_in_bracket - taxed_amt
        if shielded_amt > 0: building_data.append({"Floor": b['Floor'], "Amount": shielded_amt, "Status": "Shielded"})
        if taxed_amt > 0: building_data.append({"Floor": b['Floor'], "Amount": taxed_amt, "Status": "Taxed"})

    if building_data:
        chart = alt.Chart(pd.DataFrame(building_data)).mark_bar().encode(
            x=alt.X('Floor:N', sort=None), y=alt.Y('Amount:Q'),
            color=alt.Color('Status:N', scale=alt.Scale(domain=['Shielded', 'Taxed'], range=['#3b82f6', '#f59e0b']))
        ).properties(height=350)
        st.altair_chart(chart, use_container_width=True)

    # 3. STRATEGIC PRIORITIZATION
    st.divider()
    st.subheader("📊 Strategic Prioritization & Efficiency Report")
    penthouse_amt = max(0, taxable_income - tax_cliff)
    penthouse_color = "background-color: #ffedd5;" if penthouse_amt > 0 else "background-color: #dcfce7;"
    shield_target = max(0, t4_gross_income - tax_cliff - annual_rrsp_periodic)

    summary_df = pd.DataFrame([
        {"Priority": "1. High Rate Shield", "Action": "RRSP (Penthouse)", "Impact": f"${penthouse_amt:,.0f} @ 48%", "Requirement": f"Deposit: ${shield_target:,.0f}" if penthouse_amt > 0 else "✓ Optimized"},
        {"Priority": "2. Tax-Free Growth", "Action": "TFSA Maximize", "Impact": f"${max(0, tfsa_room - tfsa_lump_sum):,.0f} Room", "Requirement": "Fill Remaining Room"}
    ])
    st.table(summary_df.style.apply(lambda row: [penthouse_color]*len(row) if "Penthouse" in row['Action'] else ['']*len(row), axis=1))

    # 4. MARCH 1ST DEADLINES
    st.divider()
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1: st.subheader(f"📅 March 1st Deadlines ({selected_year})")
    with col_h2: components.html('<button onclick="window.print()" style="width: 100%; height: 50px; background-color: #3b82f6; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">📄 Save PDF</button>', height=70)
    
    ac1, ac2, ac3 = st.columns(3)
    ac1.metric("RRSP Bulk", f"${rrsp_lump_sum:,.0f}")
    ac2.metric("TFSA Bulk", f"${tfsa_lump_sum:,.0f}")
    ac3.metric("Est. Refund", f"${total_rrsp_contributions * 0.46:,.0f}")

    # 5. CARRYOVER ROOM PROJECTION
    st.divider()
    st.subheader(f"⏭️ {selected_year + 1} Carryover Room Projection")
    est_rrsp_new_room = min(31560, t4_gross_income * 0.18) 
    est_tfsa_new_room = 7000.0
    rem_rrsp = max(0, rrsp_room - total_rrsp_contributions) + est_rrsp_new_room
    rem_tfsa = max(0, tfsa_room - tfsa_lump_sum) + est_tfsa_new_room
    fc1, fc2 = st.columns(2)
    fc1.metric(f"Proj. {selected_year + 1} RRSP Room", f"${rem_rrsp:,.0f}", delta=f"+${est_rrsp_new_room:,.0f}")
    fc2.metric(f"Proj. {selected_year + 1} TFSA Room", f"${rem_tfsa:,.0f}", delta=f"+${est_tfsa_new_room:,.0f}")

    # NEW: 6. TAX BRACKET REFERENCE TABLE
    st.divider()
    st.subheader("📑 Tax Bracket Reference (ON + Federal Combined)")
    description_box("Detailed Thresholds", "Use this table to see exactly where your income is tiered. The 'Floor' matches the Visualizer above.")
    bracket_df = pd.DataFrame(BRACKETS)
    bracket_df.columns = ["Floor Level", "Starts At ($)", "Ends At ($)", "Combined Marginal Rate"]
    st.table(bracket_df)
