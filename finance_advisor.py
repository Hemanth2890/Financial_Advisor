import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.0-flash")

def generate_finance_tips(income, rent, food, subs, transport, insurance, investments, goal):
    prompt = f"""
You are a helpful personal finance advisor.

A person earns ₹{income} per month.
They spend:
- ₹{rent} on rent
- ₹{food} on food
- ₹{subs} on subscriptions
- ₹{transport} on transportation
- ₹{insurance} on insurance
- ₹{investments} on investments

Their savings goal is ₹{goal}.

1. Calculate total monthly expenses and potential savings.
2. Estimate how many months to reach the goal.
3. Give 3 personalized, practical money-saving tips.

Respond in a friendly, bullet-pointed format with emojis.
"""
    response = model.generate_content(prompt)
    return response.text
