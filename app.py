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

st.subheader("User Profile")

age = st.number_input("Age", min_value=1, max_value=120, value=25)
gender = st.selectbox("Gender", ["Male", "Female", "Other"])
lifestyle = st.multiselect(
    "Lifestyle Habits",
    ["Smoker", "Alcohol", "Sedentary (low activity)", "Active (regular exercise)"]
)



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


    st.subheader("Summary Report")

    total_tests = len(df)
    abnormal = df[df["Status"] != "Normal"]

    if len(abnormal) == 0:
        st.success(f"All {total_tests} results are within normal range.")
    else:
        st.warning(f"{len(abnormal)} out of {total_tests} results are abnormal.")


        abnormal_tests = ", ".join(abnormal["Test Name"].tolist())
        st.write(f"**key Issues:** {abnormal_tests}")

        st.info("Recommendation: Please review abnormal results carefully."
                "If multiple issues persist, consult your doctor.")

    # here is the charts
    import plotly.graph_objects as go

    st.subheader("Visual Insights")

    for _, row in df.iterrows():
        test = row["Test Name"]
        value = row["Value"]
        normal_range = row["Normal Range"]

        try:
            if "-" in str(normal_range):
                low, high = map(float, normal_range.split("-"))
            elif "<" in str(normal_range):
                low, high = 0, float(normal_range.replace("<", ""))
            elif ">" in str(normal_range):
                low, high = float(normal_range.replace(">", "")), value+50
            else:
                continue
        except:
            continue

        fig = go.Figure()

        #here is the normal range bar graph
        fig.add_trace(go.Bar(
            x=[test],
            y=[high - low],
            base=[low],
            name="Normal Range",
            marker_color="lightgreen",
            opacity=0.6
        ))

        color = "red" if row["Status"] != "Normal" else "green"
        fig.add_trace(go.Scatter(
            x=[test],
            y=[value],
            mode="markers+text",
            marker=dict(size=12, color=color),
            name="Your Value",
            text=[f"{value} {row['Unit']}"],
            textposition="top center"
        ))

        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=30, b=10),
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Explanations & Recommendations")

    for _, row in df.iterrows():
        test = row["Test Name"]
        status = row["Status"]

        if test in explanations and status in explanations[test]:
            condition, advice = explanations[test][status]

            extra_note = ""
            if test == "Cholesterol" and status == "High" and age > 40:
                extra_note = "Since you are over 40, risk of hear disease is higher."
            if test == "Blood Pressure" and status == "Abnormal" and "Smoker" in lifestyle:
                extra_note = "Smoking with high BP increase stroke risk."
            if test == "Glucose" and status == "High" and "Sedentary (low activity)" in lifestyle:
                extra_note = "Consider daily physical activity to improve glucose control."

            st.markdown(f"""
            **{test} ({status})**  
            -  {condition}  
            -  Recommendation: {advice}
            {extra_note}
            """)


    


