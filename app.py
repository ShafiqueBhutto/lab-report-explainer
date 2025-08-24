import streamlit as st
import pandas as pd
from pdf2image import convert_from_bytes
from PIL import Image
import pytesseract
import re
import plotly.graph_objects as go
import os
from huggingface_hub import InferenceClient

# If Tesseract is installed at a custom path on Windows, keep this:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# -------------------------
# Hugging Face Inference Client (hosted) — uses your HF_TOKEN
# -------------------------
hf_token = os.getenv("HF_TOKEN")
if not hf_token:
    st.error("Hugging Face token not found. Set environment variable HF_TOKEN and restart the app.")
    st.stop()

client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.2",  # or "mistralai/Mistral-7B-Instruct-v0.3"
    token=hf_token
)

# -------------------------
# Streamlit UI
# -------------------------
st.title("🧪 Lab Report Explainer Dashboard")
st.write("Upload your Lab Report (CSV / Excel / PDF / Image) to get results explained in simple language.")

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

st.subheader("👤 User Profile")
age = st.number_input("Age", min_value=1, max_value=120, value=25)
gender = st.selectbox("Gender", ["Male", "Female", "Other"])
lifestyle = st.multiselect(
    "Lifestyle Habits",
    ["Smoker", "Alcohol", "Sedentary (low activity)", "Active (regular exercise)"]
)

uploaded_file = st.file_uploader("📂 Upload Lab Report", type=["csv", "xlsx", "pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    # CSV
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)

    # Excel
    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)

    # PDF → OCR
    elif uploaded_file.name.endswith(".pdf"):
        images = convert_from_bytes(uploaded_file.read())
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img)

    # Images → OCR
    elif uploaded_file.name.lower().endswith(("png", "jpg", "jpeg")):
        image = Image.open(uploaded_file)
        text = pytesseract.image_to_string(image)

    # Extract structured data if OCR text exists
    if 'text' in locals():
        st.subheader("📄 Extracted Raw Text (First 1000 chars)")
        st.text(text[:1000])

        pattern = r"([A-Za-z ]+)\s+([\d.]+)\s*([a-zA-Z/%]+)?\s*([\d\-<>.]+)?"
        matches = re.findall(pattern, text)

        parsed_data = []
        for m in matches:
            test_name, value, unit, normal_range = m
            if test_name and value:
                parsed_data.append([test_name.strip(), value, unit, normal_range])

        if parsed_data:
            df = pd.DataFrame(parsed_data, columns=["Test Name", "Value", "Unit", "Normal Range"])
        else:
            st.error("⚠️ Could not parse structured test values from scanned file.")

    # Guard: make sure df exists before proceeding
    if 'df' not in locals():
        st.error("No structured data extracted from the uploaded file.")
        st.stop()

    df["Status"] = df.apply(lambda row: check_status(row["Value"], row["Normal Range"]), axis=1)

    # -------------------------
    # AI report via HF InferenceClient (Mistral)
    # -------------------------
    def generate_ai_report(df, age, gender, lifestyle):
        report_summary = df.to_string(index=False)
        user_profile = f"Age: {age}, Gender: {gender}, Lifestyle: {', '.join(lifestyle) if lifestyle else 'None'}"

        messages = [
             {"role": "system", "content": "You are a helpful medical assistant AI."},
             {"role": "user", "content": f"""
              Patient Profile: {user_profile}
              Lab Test Results with Status:
{report_summary}

Tasks:
1) Explain the results in very simple words.
2) Highlight any abnormal findings clearly.
3) Give lifestyle-based recommendations (diet, exercise, habits).
4) Keep the tone friendly and clear. Only say 'consult doctor' if necessary.
"""}
        ]

        try:
            response = client.chat_completion(
                model="mistralai/Mistral-7B-Instruct-v0.2",
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                top_p=0.9
            )
            return response.choices[0].message["content"]
        except Exception as e:
            return f"AI generation failed: {e}"

    st.subheader("📊 Uploaded Report with Status")
    st.dataframe(df.style.apply(
        lambda row: ["background-color: lightgreen" if row.Status == "Normal"
                     else "background-color: orange" if row.Status == "Low"
                     else "background-color: red" if row.Status in ["High", "Abnormal"]
                     else ""
                     for _ in row], axis=1
    ))

    st.subheader("📌 Summary Report")
    total_tests = len(df)
    abnormal = df[df["Status"] != "Normal"]

    if len(abnormal) == 0:
        st.success(f"✅ All {total_tests} results are within normal range.")
    else:
        st.warning(f"⚠️ {len(abnormal)} out of {total_tests} results are abnormal.")
        abnormal_tests = ", ".join(abnormal["Test Name"].tolist())
        st.write(f"**Key Issues:** {abnormal_tests}")

    st.subheader("📉 Visual Insights")
    for _, row in df.iterrows():
        test = row["Test Name"]
        value_str = str(row["Value"]).strip()

        try:
             value = float(value_str)
        except ValueError:
            continue
        normal_range = row["Normal Range"]

        try:
            if "-" in str(normal_range):
                low, high = map(float, normal_range.split("-"))
            elif "<" in str(normal_range):
                low, high = 0, float(normal_range.replace("<", ""))
            elif ">" in str(normal_range):
                low, high = float(normal_range.replace(">", "")), value + 50
            else:
                continue
        except:
            continue

        fig = go.Figure()
        fig.add_trace(go.Bar(x=[test], y=[high - low], base=[low],
                             name="Normal Range", marker_color="lightgreen", opacity=0.6))

        color = "red" if row["Status"] != "Normal" else "green"
        fig.add_trace(go.Scatter(x=[test], y=[value], mode="markers+text",
                                 marker=dict(size=12, color=color),
                                 name="Your Value", text=[f"{value} {row['Unit']}"], textposition="top center"))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📖 Explanations & Recommendations")
    for _, row in df.iterrows():
        test, status = row["Test Name"], row["Status"]

        if test in explanations and status in explanations[test]:
            condition, advice = explanations[test][status]

            extra_note = ""
            if test == "Cholesterol" and status == "High" and age > 40:
                extra_note = "Since you are over 40, heart disease risk is higher."
            if test == "Blood Pressure" and status == "Abnormal" and "Smoker" in lifestyle:
                extra_note = "Smoking with high BP increases stroke risk."
            if test == "Glucose" and status == "High" and "Sedentary (low activity)" in lifestyle:
                extra_note = "Daily physical activity can improve glucose control."

            st.markdown(f"""
            **{test} ({status})**  
            - {condition}  
            - Recommendation: {advice}  
            {extra_note}
            """)

    st.subheader("🤖 AI-Powered Explanation")
    if st.button("Generate AI Report"):
        with st.spinner("Analyzing with AI..."):
            ai_report = generate_ai_report(df, age, gender, lifestyle)
        st.write(ai_report)
