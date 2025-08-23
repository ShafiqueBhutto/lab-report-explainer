import streamlit as st
import pandas as pd

st.title("Lab Report Explainer Dashboard")

st.write("Upload the Lab report (CSV)/Excel to get started. ")

def check_status(value, normal_range):
    try:
        if "-" in str(normal_range):
            low, high = map(float, normal_range.split("-"))
            value = float(value)
            if value < low:
                return "Low"
            elif value > high:
                return "High"
            else:
                return "Normal"
            
        elif "<" in str(normal_range):
            limit = float(normal_range.replace("<", ''))
            value = float(value)
            return "High" if value >= limit else "Normal"
        elif ">" in str(normal_range):
            limit = float(normal_range.replace(">", ""))
            value = float(value)
            return "Low" if value <= limit else "Normal"
        else:
            return "Normal" if str(value) == str(normal_range) else "Abnormal"
        
    except: 
        return "Unknown"
    


