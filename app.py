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

def is_year_optimized(year_data):
    """Check if a year is optimized (minimizing penthouse exposure)"""
    if not year_data:
        return False
    
    # Calculate values
    t4_gross = year_data.get('t4_gross_income', 0)
    other_inc = year_data.get('other_income', 0)
    total_gross = t4_gross + other_inc
    base_salary = year_data.get('base_salary', 0)
    biweekly_pct = year_data.get('biweekly_pct', 0)
    employer_match = year_data.get('employer_match', 0)
    rrsp_opt = year_data.get('rrsp_lump_sum_optimization', 0)
    rrsp_add = year_data.get('rrsp_lump_sum_additional', 0)
    rrsp_legacy = year_data.get('rrsp_lump_sum', 0)
    
    annual_rrsp_periodic = base_salary * ((biweekly_pct + employer_match) / 100)
    total_rrsp = annual_rrsp_periodic + rrsp_opt + rrsp_add + rrsp_legacy
    taxable_income = max(0, total_gross - total_rrsp)
    
    # Optimized if no penthouse exposure (taxable income under $181,440)
    penthouse_threshold = 181440
    return taxable_income < penthouse_threshold

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
        border-left: 4px solid #ef4444;
    }
    
    .year-tile-progress {
        border-left: 4px solid #f97316;
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
        latest_rrsp_balance = 0
        latest_tfsa_balance = 0
        
        # Get the latest year's ending balance
        latest_year = max(all_history.keys(), key=lambda x: int(x))
        latest_data = all_history[latest_year]
        
        for yr, data in all_history.items():
            t4_gross = data.get('t4_gross_income', 0)
            other_inc = data.get('other_income', 0)
            total_gross = t4_gross + other_inc
            
            annual_rrsp = (data.get('base_salary', 0) * 
                          (data.get('biweekly_pct', 0) + data.get('employer_match', 0)) / 100) + \
                          data.get('rrsp_lump_sum_optimization', 0) + \
                          data.get('rrsp_lump_sum_additional', 0) + \
                          data.get('rrsp_lump_sum', 0)  # Legacy support
            tfsa_contrib = data.get('tfsa_lump_sum', 0)
            
            total_rrsp_all += annual_rrsp
            total_tfsa_all += tfsa_contrib
            
            # Calculate tax shield value
            refund = calculate_tax_refund(total_gross, annual_rrsp)
            total_tax_shield += refund
        
        # Get projected balances from latest year
        if latest_data:
            target_cagr = latest_data.get("target_cagr", 7.0) / 100
            rrsp_start = latest_data.get("rrsp_balance_start", 0)
            tfsa_start = latest_data.get("tfsa_balance_start", 0)
            
            annual_rrsp = (latest_data.get('base_salary', 0) * 
                          (latest_data.get('biweekly_pct', 0) + latest_data.get('employer_match', 0)) / 100) + \
                          latest_data.get('rrsp_lump_sum', 0)
            tfsa_contrib = latest_data.get('tfsa_lump_sum', 0)
            
            rrsp_growth = rrsp_start * target_cagr + annual_rrsp * (target_cagr / 2)
            tfsa_growth = tfsa_start * target_cagr + tfsa_contrib * (target_cagr / 2)
            
            latest_rrsp_balance = rrsp_start + rrsp_growth + annual_rrsp
            latest_tfsa_balance = tfsa_start + tfsa_growth + tfsa_contrib
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Current RRSP Balance",
                f"${latest_rrsp_balance:,.0f}",
                delta=f"{total_rrsp_all:,.0f} lifetime contrib",
                help=f"Projected balance as of end of {latest_year}"
            )
        
        with col2:
            st.metric(
                "Current TFSA Balance",
                f"${latest_tfsa_balance:,.0f}",
                delta=f"{total_tfsa_all:,.0f} lifetime contrib",
                help=f"Projected balance as of end of {latest_year}"
            )
        
        with col3:
            st.metric(
                "Total Tax Shield Value",
                f"${total_tax_shield:,.0f}",
                help="Cumulative tax refunds generated from RRSP contributions"
            )
        
        with col4:
            st.metric(
                "Total Portfolio Value",
                f"${latest_rrsp_balance + latest_tfsa_balance:,.0f}",
                delta=f"+${(latest_rrsp_balance + latest_tfsa_balance) - (total_rrsp_all + total_tfsa_all):,.0f} growth",
                help="Combined RRSP + TFSA current value"
            )
        
        st.divider()
        
        # Multi-Year Portfolio Growth Chart
        st.markdown("### 📈 Portfolio Growth Over Time")
        
        portfolio_history = []
        
        for yr in sorted(all_history.keys(), key=lambda x: int(x)):
            data = all_history[yr]
            
            target_cagr = data.get("target_cagr", 7.0) / 100
            rrsp_start = data.get("rrsp_balance_start", 0)
            tfsa_start = data.get("tfsa_balance_start", 0)
            
            annual_rrsp = (data.get('base_salary', 0) * 
                          (data.get('biweekly_pct', 0) + data.get('employer_match', 0)) / 100) + \
                          data.get('rrsp_lump_sum_optimization', 0) + \
                          data.get('rrsp_lump_sum_additional', 0) + \
                          data.get('rrsp_lump_sum', 0)  # Legacy support
            tfsa_contrib = data.get('tfsa_lump_sum', 0)
            
            # Start of year
            portfolio_history.append({
                "Year": f"{yr} (Jan)",
                "RRSP Balance": rrsp_start,
                "TFSA Balance": tfsa_start,
                "Total": rrsp_start + tfsa_start
            })
            
            # End of year (with growth and contributions)
            rrsp_growth = rrsp_start * target_cagr + annual_rrsp * (target_cagr / 2)
            tfsa_growth = tfsa_start * target_cagr + tfsa_contrib * (target_cagr / 2)
            
            rrsp_end = rrsp_start + rrsp_growth + annual_rrsp
            tfsa_end = tfsa_start + tfsa_growth + tfsa_contrib
            
            portfolio_history.append({
                "Year": f"{yr} (Dec)",
                "RRSP Balance": rrsp_end,
                "TFSA Balance": tfsa_end,
                "Total": rrsp_end + tfsa_end
            })
        
        if portfolio_history:
            df_portfolio = pd.DataFrame(portfolio_history)
            
            # Stacked area chart for portfolio composition
            portfolio_melted = df_portfolio[['Year', 'RRSP Balance', 'TFSA Balance']].melt(
                'Year',
                var_name='Account',
                value_name='Balance'
            )
            
            portfolio_chart = alt.Chart(portfolio_melted).mark_area(
                opacity=0.8,
                line=True
            ).encode(
                x=alt.X('Year:N', title='Timeline', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('Balance:Q', title='Portfolio Value ($)', stack='zero'),
                color=alt.Color('Account:N',
                    scale=alt.Scale(
                        domain=['RRSP Balance', 'TFSA Balance'],
                        range=['#3b82f6', '#10b981']
                    ),
                    legend=alt.Legend(title="Account Type")
                ),
                tooltip=[
                    alt.Tooltip('Year:N', title='Period'),
                    alt.Tooltip('Account:N', title='Account'),
                    alt.Tooltip('Balance:Q', title='Balance', format='$,.0f')
                ]
            ).properties(height=400)
            
            st.altair_chart(portfolio_chart, use_container_width=True)
            
            # Summary stats
            col_stats1, col_stats2, col_stats3 = st.columns(3)
            
            first_total = df_portfolio.iloc[0]['Total']
            last_total = df_portfolio.iloc[-1]['Total']
            total_return = last_total - first_total
            total_return_pct = (total_return / max(1, first_total)) * 100
            
            with col_stats1:
                st.metric(
                    "Total Growth",
                    f"${total_return:,.0f}",
                    delta=f"+{total_return_pct:.1f}%"
                )
            
            with col_stats2:
                years_tracked = len(all_history)
                annualized_return = ((last_total / max(1, first_total)) ** (1 / max(1, years_tracked)) - 1) * 100 if first_total > 0 else 0
                st.metric(
                    "Annualized Return",
                    f"{annualized_return:.2f}%",
                    help="Compound annual growth rate across tracked years"
                )
            
            with col_stats3:
                st.metric(
                    "Years Tracked",
                    f"{years_tracked}",
                    help="Number of years with saved data"
                )
        
        st.divider()
    
    # Planning Years Grid
    st.markdown("### 📅 Planning Years")
    
    # Add new year functionality - simple row
    col_add1, col_add2, col_add3 = st.columns([2, 1, 1])
    with col_add1:
        new_year_input = st.number_input(
            "Add Planning Year",
            min_value=2020,
            max_value=2050,
            value=2031,
            step=1,
            key="new_year_input"
        )
    with col_add2:
        if st.button("➕ Add Year", use_container_width=True):
            if str(new_year_input) not in all_history:
                # Create empty year entry
                save_year_data(new_year_input, {
                    "t4_gross_income": 0,
                    "other_income": 0,
                    "base_salary": 0,
                    "biweekly_pct": 0,
                    "employer_match": 0,
                    "rrsp_lump_sum_optimization": 0,
                    "rrsp_lump_sum_additional": 0,
                    "tfsa_lump_sum": 0,
                    "rrsp_room": 0,
                    "tfsa_room": 0,
                    "rrsp_balance_start": 0,
                    "tfsa_balance_start": 0,
                    "target_cagr": 7.0
                })
                st.success(f"✓ Year {new_year_input} added!")
                st.rerun()
            else:
                st.warning(f"Year {new_year_input} already exists!")
    with col_add3:
        st.write("")  # Spacer
    
    st.divider()
    
    # Get all years (saved + default range)
    all_years = set(range(2024, 2031))
    all_years.update([int(yr) for yr in all_history.keys()])
    years_to_show = sorted(list(all_years))
    
    cols_per_row = 4
    
    for row_start in range(0, len(years_to_show), cols_per_row):
        cols = st.columns(cols_per_row)
        for i, yr in enumerate(years_to_show[row_start:row_start + cols_per_row]):
            with cols[i]:
                is_saved = str(yr) in all_history
                is_optimized = is_year_optimized(all_history.get(str(yr), {})) if is_saved else False
                
                # Determine status and styling
                if not is_saved:
                    # Red - Empty
                    status_emoji = "🔴"
                    status_text = "Empty"
                    button_label = f"📅 **{yr}**\n{status_emoji} {status_text}"
                    container_style = "background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); border: 2px solid #ef4444; border-radius: 12px; padding: 4px;"
                elif is_optimized:
                    # Green - Optimized
                    data = all_history[str(yr)]
                    annual_rrsp = (data.get('base_salary', 0) * 
                                  (data.get('biweekly_pct', 0) + data.get('employer_match', 0)) / 100) + \
                                  data.get('rrsp_lump_sum_optimization', 0) + \
                                  data.get('rrsp_lump_sum_additional', 0) + \
                                  data.get('rrsp_lump_sum', 0)
                    status_emoji = "🟢"
                    status_text = f"${annual_rrsp:,.0f}"
                    button_label = f"📅 **{yr}**\n{status_text}\n{status_emoji} Optimized"
                    container_style = "background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border: 2px solid #10b981; border-radius: 12px; padding: 4px;"
                else:
                    # Orange - In Progress
                    data = all_history[str(yr)]
                    annual_rrsp = (data.get('base_salary', 0) * 
                                  (data.get('biweekly_pct', 0) + data.get('employer_match', 0)) / 100) + \
                                  data.get('rrsp_lump_sum_optimization', 0) + \
                                  data.get('rrsp_lump_sum_additional', 0) + \
                                  data.get('rrsp_lump_sum', 0)
                    status_emoji = "🟠"
                    status_text = f"${annual_rrsp:,.0f}"
                    button_label = f"📅 **{yr}**\n{status_text}\n{status_emoji} In Progress"
                    container_style = "background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%); border: 2px solid #f97316; border-radius: 12px; padding: 4px;"
                
                # Wrap button in styled container
                st.markdown(f'<div style="{container_style}">', unsafe_allow_html=True)
                
                # Create the button
                if st.button(
                    button_label,
                    key=f"home_{yr}",
                    use_container_width=True,
                    type="primary" if is_saved else "secondary"
                ):
                    st.session_state.selected_year = yr
                    st.session_state.current_page = "Year View"
                    st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Multi-Year Analytics
    if all_history and len(all_history) > 1:
        st.divider()
        st.markdown("### 📈 Multi-Year Analytics & Trends")
        
        # Prepare data for charts
        chart_data = []
        room_data = []
        burndown_data = []
        
        for yr, data in sorted(all_history.items(), key=lambda x: x[0]):
            t4_gross = data.get('t4_gross_income', 0)
            other_inc = data.get('other_income', 0)
            total_gross = t4_gross + other_inc
            
            annual_rrsp = (data.get('base_salary', 0) * 
                          (data.get('biweekly_pct', 0) + data.get('employer_match', 0)) / 100) + \
                          data.get('rrsp_lump_sum_optimization', 0) + \
                          data.get('rrsp_lump_sum_additional', 0) + \
                          data.get('rrsp_lump_sum', 0)  # Legacy support
            tfsa_contrib = data.get('tfsa_lump_sum', 0)
            gross = total_gross
            
            rrsp_room_avail = data.get('rrsp_room', 0)
            tfsa_room_avail = data.get('tfsa_room', 0)
            
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
                "Remaining Room": max(0, rrsp_room_avail - annual_rrsp)
            })
            room_data.append({
                "Year": yr,
                "Account": "TFSA",
                "Remaining Room": max(0, tfsa_room_avail - tfsa_contrib)
            })
            
            # Burndown data - showing used vs available
            burndown_data.append({
                "Year": yr,
                "Account": "RRSP",
                "Status": "Used",
                "Amount": annual_rrsp
            })
            burndown_data.append({
                "Year": yr,
                "Account": "RRSP",
                "Status": "Available",
                "Amount": max(0, rrsp_room_avail - annual_rrsp)
            })
            burndown_data.append({
                "Year": yr,
                "Account": "TFSA",
                "Status": "Used",
                "Amount": tfsa_contrib
            })
            burndown_data.append({
                "Year": yr,
                "Account": "TFSA",
                "Status": "Available",
                "Amount": max(0, tfsa_room_avail - tfsa_contrib)
            })
        
        df_chart = pd.DataFrame(chart_data)
        df_room = pd.DataFrame(room_data)
        df_burndown = pd.DataFrame(burndown_data)
        
        # RRSP & TFSA Burndown Charts
        st.markdown("**Contribution Room Burndown Analysis**")
        st.caption("See how much room you're using vs. leaving unused each year")
        
        col_burn1, col_burn2 = st.columns(2)
        
        with col_burn1:
            st.markdown("**RRSP Room Utilization**")
            
            rrsp_burndown = df_burndown[df_burndown['Account'] == 'RRSP']
            
            rrsp_chart = alt.Chart(rrsp_burndown).mark_bar().encode(
                x=alt.X('Year:N', title='Year'),
                y=alt.Y('Amount:Q', title='RRSP Room ($)', stack='zero'),
                color=alt.Color('Status:N',
                    scale=alt.Scale(
                        domain=['Used', 'Available'],
                        range=['#10b981', '#e2e8f0']
                    ),
                    legend=alt.Legend(title="Room Status")
                ),
                tooltip=[
                    alt.Tooltip('Year:N', title='Year'),
                    alt.Tooltip('Status:N', title='Status'),
                    alt.Tooltip('Amount:Q', title='Amount', format='$,.0f')
                ]
            ).properties(height=320)
            
            st.altair_chart(rrsp_chart, use_container_width=True)
            
            # Calculate average utilization
            total_used = rrsp_burndown[rrsp_burndown['Status'] == 'Used']['Amount'].sum()
            total_available = rrsp_burndown['Amount'].sum()
            utilization = (total_used / total_available * 100) if total_available > 0 else 0
            st.metric("Avg RRSP Utilization", f"{utilization:.1f}%")
        
        with col_burn2:
            st.markdown("**TFSA Room Utilization**")
            
            tfsa_burndown = df_burndown[df_burndown['Account'] == 'TFSA']
            
            tfsa_chart = alt.Chart(tfsa_burndown).mark_bar().encode(
                x=alt.X('Year:N', title='Year'),
                y=alt.Y('Amount:Q', title='TFSA Room ($)', stack='zero'),
                color=alt.Color('Status:N',
                    scale=alt.Scale(
                        domain=['Used', 'Available'],
                        range=['#3b82f6', '#e2e8f0']
                    ),
                    legend=alt.Legend(title="Room Status")
                ),
                tooltip=[
                    alt.Tooltip('Year:N', title='Year'),
                    alt.Tooltip('Status:N', title='Status'),
                    alt.Tooltip('Amount:Q', title='Amount', format='$,.0f')
                ]
            ).properties(height=320)
            
            st.altair_chart(tfsa_chart, use_container_width=True)
            
            # Calculate average utilization
            total_used = tfsa_burndown[tfsa_burndown['Status'] == 'Used']['Amount'].sum()
            total_available = tfsa_burndown['Amount'].sum()
            utilization = (total_used / total_available * 100) if total_available > 0 else 0
            st.metric("Avg TFSA Utilization", f"{utilization:.1f}%")
        
        st.divider()
        
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
            st.markdown("**Remaining Room Trajectory**")
            
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
            
            other_income = st.number_input(
                "Other Income",
                value=float(year_data.get("other_income", 0)),
                step=1000.0,
                min_value=0.0,
                help="Additional taxable income (e.g., rental property net income after expenses)"
            )
            
            base_salary = st.number_input(
                "Annual Base Salary",
                value=float(year_data.get("base_salary", 0)),
                step=5000.0,
                min_value=0.0,
                help="Core salary used for percentage-based contributions"
            )
            
            st.caption(f"💰 Total Gross Income: ${t4_gross_income + other_income:,.0f}")
            
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
            
            rrsp_lump_sum_optimization = st.number_input(
                "RRSP Lump Sum (Tax Optimization)",
                value=float(year_data.get("rrsp_lump_sum_optimization", 0)),
                step=1000.0,
                min_value=0.0,
                help="Strategic deposit to optimize tax bracket positioning"
            )
            
            rrsp_lump_sum_additional = st.number_input(
                "RRSP Lump Sum (Additional Refund)",
                value=float(year_data.get("rrsp_lump_sum_additional", 0)),
                step=1000.0,
                min_value=0.0,
                help="Extra contributions to maximize tax refund beyond optimization"
            )
            
            st.caption(f"💰 Total RRSP Lump Sum: ${rrsp_lump_sum_optimization + rrsp_lump_sum_additional:,.0f}")
            
            st.markdown("### 🌱 TFSA Strategy")
            
            tfsa_lump_sum = st.number_input(
                "TFSA Lump Sum Deposit",
                value=float(year_data.get("tfsa_lump_sum", 0)),
                step=1000.0,
                min_value=0.0,
                help="Tax-free savings account contribution"
            )
            
            st.markdown("### 📋 CRA Contribution Limits")
            
            # Get default values from previous year if available
            prev_year = str(selected_year - 1)
            default_rrsp_room = 0.0
            default_tfsa_room = 0.0
            
            if prev_year in all_history:
                prev_data = all_history[prev_year]
                
                # Calculate remaining room from previous year
                prev_annual_rrsp = (prev_data.get('base_salary', 0) * 
                                   (prev_data.get('biweekly_pct', 0) + prev_data.get('employer_match', 0)) / 100) + \
                                   prev_data.get('rrsp_lump_sum_optimization', 0) + \
                                   prev_data.get('rrsp_lump_sum_additional', 0)
                prev_tfsa_contrib = prev_data.get('tfsa_lump_sum', 0)
                
                prev_rrsp_room_remaining = max(0, prev_data.get('rrsp_room', 0) - prev_annual_rrsp)
                prev_tfsa_room_remaining = max(0, prev_data.get('tfsa_room', 0) - prev_tfsa_contrib)
                
                # Add new room for current year
                new_rrsp_room = min(31560, prev_data.get('t4_gross_income', 0) * 0.18)
                new_tfsa_room = 7000
                
                default_rrsp_room = prev_rrsp_room_remaining + new_rrsp_room
                default_tfsa_room = prev_tfsa_room_remaining + new_tfsa_room
            
            rrsp_room = st.number_input(
                "Available RRSP Room",
                value=float(year_data.get("rrsp_room", default_rrsp_room)),
                step=1000.0,
                min_value=0.0,
                help="From your latest Notice of Assessment (auto-filled from previous year if available)"
            )
            
            tfsa_room = st.number_input(
                "Available TFSA Room",
                value=float(year_data.get("tfsa_room", default_tfsa_room)),
                step=1000.0,
                min_value=0.0,
                help="From CRA MyAccount (auto-filled from previous year if available)"
            )
            
            if prev_year in all_history and default_rrsp_room > 0:
                st.caption(f"ℹ️ Auto-calculated from {prev_year} carryover + new room")
            
            st.markdown("### 📈 Portfolio Tracking")
            
            # Calculate default values from previous year's end balances
            prev_year = str(selected_year - 1)
            default_rrsp_balance = 0.0
            default_tfsa_balance = 0.0
            
            if prev_year in all_history:
                prev_data = all_history[prev_year]
                
                # Get previous year's values
                prev_target_cagr = prev_data.get("target_cagr", 7.0) / 100
                prev_rrsp_start = prev_data.get("rrsp_balance_start", 0)
                prev_tfsa_start = prev_data.get("tfsa_balance_start", 0)
                
                # Calculate previous year's contributions
                prev_annual_rrsp = (prev_data.get('base_salary', 0) * 
                                   (prev_data.get('biweekly_pct', 0) + prev_data.get('employer_match', 0)) / 100) + \
                                   prev_data.get('rrsp_lump_sum_optimization', 0) + \
                                   prev_data.get('rrsp_lump_sum_additional', 0) + \
                                   prev_data.get('rrsp_lump_sum', 0)  # Legacy
                prev_tfsa_contrib = prev_data.get('tfsa_lump_sum', 0)
                
                # Calculate previous year's growth
                prev_rrsp_growth = prev_rrsp_start * prev_target_cagr + prev_annual_rrsp * (prev_target_cagr / 2)
                prev_tfsa_growth = prev_tfsa_start * prev_target_cagr + prev_tfsa_contrib * (prev_target_cagr / 2)
                
                # End balances become start balances for current year
                default_rrsp_balance = prev_rrsp_start + prev_rrsp_growth + prev_annual_rrsp
                default_tfsa_balance = prev_tfsa_start + prev_tfsa_growth + prev_tfsa_contrib
            
            rrsp_balance_start = st.number_input(
                "RRSP Balance (Start of Year)",
                value=float(year_data.get("rrsp_balance_start", default_rrsp_balance)),
                step=1000.0,
                min_value=0.0,
                help="Total RRSP portfolio value on January 1st (auto-calculated from previous year if available)"
            )
            
            tfsa_balance_start = st.number_input(
                "TFSA Balance (Start of Year)",
                value=float(year_data.get("tfsa_balance_start", default_tfsa_balance)),
                step=1000.0,
                min_value=0.0,
                help="Total TFSA portfolio value on January 1st (auto-calculated from previous year if available)"
            )
            
            if prev_year in all_history and default_rrsp_balance > 0:
                st.caption(f"ℹ️ Auto-calculated from {prev_year} end-of-year projected balances")
            
            target_cagr = st.slider(
                "Target Annual Return (CAGR %)",
                0.0, 50.0,
                value=float(year_data.get("target_cagr", 7.0)),
                step=0.5,
                help="Expected compound annual growth rate for investments (0-50%)"
            )
            
            st.caption(f"📊 Using {target_cagr}% CAGR for growth projections")
            
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
                    "other_income": other_income,
                    "base_salary": base_salary,
                    "biweekly_pct": biweekly_pct,
                    "employer_match": employer_match,
                    "rrsp_lump_sum_optimization": rrsp_lump_sum_optimization,
                    "rrsp_lump_sum_additional": rrsp_lump_sum_additional,
                    "tfsa_lump_sum": tfsa_lump_sum,
                    "rrsp_room": rrsp_room,
                    "tfsa_room": tfsa_room,
                    "rrsp_balance_start": rrsp_balance_start,
                    "tfsa_balance_start": tfsa_balance_start,
                    "target_cagr": target_cagr
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
    other_income = year_data.get("other_income", 0)
    total_gross_income = t4_gross_income + other_income
    
    annual_rrsp_periodic = base_salary * ((biweekly_pct + employer_match) / 100)
    rrsp_lump_sum = rrsp_lump_sum_optimization + rrsp_lump_sum_additional
    total_rrsp_contributions = annual_rrsp_periodic + rrsp_lump_sum
    taxable_income = max(0, total_gross_income - total_rrsp_contributions)
    
    # Portfolio calculations
    rrsp_balance_start = year_data.get("rrsp_balance_start", 0)
    tfsa_balance_start = year_data.get("tfsa_balance_start", 0)
    target_cagr = year_data.get("target_cagr", 7.0) / 100  # Convert to decimal
    
    # Calculate end of year balances (growth + new contributions)
    # Assuming contributions happen throughout the year, use half-year growth on new money
    rrsp_growth_existing = rrsp_balance_start * target_cagr
    rrsp_growth_new_contrib = total_rrsp_contributions * (target_cagr / 2)  # Half year average
    rrsp_balance_end = rrsp_balance_start + rrsp_growth_existing + total_rrsp_contributions + rrsp_growth_new_contrib
    
    tfsa_growth_existing = tfsa_balance_start * target_cagr
    tfsa_growth_new_contrib = tfsa_lump_sum * (target_cagr / 2)
    tfsa_balance_end = tfsa_balance_start + tfsa_growth_existing + tfsa_lump_sum + tfsa_growth_new_contrib
    
    total_portfolio_value = rrsp_balance_end + tfsa_balance_end
    
    # Calculate tax refund
    estimated_refund = calculate_tax_refund(total_gross_income, total_rrsp_contributions)
    marginal_rate = get_marginal_rate(total_gross_income)
    
    # Header
    st.title(f"🏛️ Tax Optimization Strategy: {selected_year}")
    
    description_box(
        "Strategic Execution Framework",
        f"Follow this comprehensive plan to maximize your tax efficiency and wealth velocity for {selected_year}. "
        "Each section provides actionable insights to optimize your contribution strategy."
    )
    
    # Key Metrics Dashboard
    st.markdown("### 📊 Strategic Overview")
    
    if other_income > 0:
        st.info(f"💼 Income Breakdown: T4 ${t4_gross_income:,.0f} + Other ${other_income:,.0f} = Total ${total_gross_income:,.0f}")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Gross Income",
            f"${total_gross_income:,.0f}",
            delta=f"+${other_income:,.0f} other" if other_income > 0 else None,
            help="T4 employment income plus other taxable income"
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
    
    with col5:
        st.metric(
            "Total Portfolio Value",
            f"${total_portfolio_value:,.0f}",
            delta=f"+{target_cagr*100:.1f}% target",
            help="Combined RRSP + TFSA projected end-of-year value"
        )
    
    # Portfolio Growth Dashboard
    if rrsp_balance_start > 0 or tfsa_balance_start > 0:
        st.divider()
        st.markdown("### 💼 Portfolio Growth Tracker")
        
        description_box(
            "Year-End Portfolio Projection",
            f"Based on {target_cagr*100:.1f}% annual return assumption. Growth calculated on existing balance (full year) and new contributions (half year average)."
        )
        
        # Create portfolio table
        portfolio_table_data = []
        
        # RRSP Row
        portfolio_table_data.append({
            "Account": "RRSP",
            "Start Balance": f"${rrsp_balance_start:,.0f}",
            "New Contributions": f"${total_rrsp_contributions:,.0f}",
            "Investment Growth": f"${rrsp_growth_existing + rrsp_growth_new_contrib:,.0f}",
            "End Balance": f"${rrsp_balance_end:,.0f}",
            "Net Gain": f"${rrsp_balance_end - rrsp_balance_start:,.0f}"
        })
        
        # TFSA Row
        portfolio_table_data.append({
            "Account": "TFSA",
            "Start Balance": f"${tfsa_balance_start:,.0f}",
            "New Contributions": f"${tfsa_lump_sum:,.0f}",
            "Investment Growth": f"${tfsa_growth_existing + tfsa_growth_new_contrib:,.0f}",
            "End Balance": f"${tfsa_balance_end:,.0f}",
            "Net Gain": f"${tfsa_balance_end - tfsa_balance_start:,.0f}"
        })
        
        # Total Row
        total_start = rrsp_balance_start + tfsa_balance_start
        total_contributions = total_rrsp_contributions + tfsa_lump_sum
        total_growth = (rrsp_growth_existing + rrsp_growth_new_contrib + 
                      tfsa_growth_existing + tfsa_growth_new_contrib)
        
        portfolio_table_data.append({
            "Account": "**TOTAL**",
            "Start Balance": f"**${total_start:,.0f}**",
            "New Contributions": f"**${total_contributions:,.0f}**",
            "Investment Growth": f"**${total_growth:,.0f}**",
            "End Balance": f"**${total_portfolio_value:,.0f}**",
            "Net Gain": f"**${total_portfolio_value - total_start:,.0f}**"
        })
        
        df_portfolio = pd.DataFrame(portfolio_table_data)
        
        st.dataframe(
            df_portfolio,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Account": st.column_config.TextColumn("Account", width="small"),
                "Start Balance": st.column_config.TextColumn("Start of Year", width="medium"),
                "New Contributions": st.column_config.TextColumn("Contributions", width="medium"),
                "Investment Growth": st.column_config.TextColumn(f"Growth @ {target_cagr*100:.1f}%", width="medium"),
                "End Balance": st.column_config.TextColumn("Projected End", width="medium"),
                "Net Gain": st.column_config.TextColumn("Total Gain", width="medium")
            }
        )
        
        # Quick insights
        col_insight1, col_insight2, col_insight3 = st.columns(3)
        
        with col_insight1:
            growth_rate_actual = ((total_growth / max(1, total_start)) * 100) if total_start > 0 else 0
            st.metric("Portfolio Growth Rate", f"{growth_rate_actual:.2f}%", 
                     help="Actual growth rate on starting balance")
        
        with col_insight2:
            contribution_impact = ((total_contributions / max(1, total_portfolio_value)) * 100)
            st.metric("Contribution Impact", f"{contribution_impact:.1f}%",
                     help="% of end value from new contributions")
        
        with col_insight3:
            investment_impact = ((total_growth / max(1, total_portfolio_value)) * 100)
            st.metric("Investment Impact", f"{investment_impact:.1f}%",
                     help="% of end value from market growth")
    
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
        total_in_bracket = min(total_gross_income, bracket['high']) - bracket['low']
        
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
    penthouse_shield_needed = max(0, total_gross_income - penthouse_threshold - total_rrsp_contributions)
    
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
    
    ac1, ac2, ac3, ac4, ac5 = st.columns(5)
    
    with ac1:
        st.metric(
            "RRSP Optimization",
            f"${rrsp_lump_sum_optimization:,.0f}",
            help="Strategic deposit for tax bracket optimization"
        )
    
    with ac2:
        st.metric(
            "RRSP Additional",
            f"${rrsp_lump_sum_additional:,.0f}",
            help="Extra contributions for maximum refund"
        )
    
    with ac3:
        st.metric(
            "TFSA Deposit",
            f"${tfsa_lump_sum:,.0f}",
            help="Tax-free savings contribution"
        )
    
    with ac4:
        st.metric(
            "Expected Refund",
            f"${estimated_refund:,.0f}",
            delta=f"+{(estimated_refund/max(1,total_rrsp_contributions))*100:.1f}%",
            help="Tax refund from all RRSP contributions"
        )
    
    with ac5:
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
    rrsp_earned_room = min(31560, total_gross_income * 0.18)
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
        employee_contribution = base_salary * (biweekly_pct / 100)
        
        if employee_contribution > 0:
            instant_return_pct = (employer_contribution / employee_contribution) * 100
            insights.append({
                "icon": "🎁",
                "title": "Free Money: Employer Match",
                "message": f"Your employer is contributing ${employer_contribution:,.0f} annually ({employer_match}% match). "
                          f"This represents a **{instant_return_pct:.1f}% instant return** on your ${employee_contribution:,.0f} contribution. "
                          f"Employer matching is the single best investment return available - always maximize it first.",
                "priority": "high"
            })
        else:
            insights.append({
                "icon": "🎁",
                "title": "Free Money: Employer Match Available",
                "message": f"Your employer offers a {employer_match}% match (${employer_contribution:,.0f} potential free money). "
                          f"You're currently not contributing, so you're leaving this free money on the table. "
                          f"Start contributing to claim this benefit.",
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
