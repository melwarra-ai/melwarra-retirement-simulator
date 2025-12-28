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

# --- 2. NAVIGATION ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"
if "selected_year" not in st.session_state:
    st.session_state.selected_year = 2025

# --- 3. STYLING ---
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
    description_box("System Overview", "Welcome to your multi-year financial command center. Select a year tile to manage specific strategies. The dashboard below tracks your aggregate progress across multiple tax years.")
    
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
        st.subheader("📈 Strategic Growth Comparison")
        
        # --- DETAILED EXPLANATION SECTION ---
        description_box("Understanding Your Strategic Growth", """
        This section provides a visual audit of your wealth-building efficiency over time. It is designed to track two critical pillars of financial health:
        
        **1. Tax Shielding Efficiency (Bar Chart)**
        * **Gross Income (Grey):** This represents your total earnings before any intervention. It is the 'target' the government uses to calculate your taxes.
        * **Taxable Income (Blue):** This is the outcome of your strategy. By using RRSP contributions, you 'shield' a portion of your income, effectively moving the blue line down. The gap between Grey and Blue represents income you earned that you *do not* pay taxes on today.
        * **Goal:** Maintain a significant gap between the bars, especially during your highest-earning years.
        
        **2. Capital Accumulation Momentum (Line Chart)**
        * This tracks the **Total Annual Savings** (RRSP + TFSA) you have committed to your future. 
        * Unlike simple savings, this represents 'Tax-Advantaged' capital. A rising line indicates that your capacity to save is increasing, or you are becoming more disciplined in capturing surplus income before it is lost to tax or lifestyle inflation.
        * **Goal:** A consistent upward trend indicates compounding growth potential.
        """)

        # Prepare Data
        chart_data = []
        for yr, data in all_history.items():
            annual_rrsp = (data.get('base_salary', 0) * (data.get('biweekly_pct', 0) + data.get('employer_match', 0)) / 100) + data.get('rrsp_lump_sum', 0)
            chart_data.append({
                "Year": str(yr),
                "Gross Income": data.get('t4_gross_income', 0),
                "Taxable Income": data.get('t4_gross_income', 0) - annual_rrsp,
                "Total Savings": annual_rrsp + data.get('tfsa_lump_sum', 0)
            })
        df_chart = pd.DataFrame(chart_data).sort_values("Year")

        c1, c2 = st.columns(2)
        with c1:
            st.write("**Income vs. Taxable Footprint**")
            income_chart = alt.Chart(df_chart.melt('Year', value_vars=['Gross Income', 'Taxable Income'])).mark_bar(opacity=0.8).encode(
                x='Year:N', y=alt.Y('value:Q', title="Amount ($)", stack=None),
                color=alt.Color('variable:N', scale=alt.Scale(range=['#94a3b8', '#3b82f6']))
            ).properties(height=350)
            st.altair_chart(income_chart, use_container_width=True)
        with c2:
            st.write("**Net Annual Savings Growth**")
            savings_chart = alt.Chart(df_chart).mark_line(point=True, color='#10b981').encode(
                x='Year:N', y=alt.Y('Total Savings:Q', title="Total Saved ($)")
            ).properties(height=350)
            st.altair_chart(savings_chart, use_container_width=True)

# --- 5. PAGE: YEAR VIEW (UNCHANGED LOGIC) ---
else:
    selected_year = st.session_state.selected_year
    year_data = all_history.get(str(selected_year), {})
    with st.sidebar:
        if st.button("⬅️ Back to Home"):
            st.session_state.current_page = "Home"
            st.rerun()
        st.header(f"⚙️ {selected_year} Parameters")
        t4_gross_income = st.number_input("Annual T4 Gross Income", value=float(year_data.get("t4_gross_income", 0)), step=5000.0)
        base_salary = st.number_input("Annual Base Salary", value=float(year_data.get("base_salary", 0)), step=5000.0)
        st.header("💰 Contribution Logic")
        biweekly_pct = st.slider("Biweekly RRSP (%)", 0.0, 18.0, value=float(year_data.get("biweekly_pct", 0.0)))
        employer_match = st.slider("Employer Match (%)", 0.0, 10.0, value=float(year_data.get("employer_match", 0.0)))
        rrsp_lump_sum = st.number_input("RRSP Bulk Deposit", value=float(year_data.get("rrsp_lump_sum", 0)))
        tfsa_lump_sum = st.number_input("TFSA Bulk Deposit", value=float(year_data.get("tfsa_lump_sum", 0)))
        st.header("📁 NOA Limits")
        rrsp_room = st.number_input("Unused RRSP Room", value=float(year_data.get("rrsp_room", 0)))
        tfsa_room = st.number_input("Unused TFSA Room", value=float(year_data.get("tfsa_room", 0)))
        st.divider()
        if st.button("💾 Save Strategy", use_container_width=True):
            save_year_data(selected_year, {
                "t4_gross_income": t4_gross_income, "base_salary": base_salary,
                "biweekly_pct": biweekly_pct, "employer_match": employer_match,
                "rrsp_lump_sum": rrsp_lump_sum, "tfsa_lump_sum": tfsa_lump_sum,
                "rrsp_room": rrsp_room, "tfsa_room": tfsa_room
            })
            st.markdown('<p class="status-saved">✓ Saved!</p>', unsafe_allow_html=True)
        if st.button("🔄 Reset", use_container_width=True):
            delete_year_data(selected_year)
            st.rerun()

    st.title(f"🏛️ Execution Strategy: {selected_year}")
    description_box("Strategy Summary", f"Detailed breakdown for {selected_year}. Adjust the sidebar to see real-time tax changes.")
    
    annual_rrsp_periodic = base_salary * ((biweekly_pct + employer_match) / 100)
    total_rrsp_contributions = annual_rrsp_periodic + rrsp_lump_sum
    taxable_income = t4_gross_income - total_rrsp_contributions
    tax_cliff = 181440 

    ac1, ac2, ac3 = st.columns(3)
    ac1.metric("RRSP Bulk", f"${rrsp_lump_sum:,.0f}")
    ac2.metric("TFSA Bulk", f"${tfsa_lump_sum:,.0f}")
    ac3.metric("Est. Refund", f"${total_rrsp_contributions * 0.46:,.0f}")

    st.divider()
    st.subheader("📊 Strategic Prioritization")
    penthouse_amt = max(0, taxable_income - tax_cliff)
    penthouse_color = "background-color: #ffedd5;" if penthouse_amt > 0 else "background-color: #dcfce7;"
    shield_target = max(0, t4_gross_income - tax_cliff - annual_rrsp_periodic)

    summary_df = pd.DataFrame([
        {"Action": "RRSP (Penthouse Shield)", "Impact": f"${penthouse_amt:,.0f} Taxed @ 48%", "Requirement": f"Lump Sum Target: ${shield_target:,.0f}" if penthouse_amt > 0 else "✓ Optimized"},
        {"Action": "TFSA Maximize", "Impact": f"${max(0, tfsa_room - tfsa_lump_sum):,.0f} Room Left", "Requirement": "Tax-Free Growth"},
    ])
    st.table(summary_df.style.apply(lambda row: [penthouse_color]*len(row) if "Penthouse" in row['Action'] else ['']*len(row), axis=1))
