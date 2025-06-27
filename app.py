import streamlit as st
from finance_advisor import generate_finance_tips
st.set_page_config(page_title="💸 Personal Finance Tip Generator", page_icon="💰", layout="centered")
st.markdown("""
    <style>
    .main {
        background-color: #f9f9fb;
    }
    .stButton>button {
        background-color: #5c7cfa;
        color: white;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: bold;
        font-size: 16px;
    }
    .stButton>button:hover {
        background-color: #4a68d1;
    }
    .result-box {
        background-color: #f2f2f2; 
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid #ddd;
        font-size: 17px;
        line-height: 1.6;
        color: #111111;  /* dark text */
    }
    </style>
""", unsafe_allow_html=True)
st.title("💸 Personal Finance Tip Generator")
st.caption("Get personalized, AI-generated budgeting advice to reach your savings goals.")

col1, col2 = st.columns(2)

with col1:
    income = st.number_input("💰 Monthly Income", min_value=0, step=1000)
    rent = st.number_input("🏠 Rent & Utilities", min_value=0, step=500)
    food = st.number_input("🥗 Food & Groceries", min_value=0, step=500)
    subs = st.number_input("📺 Subscriptions", min_value=0, step=100)

with col2:
    transport = st.number_input("🚗 Transportation", min_value=0, step=500)
    insurance = st.number_input("🛡️ Insurance", min_value=0, step=500)
    investments = st.number_input("📈 Investments", min_value=0, step=500)
    goal = st.number_input("🎯 Savings Goal", min_value=0, step=1000)

st.markdown("---")


if st.button("✨ Generate My Tips"):
    with st.spinner("Crunching the numbers..."):
        tips = generate_finance_tips(
            income, rent, food, subs, transport, insurance, investments, goal
        )
        st.markdown("### 📊 Your Personalized Advice")
        st.markdown(f"<div class='result-box'>{tips}</div>", unsafe_allow_html=True)
