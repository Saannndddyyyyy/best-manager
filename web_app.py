import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Best Manager Simulation", layout="wide", page_icon="📊")

# Custom CSS for "Premium" feel
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        height: 3em;
        font-weight: bold;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- DATA CONSTANTS ---
VENUES = {
    'Grand Hall': {'Capacity': 500, 'Fixed Cost': 5000, 'Vibe': 8},
    'Tech Hub': {'Capacity': 1000, 'Fixed Cost': 12000, 'Vibe': 6},
    'City Center': {'Capacity': 2000, 'Fixed Cost': 25000, 'Vibe': 9},
    'Open Grounds': {'Capacity': 5000, 'Fixed Cost': 40000, 'Vibe': 7}
}

CATERING = {
    'Basic Snacks': {'Cost': 15, 'Quality': 2},
    'Standard Buffet': {'Cost': 35, 'Quality': 6},
    'Premium Gourmet': {'Cost': 60, 'Quality': 9}
}

STAFFING = {
    'Skeleton Crew': {'Ratio': 1, 'CostPer': 200},
    'Standard': {'Ratio': 2, 'CostPer': 250},
    'Premium Service': {'Ratio': 4, 'CostPer': 300}
}

RISKS = {
    'None (Normal)': {'DemandMult': 1.0, 'SatPenalty': 0},
    'Heavy Rain': {'DemandMult': 0.7, 'SatPenalty': -10},
    'Competitor Event': {'DemandMult': 0.6, 'SatPenalty': 0},
    'Viral Buzz': {'DemandMult': 1.5, 'SatPenalty': 5}
}

# --- HELPER FUNCTIONS ---
def run_simulation(inputs):
    # Unpack
    venue = VENUES[inputs['Venue']]
    cat = CATERING[inputs['Catering']]
    staff = STAFFING[inputs['Staffing']]
    risk = RISKS[inputs['Risk']]
    
    price = inputs['Price']
    marketing = inputs['Marketing']
    
    # 1. Demand
    # Base Model: 2000 - 3.5*Price + 0.04*Marketing + 10*sqrt(Marketing)
    base_demand = max(0, 2000 - 3.5 * price + 0.04 * marketing + 10 * np.sqrt(marketing))
    
    # Risk adjustment
    risk_demand = base_demand * risk['DemandMult']
    
    # Capacity constraint
    attendance = min(risk_demand, venue['Capacity'])
    attendance = int(attendance)
    
    # 2. Financials
    revenue = attendance * price
    
    venue_cost = venue['Fixed Cost']
    marketing_cost = marketing
    catering_cost = attendance * cat['Cost']
    
    num_staff = np.ceil((attendance / 100) * staff['Ratio'])
    staff_cost = num_staff * staff['CostPer']
    
    total_cost = venue_cost + marketing_cost + catering_cost + staff_cost
    profit = revenue - total_cost
    
    # 3. Satisfaction
    crowding = attendance / venue['Capacity'] if venue['Capacity'] > 0 else 0
    crowding_penalty = 15 if crowding > 0.9 else 0
    
    sat_score = (venue['Vibe'] * 3.3) + (cat['Quality'] * 3.3) + (staff['Ratio'] * 8)
    sat_score -= crowding_penalty
    sat_score += risk['SatPenalty']
    sat_score = min(100, max(0, sat_score))
    
    # 4. Final Score
    # Scaling: Target Profit 200k = 50 pts
    score = (max(0, profit) / 200000 * 50) + (sat_score * 0.5)
    
    return {
        'Attendance': attendance,
        'Revenue': revenue,
        'Total Cost': total_cost,
        'Profit': profit,
        'Satisfaction': sat_score,
        'Score': score,
        'Crowding': crowding * 100,
        'Details': {
            'Venue Cost': venue_cost,
            'Marketing Cost': marketing_cost,
            'Catering Cost': catering_cost,
            'Staff Cost': staff_cost
        }
    }

