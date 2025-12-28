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
    description_box("System Overview", "Welcome to your multi-year financial command center. Select a year tile to adjust your plan. The charts below automatically aggregate your data to show your tax-shielding progress.")
    
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
            ).properties(height=300)
            st.altair_chart(income_chart, use_container_width=True)
        with c2:
            st.write("**Net Annual Savings Growth**")
            savings_chart = alt.Chart(df_chart).mark_line(point=True, color='#10b981').encode(
                x='Year:N', y=alt.Y('Total Savings:Q', title="Total Saved ($)")
            ).properties(height=300)
            st.altair_chart(savings_chart, use_container_width=True)

# --- 5. PAGE: YEAR VIEW ---
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

    # --- MAIN RIGHT PANEL ---
    st.title(f"🏛️ Execution Strategy: {selected_year}")
    
    description_box("Quick Start Checklist", f"""
    1. **Data Entry:** Enter gross income and contribution % in the sidebar.<br>
    2. **Verification:** Confirm March 1st bulk deposits are scheduled.<br>
    3. **Optimization:** Check the 'Penthouse' status in the priority table below.<br>
    4. **Finalize:** Click Save and export as PDF for your records.
    """)

    # Calculations
    annual_rrsp_periodic = base_salary * ((biweekly_pct + employer_match) / 100)
    total_rrsp_contributions = annual_rrsp_periodic + rrsp_lump_sum
    taxable_income = t4_gross_income - total_rrsp_contributions
    tax_cliff = 181440 

    # Action Metrics
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1: st.subheader(f"📅 March 1st Deadlines ({selected_year})")
    with col_h2: components.html('<button onclick="window.print()" style="width: 100%; height: 50px; background-color: #3b82f6; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">📄 Save PDF</button>', height=70)

    ac1, ac2, ac3 = st.columns(3)
    ac1.metric("RRSP Bulk", f"${rrsp_lump_sum:,.0f}")
    ac2.metric("TFSA Bulk", f"${tfsa_lump_sum:,.0f}")
    ac3.metric("Est. Refund", f"${total_rrsp_contributions * 0.46:,.0f}")

    st.divider()
    st.subheader("🏢 The Tax Building Visualizer")
    
    
    BRACKETS = [
        {"Floor": "Floor 1", "low": 0, "top": 53891},
        {"Floor": "Floor 2", "low": 53891, "top": 58523},
        {"Floor": "Floor 3", "low": 58523, "top": 94907},
        {"Floor": "Floor 4", "low": 94907, "top": 117045},
        {"Floor": "Floor 5", "low": 117045, "top": 181440}, 
        {"Floor": "Penthouse", "low": 181440, "top": 258482}
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

    st.divider()
    st.subheader("📊 Strategic Prioritization")
    description_box("Optimization Guide", "The table below highlights high-efficiency actions. Items in **Orange** represent income being taxed at the highest rates. Aim to increase RRSP until they turn **Green**.")

    penthouse_amt = max(0, taxable_income - tax_cliff)
    penthouse_color = "background-color: #ffedd5;" if penthouse_amt > 0 else "background-color: #dcfce7;"
    shield_target = max(0, t4_gross_income - tax_cliff - annual_rrsp_periodic)

    summary_df = pd.DataFrame([
        {"Action": "RRSP (Penthouse Shield)", "Impact": f"${penthouse_amt:,.0f} Taxed @ 48%", "Requirement": f"Lump Sum Target: ${shield_target:,.0f}" if penthouse_amt > 0 else "✓ Optimized"},
        {"Action": "TFSA Maximize", "Impact": f"${max(0, tfsa_room - tfsa_lump_sum):,.0f} Room Left", "Requirement": "Tax-Free Growth"},
        {"Action": "RRSP (Lower Floor)", "Impact": "Income < $181k", "Requirement": "Tax Deferral Only"}
    ])

    def color_priority(row):
        if "Penthouse" in row['Action']:
            return [penthouse_color] * len(row)
        return [''] * len(row)

    st.table(summary_df.style.apply(color_priority, axis=1))
