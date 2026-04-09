from fastapi import APIRouter
from langchain_google_genai import ChatGoogleGenerativeAI
from app.schemas.print import PrintRequest, PrintResponse
from app.prompts.question import question_prompt, parser
import os

router = APIRouter()

@router.post("/generate", response_model=PrintResponse)
def generate_print(request: PrintRequest):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    chain = question_prompt | llm | parser

    result = chain.invoke({
        "grade": request.grade,
        "unit": request.unit,
        "difficulty": request.difficulty,
        "num_questions": request.num_questions,
    })

    return PrintResponse(questions=result["questions"])