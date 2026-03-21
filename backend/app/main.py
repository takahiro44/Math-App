from fastapi import FastAPI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
import os

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/test-llm")
def test_llm():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    response = llm.invoke([HumanMessage(content="こんにちは！一言で自己紹介してください。")])
    return {"response": response.content}