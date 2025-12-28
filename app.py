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

# --- 2. NAVIGATION STATE ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"
if "selected_year" not in st.session_state:
    st.session_state.selected_year = 2025

# --- 3. CONFIGURATION & CUSTOM STYLING ---
st.set_page_config(page_title="TAX RRSP/TFSA Planner", layout="wide")

st.markdown("""
    <style>
    .desc-box {
        background-color: #f8fafc; 
        padding: 18px; 
        border-radius: 12px; 
        border-left: 5px solid #3b82f6;
        margin-bottom: 25px;
        color: #334155;
        line-height: 1.6;
    }
    .input-label {
        font-weight: bold;
        color: #1e293b;
        margin-bottom: -15px;
    }
    .step-text {
        margin-bottom: 8px;
        display: block;
    }
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

def description_box(text):
    st.markdown(f'<div class="desc-box">{text}</div>', unsafe_allow_html=True)

# --- 4. PAGE: HOME ---
if st.session_state.current_page == "Home":
    st.title("🏠 Strategy Dashboard")
    description_box("**Overview:** This dashboard provides a bird's-eye view of your multi-year financial planning. Select a specific year tile to adjust inputs or view the detailed tax breakdown for that period.")
    
    st.subheader("📅 Planning Years")
    cols = st.columns(4)
    years_to_show = list(range(2024, 2030))
    
    for i, yr in enumerate(years_to_show):
        with cols[i % 4]:
            status = "✅ Saved" if str(yr) in all_history else "⚪ Empty"
            if st.button(f"📅 {yr}\n({status})", use_container_width=True):
                st.session_state.selected_year = yr
                st.session_state.current_page = "Year View"
                st.rerun()

    if all_history:
        st.divider()
        st.subheader("📈 Strategic Growth Comparison")
        description_box("**Analytics:** These charts track your performance over time. The **Income vs. Taxable Income** chart demonstrates the 'Tax Shield' effect of your RRSP, while the **Savings Volume** tracks your total capital accumulation.")
        
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
            st.write("**Tax Shield Performance**")
            melted_income = df_chart.melt('Year', value_vars=['Gross Income', 'Taxable Income'])
            income_chart = alt.Chart(melted_income).mark_bar(opacity=0.8).encode(
                x='Year:N', y=alt.Y('value:Q', title="Amount ($)", stack=None),
                color=alt.Color('variable:N', scale=alt.Scale(range=['#94a3b8', '#3b82f6'])),
                tooltip=['Year', 'variable', 'value']
            ).properties(height=300)
            st.altair_chart(income_chart, use_container_width=True)

        with c2:
            st.write("**Contribution Momentum**")
            savings_chart = alt.Chart(df_chart).mark_line(point=True, color='#10b981').encode(
                x='Year:N', y=alt.Y('Total Savings:Q', title="Total Saved ($)"),
                tooltip=['Year', 'Total Savings']
            ).properties(height=300)
            st.altair_chart(savings_chart, use_container_width=True)

    st.divider()
    st.subheader("📜 Execution History Log")
    description_box("**Audit Trail:** A tabular summary of your historical inputs and saved execution strategies.")
    if all_history:
        history_list = []
        for yr, data in all_history.items():
            annual_rrsp = (data.get('base_salary', 0) * (data.get('biweekly_pct', 0) + data.get('employer_match', 0)) / 100) + data.get('rrsp_lump_sum', 0)
            history_list.append({
                "Year": yr, "Gross Income": f"${data.get('t4_gross_income', 0):,.0f}",
                "RRSP Total": f"${annual_rrsp:,.0f}", "TFSA Lump Sum": f"${data.get('tfsa_lump_sum', 0):,.0f}"
            })
        st.table(pd.DataFrame(history_list).sort_values(by="Year", ascending=False))
    else:
        st.info("No saved strategies found. Click a year tile above to start planning.")

# --- 5. PAGE: YEAR VIEW ---
else:
    selected_year = st.session_state.selected_year
    year_data = all_history.get(str(selected_year), {})

    with st.sidebar:
        if st.button("⬅️ Back to Home"):
            st.session_state.current_page = "Home"
            st.rerun()
        
        st.header(f"⚙️ {selected_year} Parameters")
        
        st.markdown("**1. Annual T4 Gross Income**")
        st.caption("Your total income before any deductions (found on your T4).")
        t4_gross_income = st.number_input("T4 Gross", label_visibility="collapsed", value=float(year_data.get("t4_gross_income", 0)), step=5000.0)
        
        st.markdown("**2. Annual Base Salary**")
        st.caption("The fixed portion of your pay used to calculate bi-weekly RRSP deductions.")
        base_salary = st.number_input("Base Salary", label_visibility="collapsed", value=float(year_data.get("base_salary", 0)), step=5000.0)
        
        st.divider()
        st.header("💰 Payroll Contributions")
        
        st.markdown("**Biweekly RRSP (%)**")
        st.caption("Percentage of your base salary deducted every pay period.")
        biweekly_pct = st.slider("Biweekly %", 0.0, 18.0, value=float(year_data.get("biweekly_pct", 0.0)), label_visibility="collapsed")
        
        st.markdown("**Employer Match (%)**")
        st.caption("The percentage your company contributes to your RRSP.")
        employer_match = st.slider("Match %", 0.0, 10.0, value=float(year_data.get("employer_match", 0.0)), label_visibility="collapsed")
        
        st.divider()
        st.header("📅 One-Time Deposits")
        
        st.markdown("**RRSP Lump Sum**")
        st.caption("Additional manual cash deposits to RRSP before March 1st.")
        rrsp_lump_sum = st.number_input("RRSP Bulk", label_visibility="collapsed", value=float(year_data.get("rrsp_lump_sum", 0)))
        
        st.markdown("**TFSA Lump Sum**")
        st.caption("Total planned contributions to your Tax-Free Savings Account.")
        tfsa_lump_sum = st.number_input("TFSA Bulk", label_visibility="collapsed", value=float(year_data.get("tfsa_lump_sum", 0)))
        
        st.divider()
        st.header("📁 Available Room")
        
        st.markdown("**Unused RRSP Room**")
        st.caption("Your deduction limit from your latest Notice of Assessment.")
        rrsp_room = st.number_input("RRSP Room", label_visibility="collapsed", value=float(year_data.get("rrsp_room", 0)))
        
        st.markdown("**Unused TFSA Room**")
        st.caption("Your total available TFSA contribution room.")
        tfsa_room = st.number_input("TFSA Room", label_visibility="collapsed", value=float(year_data.get("tfsa_room", 0)))

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
                st.success("Saved!")
                st.rerun()
        with c_reset:
            if st.session_state.get("confirm_reset"):
                if st.button("✅ Confirm?", use_container_width=True):
                    delete_year_data(selected_year)
                    st.session_state.confirm_reset = False
                    st.rerun()
            elif st.button("🔄 Reset", use_container_width=True):
                st.session_state.confirm_reset = True
                st.rerun()

    # --- MAIN RIGHT PANEL ---
    st.title(f"🏛️ Execution Strategy: {selected_year}")
    
    # 1. QUICK START GUIDE (REFORMATTED)
    st.header("🚀 Quick Start Guide")
    description_box(f"""
    **1. Input Data:** Use the sidebar to enter your Income and Room Limits for **{selected_year}**.  
    **2. Review Deadlines:** Check the 'March 1st Deadlines' section for immediate actions.  
    **3. Visualize Savings:** Look at the 'Tax Building' to see how your RRSP 'shields' your income.  
    **4. Optimize:** Adjust your Lump Sums to eliminate income in the orange 'Taxed' zones.  
    **5. Finalize:** Hit 'Save' to record your **{selected_year}** execution strategy.
    """)

    # Calculations
    annual_rrsp_periodic = base_salary * ((biweekly_pct + employer_match) / 100)
    total_rrsp_contributions = annual_rrsp_periodic + rrsp_lump_sum
    taxable_income_for_chart = t4_gross_income - total_rrsp_contributions
    est_refund = total_rrsp_contributions * 0.46

    # 2. ACTION PLAN
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.subheader(f"📅 March 1st Deadlines ({selected_year})")
        description_box("**Action Plan:** These are your critical execution targets. Ensure bulk deposits are transferred before the deadline to qualify for the current tax year.")
    with col_h2:
        components.html('<button onclick="window.print()" style="width: 100%; height: 50px; background-color: #3b82f6; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">📄 Save as PDF</button>', height=70)

    ac1, ac2, ac3 = st.columns(3)
    with ac1: st.metric("RRSP Bulk Deposit", f"${rrsp_lump_sum:,.0f}")
    with ac2: st.metric("TFSA Bulk Deposit", f"${tfsa_lump_sum:,.0f}")
    with ac3: st.metric("Expected Tax Refund", f"${est_refund:,.0f}")

    # 3. ROOM TRACKER
    st.divider()
    st.subheader("🏦 Registration Room Status")
    description_box("**Room Analysis:** This table tracks how much of your legal contribution limit you are utilizing. Remaining room can be carried forward to future years.")
    room_df = pd.DataFrame({
        "Account": ["RRSP Room", "TFSA Room"],
        "Starting": [f"${rrsp_room:,.0f}", f"${tfsa_room:,.0f}"],
        "Usage": [f"-${total_rrsp_contributions:,.0f}", f"-${tfsa_lump_sum:,.0f}"],
        "Remaining": [f"${max(0, rrsp_room - total_rrsp_contributions):,.0f}", f"${max(0, tfsa_room - tfsa_lump_sum):,.0f}"]
    })
    st.table(room_df)

    # 4. THE TAX BUILDING
    st.divider()
    st.subheader("🏢 The Tax Building Visualizer")
    description_box("**Visual Strategy:** The **Blue (Shielded)** blocks show income that is successfully protected from tax by your RRSP. The **Orange (Taxed)** blocks represent income subject to marginal rates. Aim to 'shield' the highest floors first.")

    

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
        if shielded_amt > 0: building_data.append({"Floor": b['Floor'], "Amount": shielded_amt, "Status": "Shielded", "Rate": f"{b['rate']*100:.1f}%"})
        if taxed_amt > 0: building_data.append({"Floor": b['Floor'], "Amount": taxed_amt, "Status": "Taxed", "Rate": f"{b['rate']*100:.1f}%"})

    if building_data:
        chart = alt.Chart(pd.DataFrame(building_data)).mark_bar().encode(
            x=alt.X('Floor:N', sort=None), y=alt.Y('Amount:Q', title="Income ($)"),
            color=alt.Color('Status:N', scale=alt.Scale(domain=['Shielded', 'Taxed'], range=['#3b82f6', '#f59e0b'])),
            tooltip=['Floor', 'Amount', 'Rate', 'Status']
        ).properties(height=400)
        st.altair_chart(chart, use_container_width=True)

    # 5. STRATEGY SUMMARY
    st.divider()
    st.subheader("📊 Strategic Prioritization")
    description_box("**Prioritization Logic:** RRSP contributions are most effective when they offset income in the highest tax brackets (the 'Penthouse'). TFSA is prioritized next for its long-term tax-free growth.")
    
    tax_cliff = 181440 
    summary_df = pd.DataFrame({
        "Action": ["RRSP (High Value)", "RRSP (Low Value)", "TFSA"],
        "Current Impact": [
            f"${max(0, taxable_income_for_chart - tax_cliff):,.0f} still in Penthouse",
            f"${min(taxable_income_for_chart, tax_cliff):,.0f} in lower floors",
            f"${max(0, tfsa_room - tfsa_lump_sum):,.0f} available room"
        ],
        "Priority": ["1st - Immediate 48% ROI", "3rd - Tax Deferral only", "2nd - Tax-Free Growth"]
    })
    st.table(summary_df)
