import os
from langchain_openai import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv

# Load env vars from .env file if present
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set OPENAI_API_KEY in your environment or .env file")

# Initialize ChatOpenAI client
# llm = AzureChatOpenAI(temperature=0, model="gpt-4o-mini", openai_api_key=OPENAI_API_KEY)

prompt = PromptTemplate.from_template("""
You are an AI that compares two transaction comments and returns a similarity percentage from 0 to 100.

Comment 1: "{comment1}"
Comment 2: "{comment2}"

How similar are these two, considering they could be partial payments, future settlements, or recurring transfers?

**Respond with only an integer number from 0 to 100, no extra text or punctuation.**
""")

chain = LLMChain(llm=llm, prompt=prompt)

comment1 = "Payment for cloud services for Q1"
comment2 = "Cloud services billing for first quarter"

response = chain.run(comment1=comment1, comment2=comment2).strip()

print(f"Raw GPT response: '{response}'")

try:
    similarity_score = int(''.join(filter(str.isdigit, response)))
    print(f"Parsed similarity score: {similarity_score}")
except Exception as e:
    print(f"Error parsing similarity score: {e}")
