import streamlit as st

st.set_page_config(page_title="Smoke Test", layout="centered")

st.title("Smoke Test")
st.write("If you can see this, the app is running correctly.")

ticker = st.text_input("Ticker", "AAPL")
st.write(f"You entered: {ticker}")
