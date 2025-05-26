import streamlit as st
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv
import os
import requests

# 🔐 Load API key and endpoint securely
load_dotenv()
API_URL = os.getenv("AZURE_OPENAI_ENDPOINT")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")

st.write(f"API Key loaded: {API_KEY[:5]}...{API_KEY[-4:]}")
st.write(f"API URL: {API_URL[:40]}...")

def get_similarity_azure(comment1, comment2, api_url, api_key):
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }
    prompt = f"""You are an AI that compares two transaction comments and returns a similarity percentage from 0 to 100.

Comment 1: "{comment1}"
Comment 2: "{comment2}"

How similar are these two, considering they could be partial payments, future settlements, or recurring transfers?

Respond with only a number from 0 to 100, no extra text or punctuation."""
    request_body = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 10,
        "temperature": 0,
    }
    response = requests.post(api_url, headers=headers, json=request_body)
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"].strip()

# 🌐 Streamlit App
st.title("🔍 Transaction Comment Matcher")
st.write("Upload two Excel files and compare `Comment` fields using Azure OpenAI.")

file1 = st.file_uploader("Upload Sheet 1", type=["xlsx"])
file2 = st.file_uploader("Upload Sheet 2", type=["xlsx"])

if file1 and file2:
    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)

    if "Comment" not in df1.columns or "Comment" not in df2.columns:
        st.error("Both sheets must contain a 'Comment' column.")
    else:
        if st.button("🔁 Compare Comments"):
            results = []
            total = len(df1) * len(df2)
            progress = st.progress(0)
            count = 0

            for idx1, row1 in df1.iterrows():
                for idx2, row2 in df2.iterrows():
                    comment1 = str(row1["Comment"])
                    comment2 = str(row2["Comment"])
                
                    try:
                        response = get_similarity_azure(comment1, comment2, API_URL, API_KEY)
                        match_score = int(''.join(filter(str.isdigit, response)))
                    except Exception as e:
                        st.error(f"OpenAI error: {e}")
                        match_score = 0

                    results.append({
                        "Sheet1_ID": idx1,
                        "Sheet2_ID": idx2,
                        "Sheet1_Comment": comment1,
                        "Sheet2_Comment": comment2,
                        "Similarity (%)": match_score,
                        "Flag": "🔴" if match_score < 80 else ""
                    })

                    count += 1
                    progress.progress(count / total)

            result_df = pd.DataFrame(results)
            st.success("✅ Comparison complete!")
            st.dataframe(result_df)

            # 💾 Save to Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                result_df.to_excel(writer, index=False, sheet_name="ComparisonResults")
            st.download_button("📥 Download Results", output.getvalue(), "comparison_results.xlsx")