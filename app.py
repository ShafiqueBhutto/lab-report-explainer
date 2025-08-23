import streamlit as st
import pandas as pd

st.title("Lab Report Explainer Dashboard")

st.write("Upload the Lab report (CSV)/Excel to get started. ")

uploaded_file = st.file_uploader("Upload Lab report", type=["csv", "xlsx"])

if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("Uploaded Report")
    st.dataframe(df)

