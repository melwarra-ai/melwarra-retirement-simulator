import streamlit as st
import pandas as pd
import altair as alt
import json
import os
import streamlit.components.v1 as components

# --- 1. PERSISTENCE ENGINE ---
SAVE_FILE = "retirement_history.json"

def load_all_data():
    """Load all saved year data from JSON file"""
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return {}
    return {}

def save_year_data(year, data):
    """Save data for a specific year"""
    all_data = load_all_data()
    all_data[str(year)] = data
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(all_data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

def delete_year_data(year):
    """Delete data for a specific year"""
    all_data = load_all_data()
    if str(year) in all_data:
        del all_data[str(year)]
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(all_data, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Error deleting data: {e}")
            return False
    return False

# --- 2. TAX CALCULATION ENGINE ---
TAX_BRACKETS = [
    {"name": "Floor 1", "low": 0, "high": 53891, "rate": 0.2005},
    {"name": "Floor 2", "low": 53891, "high": 58523, "rate": 0.2415},
    {"name": "Floor 3", "low": 58523, "high": 94907, "rate": 0.2965},
    {"name": "Floor 4", "low": 94907, "high": 117045, "rate": 0.3148},
    {"name": "Floor 5", "low": 117045, "high": 181440, "rate": 0.3389},
    {"name": "Penthouse", "low": 181440, "high": float('inf'), "rate": 0.4797}
]

def calculate_tax_on_income(income):
    """Calculate total tax owed on given income using marginal brackets"""
    if income <= 0:
        return 0
    
    total_tax = 0
    for bracket in TAX_BRACKETS:
        if income > bracket['low']:
            taxable_in_bracket = min(income, bracket['high']) - bracket['low']
            total_tax += taxable_in_bracket * bracket['rate']
    
    return total_tax

def calculate_tax_refund(gross_income, rrsp_contributions):
    """Calculate tax refund from RRSP contributions"""
    if gross_income <= 0:
        return 0
    
    tax_without_rrsp = calculate_tax_on_income(gross_income)
    tax_with_rrsp = calculate_tax_on_income(gross_income - rrsp_contributions)
    refund = tax_without_rrsp - tax_with_rrsp
    
    return max(0, refund)

def get_marginal_rate(income):
    """Get the marginal tax rate for a given income level"""
    if income <= 0:
        return 0
    
    for bracket in TAX_BRACKETS:
        if bracket['low'] <= income < bracket['high']:
            return bracket['rate']
    
    return TAX_BRACKETS[-1]['rate']

# --- 3. CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Tax & Wealth Velocity Suite",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Fintech Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
    }
    
    .premium-card {
        background: white;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
    }
    
    .desc-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(102, 126, 234, 0.4);
    }
    
    .desc-box h4 {
        margin-top: 0;
        color: white;
        font-weight: 600;
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        text-align: center;
        border-left: 4px solid #3b82f6;
    }
    
    .year-tile {
        background: white;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        cursor: pointer;
        border: 2px solid transparent;
    }
    
    .year-tile:hover {
        box-shadow: 0 8px 16px rgba(0,0,0,0.12);
        transform: translateY(-2px);
        border-color: #3b82f6;
    }
    
    .year-tile-saved {
        border-left: 4px solid #10b981;
    }
    
    .year-tile-empty {
        border-left: 4px solid #94a3b8;
    }
    
    .status-saved {
        color: #10b981;
        font-weight: 600;
        margin-top: 8px;
        display: block;
        animation: fadeIn 0.5s;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    .priority-high {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 4px solid #f59e0b;
    }
    
    .priority-medium {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border-left: 4px solid #3b82f6;
    }
    
    h1, h2, h3 {
        font-weight: 600;
        color: #1e293b;
    }
    
    @media print {
        div[data-testid="stSidebar"], 
        .stButton, 
        button:not(.print-button), 
        header, 
        footer, 
        [data-testid="stToolbar"] {
            display: none !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

def description_box(title, content):
    """Render a premium description box"""
    st.markdown(f'''
        <div class="desc-box">
            <h4>{title}</h4>
            <div style="line-height:1.7; font-weight: 300;">{content}</div>
        </div>
    ''', unsafe_allow_html=True)

# --- 4. SESSION STATE INITIALIZATION ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"
if "selected_year" not in st.session_state:
    st.session_state.selected_year = 2025
if "saved_flag" not in st.session_state:
    st.session_state.saved_flag = False
if "refund_to_tfsa" not in st.session_state:
    st.session_state.refund_to_tfsa = 0

# Load all historical data
all_history = load_all_data()

# --- 5. PAGE: HOME ---
if st.session_state.current_page == "Home":
    st.title("🏦 Canadian Tax & Wealth Velocity Suite")
    
    description_box(
        "Strategic Financial Command Center",
        "Your comprehensive multi-year tax optimization and wealth acceleration platform. "
        "Navigate between planning years to build tax-efficient contribution strategies and track your wealth velocity across time."
    )
    
    # Global Net Worth Summary
    if all_history:
        st.markdown("### 💎 Global Wealth Summary")
        
        total_rrsp_all = 0
        total_tfsa_all = 0
        total_tax_shield = 0
        
        for yr, data in all_history.items():
            annual_rrsp = (data.get('base_salary', 0) * 
                          (data.get('biweekly_pct', 0) + data.get('employer_match', 0)) / 100) + \
                          data.get('rrsp_lump_sum', 0)
            tfsa_contrib = data.get('tfsa_lump_sum', 0)
            
            total_rrsp_all += annual_rrsp
            total_tfsa_all += tfsa_contrib
            
            # Calculate tax shield value
            refund = calculate_tax_refund(data.get('t4_gross_income', 0), annual_rrsp)
            total_tax_shield += refund
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total RRSP Contributions",
                f"${total_rrsp_all:,.0f}",
                help="Cumulative RRSP across all saved years"
            )
        
        with col2:
            st.metric(
                "Total TFSA Contributions",
                f"${total_tfsa_all:,.0f}",
                help="Cumulative TFSA across all saved years"
            )
        
        with col3:
            st.metric(
                "Total Tax Shield Value",
                f"${total_tax_shield:,.0f}",
                help="Total tax refunds generated from RRSP contributions"
            )
        
        with col4:
            st.metric(
                "Combined Wealth Velocity",
                f"${total_rrsp_all + total_tfsa_all:,.0f}",
                delta=f"+${total_tax_shield:,.0f} shield",
                help="Total contributions plus tax efficiency gains"
            )
        
        st.divider()
    
    # Planning Years Grid
    st.markdown("### 📅 Planning Years")
    
    years_to_show = list(range(2024, 2031))
    cols_per_row = 4
    
    for row_start in range(0, len(years_to_show), cols_per_row):
        cols = st.columns(cols_per_row)
        for i, yr in enumerate(years_to_show[row_start:row_start + cols_per_row]):
            with cols[i]:
                is_saved = str(yr) in all_history
                
                if is_saved:
                    data = all_history[str(yr)]
                    annual_rrsp = (data.get('base_salary', 0) * 
                                  (data.get('biweekly_pct', 0) + data.get('employer_match', 0)) / 100) + \
                                  data.get('rrsp_lump_sum', 0)
                    status = f"💰 ${annual_rrsp:,.0f}"
                    button_type = "primary"
                else:
                    status = "Empty"
                    button_type = "secondary"
                
                if st.button(
                    f"📅 **{yr}**\n{status}",
                    use_container_width=True,
                    key=f"home_{yr}",
                    type=button_type
                ):
                    st.session_state.selected_year = yr
                    st.session_state.current_page = "Year View"
                    st.rerun()
    
    # Multi-Year Analytics
    if all_history and len(all_history) > 1:
        st.divider()
        st.markdown("### 📈 Multi-Year Analytics & Trends")
        
        # Prepare data for charts
        chart_data = []
        room_data = []
        
        for yr, data in sorted(all_history.items(), key=lambda x: x[0]):
            annual_rrsp = (data.get('base_salary', 0) * 
                          (data.get('biweekly_pct', 0) + data.get('employer_match', 0)) / 100) + \
                          data.get('rrsp_lump_sum', 0)
            tfsa_contrib = data.get('tfsa_lump_sum', 0)
            gross = data.get('t4_gross_income', 0)
            
            chart_data.append({
                "Year": yr,
                "Gross Income": gross,
                "Taxable Income": gross - annual_rrsp,
                "Tax Shield": annual_rrsp,
                "RRSP": annual_rrsp,
                "TFSA": tfsa_contrib
            })
            
            room_data.append({
                "Year": yr,
                "Account": "RRSP",
                "Remaining Room": max(0, data.get('rrsp_room', 0) - annual_rrsp)
            })
            room_data.append({
                "Year": yr,
                "Account": "TFSA",
                "Remaining Room": max(0, data.get('tfsa_room', 0) - tfsa_contrib)
            })
        
        df_chart = pd.DataFrame(chart_data)
        df_room = pd.DataFrame(room_data)
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("**Income vs. Tax-Shielded Income**")
            
            income_df = df_chart[['Year', 'Gross Income', 'Taxable Income']].melt(
                'Year',
                var_name='Category',
                value_name='Amount'
            )
            
            income_chart = alt.Chart(income_df).mark_bar(opacity=0.85).encode(
                x=alt.X('Year:N', title='Year'),
                y=alt.Y('Amount:Q', title='Income ($)'),
                color=alt.Color('Category:N',
                    scale=alt.Scale(
                        domain=['Gross Income', 'Taxable Income'],
                        range=['#94a3b8', '#3b82f6']
                    ),
                    legend=alt.Legend(title="Income Type")
                ),
                xOffset='Category:N'
            ).properties(height=320)
            
            st.altair_chart(income_chart, use_container_width=True)
        
        with col_right:
            st.markdown("**Contribution Room Burn-Down**")
            
            room_chart = alt.Chart(df_room).mark_area(
                opacity=0.7,
                line=True
            ).encode(
                x=alt.X('Year:N', title='Year'),
                y=alt.Y('Remaining Room:Q', title='Remaining Room ($)'),
                color=alt.Color('Account:N',
                    scale=alt.Scale(
                        domain=['RRSP', 'TFSA'],
                        range=['#3b82f6', '#10b981']
                    ),
                    legend=alt.Legend(title="Account")
                )
            ).properties(height=320)
            
            st.altair_chart(room_chart, use_container_width=True)
        
        # Contribution trends
        st.markdown("**Annual Contribution Trends**")
        
        contrib_df = df_chart[['Year', 'RRSP', 'TFSA']].melt(
            'Year',
            var_name='Account',
            value_name='Contribution'
        )
        
        contrib_chart = alt.Chart(contrib_df).mark_line(
            point=alt.OverlayMarkDef(filled=False, fill="white", size=80)
        ).encode(
            x=alt.X('Year:N', title='Year'),
            y=alt.Y('Contribution:Q', title='Annual Contribution ($)'),
            color=alt.Color('Account:N',
                scale=alt.Scale(
                    domain=['RRSP', 'TFSA'],
                    range=['#3b82f6', '#10b981']
                )
            ),
            strokeWidth=alt.value(3)
        ).properties(height=300)
        
        st.altair_chart(contrib_chart, use_container_width=True)

# --- 6. PAGE: YEAR VIEW ---
else:
    selected_year = st.session_state.selected_year
    year_data = all_history.get(str(selected_year), {})
    
    # Sidebar with form for inputs
    with st.sidebar:
        if st.button("⬅️ Back to Home", use_container_width=True):
            st.session_state.current_page = "Home"
            st.rerun()
        
        st.markdown(f"## ⚙️ {selected_year} Strategy")
        
        with st.form(key="input_form"):
            st.markdown("### 💵 Income Parameters")
            
            t4_gross_income = st.number_input(
                "Annual T4 Gross Income",
                value=float(year_data.get("t4_gross_income", 0)),
                step=5000.0,
                min_value=0.0,
                help="Total employment income from Box 14 of your T4"
            )
            
            base_salary = st.number_input(
                "Annual Base Salary",
                value=float(year_data.get("base_salary", 0)),
                step=5000.0,
                min_value=0.0,
                help="Core salary used for percentage-based contributions"
            )
            
            st.markdown("### 🎯 RRSP Strategy")
            
            biweekly_pct = st.slider(
                "Biweekly RRSP Contribution (%)",
                0.0, 18.0,
                value=float(year_data.get("biweekly_pct", 0.0)),
                step=0.5,
                help="Percentage deducted from each paycheck"
            )
            
            employer_match = st.slider(
                "Employer Match (%)",
                0.0, 10.0,
                value=float(year_data.get("employer_match", 0.0)),
                step=0.5,
                help="Employer contribution percentage (free money!)"
            )
            
            rrsp_lump_sum = st.number_input(
                "RRSP Lump Sum Deposit",
                value=float(year_data.get("rrsp_lump_sum", 0)),
                step=1000.0,
                min_value=0.0,
                help="One-time deposit before March 1st deadline"
            )
            
            st.markdown("### 🌱 TFSA Strategy")
            
            tfsa_lump_sum = st.number_input(
                "TFSA Lump Sum Deposit",
                value=float(year_data.get("tfsa_lump_sum", 0)),
                step=1000.0,
                min_value=0.0,
                help="Tax-free savings account contribution"
            )
            
            st.markdown("### 📋 CRA Contribution Limits")
            
            rrsp_room = st.number_input(
                "Available RRSP Room",
                value=float(year_data.get("rrsp_room", 0)),
                step=1000.0,
                min_value=0.0,
                help="From your latest Notice of Assessment"
            )
            
            tfsa_room = st.number_input(
                "Available TFSA Room",
                value=float(year_data.get("tfsa_room", 0)),
                step=1000.0,
                min_value=0.0,
                help="From CRA MyAccount"
            )
            
            st.divider()
            
            # Form submit buttons
            col_save, col_reset = st.columns(2)
            
            with col_save:
                submitted = st.form_submit_button(
                    "💾 Save",
                    use_container_width=True,
                    type="primary"
                )
            
            with col_reset:
                reset = st.form_submit_button(
                    "🔄 Reset",
                    use_container_width=True
                )
            
            if submitted:
                success = save_year_data(selected_year, {
                    "t4_gross_income": t4_gross_income,
                    "base_salary": base_salary,
                    "biweekly_pct": biweekly_pct,
                    "employer_match": employer_match,
                    "rrsp_lump_sum": rrsp_lump_sum,
                    "tfsa_lump_sum": tfsa_lump_sum,
                    "rrsp_room": rrsp_room,
                    "tfsa_room": tfsa_room
                })
                
                if success:
                    st.session_state.saved_flag = True
                    st.rerun()
            
            if reset:
                delete_year_data(selected_year)
                st.rerun()
        
        if st.session_state.get("saved_flag"):
            st.success("✓ Strategy saved successfully!")
            st.session_state.saved_flag = False
    
    # Main content area - Calculations
    annual_rrsp_periodic = base_salary * ((biweekly_pct + employer_match) / 100)
    total_rrsp_contributions = annual_rrsp_periodic + rrsp_lump_sum
    taxable_income = max(0, t4_gross_income - total_rrsp_contributions)
    
    # Calculate tax refund
    estimated_refund = calculate_tax_refund(t4_gross_income, total_rrsp_contributions)
    marginal_rate = get_marginal_rate(t4_gross_income)
    
    # Header
    st.title(f"🏛️ Tax Optimization Strategy: {selected_year}")
    
    description_box(
        "Strategic Execution Framework",
        f"Follow this comprehensive plan to maximize your tax efficiency and wealth velocity for {selected_year}. "
        "Each section provides actionable insights to optimize your contribution strategy."
    )
    
    # Key Metrics Dashboard
    st.markdown("### 📊 Strategic Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Gross Income",
            f"${t4_gross_income:,.0f}",
            help="Total T4 employment income"
        )
    
    with col2:
        st.metric(
            "Tax-Shielded Income",
            f"${taxable_income:,.0f}",
            delta=f"-${total_rrsp_contributions:,.0f}",
            delta_color="inverse",
            help="Income after RRSP deductions"
        )
    
    with col3:
        st.metric(
            "Marginal Tax Rate",
            f"{marginal_rate*100:.2f}%",
            help="Your current tax bracket rate"
        )
    
    with col4:
        st.metric(
            "Estimated Tax Refund",
            f"${estimated_refund:,.0f}",
            delta=f"+{(estimated_refund/max(1,total_rrsp_contributions))*100:.1f}% ROI",
            help="Tax refund from RRSP contributions"
        )
    
    st.divider()
    
    # Tax Building Visualizer
    st.markdown("### 🏢 Tax Building Visualizer")
    
    description_box(
        "Income Distribution Across Tax Brackets",
        "This chart shows how your income is distributed across tax floors. "
        "Blue bars represent tax-shielded income (protected by RRSP), "
        "while orange bars show taxable income. Your goal: maximize the blue."
    )
    
    # Build the tax building data
    building_data = []
    
    for bracket in TAX_BRACKETS:
        # Total income in this bracket
        total_in_bracket = min(t4_gross_income, bracket['high']) - bracket['low']
        
        if total_in_bracket <= 0:
            continue
        
        # Taxable amount in this bracket
        taxed_amt = max(0, min(bracket['high'], taxable_income) - bracket['low'])
        
        # Shielded amount in this bracket
        shielded_amt = total_in_bracket - taxed_amt
        
        if shielded_amt > 0:
            building_data.append({
                "Floor": bracket['name'],
                "Amount": shielded_amt,
                "Status": "Tax-Shielded",
                "Rate": f"{bracket['rate']*100:.2f}%"
            })
        
        if taxed_amt > 0:
            building_data.append({
                "Floor": bracket['name'],
                "Amount": taxed_amt,
                "Status": "Taxable",
                "Rate": f"{bracket['rate']*100:.2f}%"
            })
    
    if building_data:
        df_building = pd.DataFrame(building_data)
        
        # Create ordered floor list for proper sorting
        floor_order = [b['name'] for b in TAX_BRACKETS]
        
        building_chart = alt.Chart(df_building).mark_bar().encode(
            x=alt.X('Floor:N',
                title='Tax Bracket Floor',
                sort=floor_order
            ),
            y=alt.Y('Amount:Q',
                title='Income Amount ($)',
                stack='zero'
            ),
            color=alt.Color('Status:N',
                scale=alt.Scale(
                    domain=['Tax-Shielded', 'Taxable'],
                    range=['#3b82f6', '#f59e0b']
                ),
                legend=alt.Legend(title="Status", orient="top")
            ),
            tooltip=[
                alt.Tooltip('Floor:N', title='Bracket'),
                alt.Tooltip('Status:N', title='Status'),
                alt.Tooltip('Amount:Q', title='Amount', format='$,.0f'),
                alt.Tooltip('Rate:N', title='Tax Rate')
            ]
        ).properties(
            height=400
        )
        
        st.altair_chart(building_chart, use_container_width=True)
    else:
        st.info("Enter your income parameters in the sidebar to see the tax building visualization.")
    
    st.divider()
    
    # Strategic Prioritization
    st.markdown("### 🎯 Strategic Prioritization Matrix")
    
    penthouse_threshold = 181440
    penthouse_income = max(0, taxable_income - penthouse_threshold)
    penthouse_shield_needed = max(0, t4_gross_income - penthouse_threshold - total_rrsp_contributions)
    
    remaining_rrsp_room = max(0, rrsp_room - total_rrsp_contributions)
    remaining_tfsa_room = max(0, tfsa_room - tfsa_lump_sum)
    
    # Priority 1: Penthouse Shield
    if penthouse_income > 0:
        priority_1_status = f"⚠️ ${penthouse_income:,.0f} in Penthouse"
        priority_1_action = f"Deposit ${penthouse_shield_needed:,.0f} to RRSP"
        priority_1_impact = f"Save ${penthouse_income * 0.4797:,.0f} in taxes (47.97% rate)"
        priority_1_class = "priority-high"
    else:
        priority_1_status = "✅ Optimized"
        priority_1_action = "No Penthouse exposure"
        priority_1_impact = f"Maximum efficiency at {marginal_rate*100:.2f}% bracket"
        priority_1_class = "priority-medium"
    
    st.markdown(f'''
        <div class="premium-card {priority_1_class}">
            <h4>Priority 1: High-Rate Tax Shield</h4>
            <p><strong>Status:</strong> {priority_1_status}</p>
            <p><strong>Action:</strong> {priority_1_action}</p>
            <p><strong>Impact:</strong> {priority_1_impact}</p>
        </div>
    ''', unsafe_allow_html=True)
    
    # Priority 2: TFSA Maximization
    st.markdown(f'''
        <div class="premium-card priority-medium">
            <h4>Priority 2: Tax-Free Growth Acceleration</h4>
            <p><strong>Status:</strong> ${remaining_tfsa_room:,.0f} TFSA room remaining</p>
            <p><strong>Action:</strong> Maximize TFSA contributions for tax-free compounding</p>
            <p><strong>Impact:</strong> All future gains grow tax-free forever</p>
        </div>
    ''', unsafe_allow_html=True)
    
    st.divider()
    
    # THE FEEDBACK LOOP - Tax Refund Reinvestment
    st.markdown("### 🔄 The Feedback Loop: Refund Reinvestment")
    
    description_box(
        "Strategic Refund Deployment",
        f"Your RRSP contributions of ${total_rrsp_contributions:,.0f} will generate an estimated tax refund of ${estimated_refund:,.0f}. "
        "Deploy this refund strategically into your TFSA to accelerate tax-free wealth growth."
    )
    
    col_refund1, col_refund2, col_refund3 = st.columns(3)
    
    with col_refund1:
        st.metric(
            "Tax Refund Generated",
            f"${estimated_refund:,.0f}",
            help="Estimated refund from RRSP tax deductions"
        )
    
    with col_refund2:
        available_for_tfsa = min(estimated_refund, remaining_tfsa_room)
        st.metric(
            "Available for TFSA",
            f"${available_for_tfsa:,.0f}",
            help="Refund amount that fits in remaining TFSA room"
        )
    
    with col_refund3:
        reinvest_pct = (available_for_tfsa / max(1, estimated_refund)) * 100
        st.metric(
            "Reinvestment Rate",
            f"{reinvest_pct:.1f}%",
            help="Percentage of refund deployable to TFSA"
        )
    
    # Refund deployment calculator
    with st.expander("🧮 Refund Deployment Calculator", expanded=True):
        st.markdown("**Strategic Question:** How much of your tax refund will you reinvest into your TFSA?")
        
        if estimated_refund > 0:
            refund_to_deploy = st.slider(
                "Amount to reinvest in TFSA",
                0.0,
                float(estimated_refund),
                value=min(float(estimated_refund), float(remaining_tfsa_room)),
                step=100.0
            )
            
            st.caption(f"Selected amount: ${refund_to_deploy:,.0f}")
            
            col_deploy1, col_deploy2 = st.columns(2)
            
            with col_deploy1:
                st.markdown("**Deployment Impact:**")
                new_tfsa_total = tfsa_lump_sum + refund_to_deploy
                new_tfsa_room = max(0, tfsa_room - new_tfsa_total)
                
                st.write(f"- Total TFSA contribution: ${new_tfsa_total:,.0f}")
                st.write(f"- Remaining TFSA room: ${new_tfsa_room:,.0f}")
                st.write(f"- Combined tax-advantaged savings: ${total_rrsp_contributions + new_tfsa_total:,.0f}")
            
            with col_deploy2:
                st.markdown("**20-Year Growth Projection:**")
                # Assuming 7% annual return
                growth_rate = 0.07
                years = 20
                future_value = refund_to_deploy * ((1 + growth_rate) ** years)
                tax_saved_at_withdrawal = future_value * marginal_rate
                
                st.write(f"- Refund deployed: ${refund_to_deploy:,.0f}")
                st.write(f"- Future value @ 7%: ${future_value:,.0f}")
                st.write(f"- Tax saved (vs. taxable): ${tax_saved_at_withdrawal:,.0f}")
        else:
            st.info("💡 Make RRSP contributions to generate a tax refund that can be reinvested into your TFSA for tax-free growth.")
    
    st.divider()
    
    # March 1st Deadline Dashboard
    st.markdown(f"### 📅 March 1st Deadline Dashboard ({selected_year + 1})")
    
    col_deadline = st.columns([3, 1])
    with col_deadline[1]:
        components.html('''
            <button onclick="window.print()" 
                style="width: 100%; height: 60px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
                color: white; border: none; border-radius: 10px; font-weight: 600; 
                cursor: pointer; box-shadow: 0 4px 6px rgba(59, 130, 246, 0.4);
                transition: all 0.3s ease;">
                📄 Save as PDF
            </button>
        ''', height=80)
    
    st.markdown(f"""
        <div class="premium-card">
            <h4>Critical Action Items Before March 1, {selected_year + 1}</h4>
            <p style="color: #64748b; margin-bottom: 20px;">
                These deposits must be completed to claim deductions for tax year {selected_year}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    ac1, ac2, ac3, ac4 = st.columns(4)
    
    with ac1:
        st.metric(
            "RRSP Lump Sum Due",
            f"${rrsp_lump_sum:,.0f}",
            help="One-time deposit needed before deadline"
        )
    
    with ac2:
        st.metric(
            "TFSA Deployment",
            f"${tfsa_lump_sum:,.0f}",
            help="Planned TFSA contribution"
        )
    
    with ac3:
        st.metric(
            "Expected Refund",
            f"${estimated_refund:,.0f}",
            delta=f"+{(estimated_refund/max(1,total_rrsp_contributions))*100:.1f}%",
            help="Tax refund from all RRSP contributions"
        )
    
    with ac4:
        net_cashflow = estimated_refund - rrsp_lump_sum - tfsa_lump_sum
        st.metric(
            "Net Cashflow Impact",
            f"${net_cashflow:,.0f}",
            delta="Surplus" if net_cashflow >= 0 else "Investment",
            delta_color="normal" if net_cashflow >= 0 else "inverse",
            help="Refund minus deposits"
        )
    
    st.divider()
    
    # Carryover Room Projection
    st.markdown(f"### ⏭️ {selected_year + 1} Carryover Room Projection")
    
    description_box(
        "Forward-Looking Planning",
        f"Based on CRA's indexed limits and your {selected_year} contributions, "
        "here's your projected contribution room for next year."
    )
    
    # RRSP new room calculation (18% of income, max $31,560 for 2025)
    rrsp_earned_room = min(31560, t4_gross_income * 0.18)
    projected_rrsp_room = remaining_rrsp_room + rrsp_earned_room
    
    # TFSA new room (indexed amount, $7,000 for 2025)
    tfsa_earned_room = 7000
    projected_tfsa_room = remaining_tfsa_room + tfsa_earned_room
    
    col_carry1, col_carry2 = st.columns(2)
    
    with col_carry1:
        st.markdown("**RRSP Room Evolution**")
        st.metric(
            f"{selected_year + 1} Projected RRSP Room",
            f"${projected_rrsp_room:,.0f}",
            delta=f"+${rrsp_earned_room:,.0f} new",
            help="Unused room + newly earned contribution room"
        )
        
        st.progress(min(1.0, total_rrsp_contributions / max(1, rrsp_room)))
        st.caption(f"You used {(total_rrsp_contributions/max(1,rrsp_room))*100:.1f}% of available RRSP room in {selected_year}")
    
    with col_carry2:
        st.markdown("**TFSA Room Evolution**")
        st.metric(
            f"{selected_year + 1} Projected TFSA Room",
            f"${projected_tfsa_room:,.0f}",
            delta=f"+${tfsa_earned_room:,.0f} new",
            help="Unused room + annual indexed increase"
        )
        
        st.progress(min(1.0, tfsa_lump_sum / max(1, tfsa_room)))
        st.caption(f"You used {(tfsa_lump_sum/max(1,tfsa_room))*100:.1f}% of available TFSA room in {selected_year}")
    
    st.divider()
    
    # Tax Bracket Reference
    st.markdown("### 📑 Ontario Tax Bracket Reference (Combined Federal + Provincial)")
    
    with st.expander("📊 View Detailed Bracket Information", expanded=False):
        description_box(
            "2025/2026 Marginal Tax Rates",
            "These are the combined federal and Ontario provincial marginal tax rates. "
            "Your marginal rate is the tax you pay on each additional dollar earned."
        )
        
        bracket_df = pd.DataFrame([
            {
                "Floor Level": bracket['name'],
                "Income Range": f"${bracket['low']:,} - ${bracket['high']:,}" if bracket['high'] != float('inf') else f"${bracket['low']:,}+",
                "Marginal Rate": f"{bracket['rate']*100:.2f}%",
                "Tax on $1,000": f"${1000 * bracket['rate']:.2f}"
            }
            for bracket in TAX_BRACKETS
        ])
        
        st.dataframe(
            bracket_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Highlight current bracket
        current_bracket = None
        for bracket in TAX_BRACKETS:
            if bracket['low'] <= taxable_income < bracket['high']:
                current_bracket = bracket
                break
        
        if current_bracket and taxable_income > 0:
            st.info(f"📍 Your current marginal bracket: **{current_bracket['name']}** at **{current_bracket['rate']*100:.2f}%**")
    
    # Strategic Insights
    st.divider()
    st.markdown("### 💡 Strategic Insights & Recommendations")
    
    insights = []
    
    # Insight 1: Penthouse exposure
    if penthouse_income > 0:
        insights.append({
            "icon": "⚠️",
            "title": "High Priority: Penthouse Exposure",
            "message": f"You have ${penthouse_income:,.0f} exposed to the Penthouse rate (47.97%). "
                      f"Consider depositing an additional ${penthouse_shield_needed:,.0f} to your RRSP before March 1st "
                      f"to save ${penthouse_income * 0.4797:,.0f} in taxes.",
            "priority": "high"
        })
    
    # Insight 2: Unused RRSP room
    if remaining_rrsp_room > 10000:
        insights.append({
            "icon": "💰",
            "title": "Opportunity: Unused RRSP Room",
            "message": f"You have ${remaining_rrsp_room:,.0f} of unused RRSP room. "
                      f"At your marginal rate of {marginal_rate*100:.2f}%, every additional $10,000 contributed "
                      f"would generate a ${10000 * marginal_rate:,.0f} tax refund.",
            "priority": "medium"
        })
    
    # Insight 3: TFSA optimization
    if remaining_tfsa_room > 5000:
        insights.append({
            "icon": "🌱",
            "title": "Growth Opportunity: TFSA Capacity",
            "message": f"You have ${remaining_tfsa_room:,.0f} of unused TFSA room. "
                      f"Consider deploying your ${estimated_refund:,.0f} tax refund into this tax-free growth vehicle. "
                      f"Over 20 years at 7% annual returns, this could grow to ${estimated_refund * (1.07**20):,.0f} tax-free.",
            "priority": "medium"
        })
    
    # Insight 4: Employer match
    if employer_match > 0:
        employer_contribution = base_salary * (employer_match / 100)
        insights.append({
            "icon": "🎁",
            "title": "Free Money: Employer Match",
            "message": f"Your employer is contributing ${employer_contribution:,.0f} annually ({employer_match}% match). "
                      f"This is a {employer_match*100:.0f}% instant return on your contributions. "
                      f"Always maximize employer matching contributions first.",
            "priority": "high"
        })
    
    # Insight 5: Efficiency score
    efficiency_score = (total_rrsp_contributions / max(1, rrsp_room)) * 0.5 + \
                      (tfsa_lump_sum / max(1, tfsa_room)) * 0.5
    
    if efficiency_score < 0.5:
        insights.append({
            "icon": "📈",
            "title": "Efficiency Opportunity",
            "message": f"Your contribution room utilization is {efficiency_score*100:.1f}%. "
                      f"You're leaving significant tax advantages on the table. "
                      f"Consider increasing your automatic contributions or making larger lump-sum deposits.",
            "priority": "medium"
        })
    elif efficiency_score > 0.8:
        insights.append({
            "icon": "✨",
            "title": "Excellent Optimization",
            "message": f"Your contribution room utilization is {efficiency_score*100:.1f}%. "
                      f"You're making excellent use of your available tax-advantaged space. "
                      f"Keep up this disciplined approach to wealth building!",
            "priority": "high"
        })
    
    # Display insights
    for insight in insights:
        priority_class = "priority-high" if insight['priority'] == "high" else "priority-medium"
        st.markdown(f'''
            <div class="premium-card {priority_class}">
                <h4>{insight['icon']} {insight['title']}</h4>
                <p style="line-height: 1.6;">{insight['message']}</p>
            </div>
        ''', unsafe_allow_html=True)
    
    if not insights:
        st.success("✅ Your strategy is well-optimized! No critical action items identified.")

# Footer
st.divider()
st.markdown("""
    <div style="text-align: center; color: #64748b; padding: 20px;">
        <p><strong>Canadian Tax & Wealth Velocity Suite</strong></p>
        <p style="font-size: 0.9em;">
            Tax rates are based on 2025/2026 Ontario combined federal + provincial brackets. 
            Always consult with a qualified tax professional for personalized advice.
        </p>
        <p style="font-size: 0.85em; margin-top: 10px;">
            RRSP contribution limit: 18% of previous year's income (max $31,560) | 
            TFSA annual limit: $7,000
        </p>
    </div>
""", unsafe_allow_html=True)
