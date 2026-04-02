from fastapi import APIRouter
from langchain_google_genai import ChatGoogleGenerativeAI
from app.schemas.grading import GradingRequest, GradingResponse
from app.prompts.grading import grading_prompt, parser
import os
import re

router = APIRouter()

def normalize(text: str) -> str:
    text = text.strip()
    # 全角を半角に変換
    text = text.replace('＋', '+').replace('－', '-').replace('×', '*').replace('÷', '/')
    # スペースを除去
    text = re.sub(r'\s+', '', text)
    return text

@router.post("/grade", response_model=GradingResponse)
def grade_answer(request: GradingRequest):

    # ① 文字列一致で判定
    if normalize(request.user_answer) == normalize(request.correct_answer):
        return GradingResponse(
            is_correct=True,
            feedback="正解です！素晴らしい！"
        )

    # ② 一致しない場合のみLLMで判定
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    chain = grading_prompt | llm | parser

    result = chain.invoke({
        "question": request.question,
        "correct_answer": request.correct_answer,
        "user_answer": request.user_answer
    })

    return result