
import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv(override=True)

model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

print(f"Connecting to {model_name}...", flush=True)

llm = ChatGoogleGenerativeAI(
    model=model_name,
    temperature=0.2,
    max_retries=0,
    timeout=20,
)

try:
    start = time.monotonic()

    response = llm.invoke(
        "Explain what an ETF is in one sentence."
    )

    print("Response:", response.content)
    print(f"Time: {time.monotonic() - start:.2f}s")

except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
