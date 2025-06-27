import streamlit as st
from finance_advisor import generate_finance_tips

st.set_page_config(page_title="💸 Personal Finance Tip Generator")

st.title("💸 Personal Finance Tip Generator")
st.write("Get practical, AI-generated advice on how to save more money!")

# Input fields
income = st.number_input("Monthly Income (₹)", min_value=0)
rent = st.number_input("Housing (₹)", min_value=0)
food = st.number_input("Food & Groceries (₹)", min_value=0)
subs = st.number_input("Subscriptions (₹)", min_value=0)
transport = st.number_input("Transportation (₹)", min_value=0)
insurance = st.number_input("Insurance (₹)", min_value=0)
investments = st.number_input("Investments (₹)", min_value=0)
goal = st.number_input("Savings Goal (₹)", min_value=0)

# Generate button
if st.button("Generate Tips"):
    with st.spinner("Analyzing your finances..."):
        tips = generate_finance_tips(income, rent, food, subs, goal)
        st.subheader("📊 Your Personalized Financial Advice")
        st.write(tips)
