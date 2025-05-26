           
import streamlit as st
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv
import os

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# 🔐 Load API key securely
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set OPENAI_API_KEY in your environment or .env file")

# Initialize ChatOpenAI client
llm = ChatOpenAI(temperature=0, model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)

st.write(f"API Key loaded: {OPENAI_API_KEY[:5]}...{OPENAI_API_KEY[-4:]}")

# 🧠 Setup GPT model


# 🧠 Prompt to judge similarity
prompt = PromptTemplate.from_template("""
You are an AI that compares two transaction comments and returns a similarity percentage from 0 to 100.

Comment 1: "{comment1}"
Comment 2: "{comment2}"

How similar are these two, considering they could be partial payments, future settlements, or recurring transfers?

Respond with only a number from 0 to 100, no extra text or punctuation.
""")
chain = prompt | llm

# 🌐 Streamlit App
st.title("🔍 Transaction Comment Matcher")
st.write("Upload two Excel files and compare `Comment` fields using OpenAI GPT.")

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
                        response = chain.invoke({"comment1": comment1, "comment2": comment2}).strip()
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
