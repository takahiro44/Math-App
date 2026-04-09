from fastapi import APIRouter
from langchain_google_genai import ChatGoogleGenerativeAI
from app.schemas.question import QuestionRequest, QuestionResponse
from app.prompts.question import single_question_prompt, single_parser
import os

router = APIRouter()

@router.post("/generate", response_model=QuestionResponse)
def generate_question(request: QuestionRequest):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    chain = single_question_prompt | llm | single_parser

    result = chain.invoke({
        "grade": request.grade,
        "unit": request.unit,
        "difficulty": request.difficulty
    })

    return result