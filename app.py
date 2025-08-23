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
    


# Here is the explanation to show final in text for results
explanations = {
    "Glucose": {
        "High": ("High blood sugar may indicate pre-diabetes or diabetes.",
                 "Limit sugar, exercise 30 mins daily, drink water."),
        "Low": ("Low blood sugar may cause weakness/dizziness.",
                "Eat small frequent meals, include complex carbs.")
    },
    "Hemoglobin": {
        "Low": ("Low hemoglobin may indicate anemia.",
                "Eat iron-rich foods (spinach, beans, red meat)."),
        "High": ("High hemoglobin may be due to dehydration or lung issues.",
                 "Stay hydrated, consult doctor if persistent.")
    },
    "Cholesterol": {
        "High": ("High cholesterol increases heart disease risk.",
                 "Avoid oily food, eat more fruits/veggies, exercise regularly.")
    },
    "Vitamin D": {
        "Low": ("Low Vitamin D may cause weak bones/fatigue.",
                "Spend 15 mins in sunlight daily, take supplements if needed."),
    },
    "Blood Pressure": {
        "Abnormal": ("Abnormal blood pressure may indicate hypertension.",
                     "Reduce salt, exercise, avoid stress, consult doctor.")
    }
}



uploaded_file = st.file_uploader("Upload Lab Report", type=["csv", "xlsx"])

if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df["Status"] = df.apply(lambda row: check_status(row["Value"], row["Normal Range"]), axis=1)

    st.subheader("Uploaded Report with Status")
    st.dataframe(df.style.apply(
        lambda row: ["background-color: lightgreen" if row.Status=="Normal"
                     else "background-color: orange" if row.Status=="Low"
                     else "background-color: red" if row.Status=="High" or row.Status=="Abnormal"
                     else ""
                     for _ in row], axis=1
    ))

    st.subheader("Explanations & Recommendations")

    for _, row in df.iterrows():
        test = row["Test Name"]
        status = row["Status"]

        if test in explanations and status in explanations[test]:
            condition, advice = explanations[test][status]
            st.markdown(f"""
            **{test} ({status})**  
            -  {condition}  
            -  Recommendation: {advice}
            """)


    