def generate_excel_download(inputs, results, team_name):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Sheet 1: Summary
        summary_data = {
            'Metric': ['Team Name', 'Success Score', 'Net Profit', 'Satisfaction', 'Attendance', 'Total Revenue', 'Total Cost'],
            'Value': [team_name, results['Score'], results['Profit'], results['Satisfaction'], results['Attendance'], results['Revenue'], results['Total Cost']]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        # Sheet 2: Decisions
        decision_data = {'Decision Variable': list(inputs.keys()), 'Selected Option': list(inputs.values())}
        pd.DataFrame(decision_data).to_excel(writer, sheet_name='Decisions', index=False)
        
        # Sheet 3: Cost Breakdown
        cost_data = {'Category': list(results['Details'].keys()), 'Amount': list(results['Details'].values())}
        pd.DataFrame(cost_data).to_excel(writer, sheet_name='Cost Breakdown', index=False)
        
    return output.getvalue()

# --- SIDEBAR (INPUTS) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2910/2910793.png", width=100)
    st.title("Command Center")
    
    team_name = st.text_input("Team Name", "Team Alpha")
    
    st.markdown("### 1. Operations")
    venue = st.selectbox("Venue", list(VENUES.keys()), index=2)
    catering = st.selectbox("Catering", list(CATERING.keys()), index=1)
    staffing = st.selectbox("Service Level", list(STAFFING.keys()), index=1)
    
    st.markdown("### 2. Marketing & Price")
    price = st.slider("Ticket Price ($)", 50, 500, 250, 10)
    marketing = st.number_input("Marketing Budget ($)", 0, 100000, 20000, 1000)
    
    st.markdown("### 3. External Factors")
    risk = st.selectbox("Risk Scenario", list(RISKS.keys()), index=0)
    
    inputs = {
        'Venue': venue, 'Catering': catering, 'Staffing': staffing,
        'Price': price, 'Marketing': marketing, 'Risk': risk
    }

# --- MAIN PAGE ---
st.title("🏆 Best Manager Simulation: The Grand Tech Summit")
st.markdown("Welcome, **Event Manager**. Analyze, Plan, and Execute to win the title.")

# Run Simulation Live
results = run_simulation(inputs)

# Tabs
tab1, tab2, tab3 = st.tabs(["🚀 Live Dashboard", "📊 Market Analytics", "📜 Mission Briefing"])

with tab1:
    # Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Attendance", f"{results['Attendance']:,}", delta=f"{results['Crowding']:.1f}% Full")
    col2.metric("Revenue", f"${results['Revenue']:,.0f}")
    col3.metric("Net Profit", f"${results['Profit']:,.0f}", delta_color="normal" if results['Profit']>0 else "inverse")
    col4.metric("Success Score", f"{results['Score']:.1f}/100")
    
    # Charts
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Financial Snapshot")
        # Waterfall or Bar chart
        df_fin = pd.DataFrame({
            'Category': ['Revenue', 'Venue', 'Marketing', 'Catering', 'Staffing', 'NET PROFIT'],
            'Amount': [
                results['Revenue'], 
                -results['Details']['Venue Cost'], 
                -results['Details']['Marketing Cost'], 
                -results['Details']['Catering Cost'], 
                -results['Details']['Staff Cost'], 
                results['Profit']
            ],
            'Type': ['Income', 'Expense', 'Expense', 'Expense', 'Expense', 'Total']
        })
        fig_fin = go.Figure(go.Waterfall(
            name = "Finance", orientation = "v",
            measure = ["relative", "relative", "relative", "relative", "relative", "total"],
            x = df_fin['Category'],
            textposition = "outside",
            text = df_fin['Amount']/1000,
            y = df_fin['Amount'],
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ))
        st.plotly_chart(fig_fin, use_container_width=True)

    with c2:
        st.subheader("Satisfaction Components")
        # Radar Chart or Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = results['Satisfaction'],
            title = {'text': "Customer Satisfaction"},
            gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "darkblue"}}
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)
        
    # SUBMISSION AREA
    st.markdown("---")
    st.subheader("📤 Submit Your Strategy")
    st.info("Once you are confident in your strategy, click below to generate your submission file.")
    
    excel_data = generate_excel_download(inputs, results, team_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    file_name = f"{team_name}_Submission_{timestamp}.xlsx"
    
    st.download_button(
        label="📥 Download Submission File (.xlsx)",
        data=excel_data,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

with tab2:
    st.header("Historical Market Data")
    st.markdown("Use this data to estimate the optimal **Price** and **Marketing Budget**.")
    
    # Generate static history for visualization
    np.random.seed(42)
    hist_prices = np.random.uniform(100, 500, 50)
    hist_marketing = np.random.uniform(5000, 50000, 50)
    hist_demand = 2000 - 3.5 * hist_prices + 0.04 * hist_marketing + np.random.normal(0, 50, 50)
    
    df_hist = pd.DataFrame({'Price': hist_prices, 'Marketing': hist_marketing, 'Attendance': hist_demand})
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        fig_p = px.scatter(df_hist, x='Price', y='Attendance', title="Price Sensitivity Analysis")
        st.plotly_chart(fig_p, use_container_width=True)
        
    with col_b:
        fig_m = px.scatter(df_hist, x='Marketing', y='Attendance', title="Marketing ROI Analysis")
        st.plotly_chart(fig_m, use_container_width=True)

with tab3:
    st.header("The Mission")
    st.markdown("""
    **Scenario**: You are the Event Manager for the annual **Tech Summit**.
    
    **Goal**: Maximize the **Event Success Score**.
    - Profit is important (50% weight).
    - But Attendee Satisfaction is crucial (50% weight).
    
    **Relationships**:
    - **Higher Price** → Lower Attendance.
    - **Higher Marketing** → Higher Awareness/Attendance (diminishing returns).
    - **Venue Capacity** → Hard limit on attendance.
    - **Staffing & Catering** → Drive Satisfaction (but increase costs).
    
    **Warning**:
    - If you overfill a venue, crowding penalties apply!
    - External risks (like rain) can ruin a good plan if not anticipated.
    """)
