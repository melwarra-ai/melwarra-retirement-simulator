import streamlit as st
import pandas as pd

# --- APP CONFIG ---
st.set_page_config(page_title="Retirement Architect Pro", layout="wide")
st.title("🏛️ Retirement Architect: Path to Age 55")
st.markdown("Optimize your income to avoid the 'Penthouse' tax brackets.")

# --- SIDEBAR: USER PROFILE ---
with st.sidebar:
    st.header("👤 Income & Goals")
    gross_income = st.number_input("Total Gross (Salary + Bonus) ($)", value=200000, step=5000)
    base_salary = st.number_input("Annual Base Salary ($)", value=180000, step=5000)
    
    st.header("💰 RRSP & TFSA")
    biweekly_pct = st.slider("Biweekly Contribution (% of Base)", 0.0, 18.0, 6.0)
    employer_match = st.slider("Employer Match (% of Base)", 0.0, 10.0, 4.0)
    rrsp_room = st.number_input("Unused RRSP Room ($)", value=146000)
    tfsa_room = st.number_input("Unused TFSA Room ($)", value=102000)

# --- OFFICIAL 2026 COMBINED ON/FED TAX RATES ---
# Using the 14% Federal base + Indexed Ontario thresholds
BRACKETS = [
    {"name": "Floor 1", "top": 53891, "rate": 0.1905},
    {"name": "Floor 2", "top": 58523, "rate": 0.2315},
    {"name": "Floor 3", "top": 94907, "rate": 0.2965},
    {"name": "Floor 4", "top": 117045, "rate": 0.3148},
    {"name": "Floor 5", "top": 181440, "rate": 0.4497}, # The Efficiency Cliff
    {"name": "Penthouse", "top": 258482, "rate": 0.4829},
    {"name": "Skyline", "top": 1000000, "rate": 0.5353}
]

# --- CALCULATIONS ---
annual_rrsp_periodic = base_salary * ((biweekly_pct + employer_match) / 100)
taxable_income = gross_income - annual_rrsp_periodic
tax_cliff = 181440 # Income above this is taxed at 48.3%+

# --- FEATURE 1: COLOR-CODED TAX BUILDING ---
st.header("🏢 The Tax Building Visualizer")
st.write("Each bar is a tax bracket. **Blue** is income you've successfully shielded. **Green** is income still being taxed.")

building_data = []
prev_top = 0
for b in BRACKETS:
    slice_amt = min(gross_income, b['top']) - prev_top
    if slice_amt <= 0: break
    
    # Shielding Logic: Income is reduced from the top floor down
    # If the bottom of this slice is above our taxable income, it's shielded
    is_shielded = (prev_top >= taxable_income)
    status = "Shielded (0% Tax)" if is_shielded else f"Taxed at {b['rate']*100:.1f}%"
    
    building_data.append({"Floor": b['name'], "Amount": slice_amt, "Status": status})
    prev_top = b['top']

df_building = pd.DataFrame(building_data)
st.bar_chart(
    df_building, 
    x="Floor", 
    y="Amount", 
    color="Status", 
    # Hardcoded color mapping for reliability
    color_map={"Shielded (0% Tax)": "#3b82f6"} 
)

# --- FEATURE 2: MARCH 2nd DEADLINE TOOLKIT ---
st.divider()
st.header("📅 Tax Deadline: March 2nd")
premium_lump_sum = max(0, taxable_income - tax_cliff)
actual_lump = min(premium_lump_sum, rrsp_room)
tax_refund = actual_lump * 0.4829

c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Income in 'Penthouse'", f"${premium_lump_sum:,.0f}")
    st.caption("Taxed at 48.3%—Your target for reduction.")
with c2:
    st.metric("Recommended Lump Sum", f"${actual_lump:,.0f}")
    st.caption("Contribute this to maximize efficiency.")
with c3:
    st.success(f"Est. Tax Refund: ${tax_refund:,.0f}")
    st.caption("Strategy: Move this refund directly to TFSA.")

# --- FEATURE 3: THE RETIREMENT BRIDGE (AGE 55) ---
st.divider()
st.subheader("🌉 The Retirement Bridge Strategy")
st.write("To retire at 55, you need to live off **TFSA (Tax-Free)** until age 65 to avoid the OAS Clawback.")

# Simple visualization of retirement income sources
bridge_data = pd.DataFrame({
    "Source": ["TFSA (Tax-Free Bridge)", "RRSP (Taxable Floor)", "OAS/CPP (Government)"],
    "Role": ["Age 55 to 65", "Age 65+", "Age 65+"],
    "Priority": [100, 70, 40]
})
st.bar_chart(bridge_data, x="Source", y="Priority", color="Role")

st.info(f"""
**Strategic Roadmap:**
1. **Bonus Shield:** Your $20k bonus is currently taxed at ~48%. Use the **T1213 Form** to transfer it directly to RRSP tax-free.
2. **The RRSP Floor:** Stop RRSP contributions once taxable income hits **${tax_cliff:,.0f}**.
3. **TFSA Pivot:** Any savings beyond the floor should go to TFSA to build your 'Age 55 Bridge'.
""")
