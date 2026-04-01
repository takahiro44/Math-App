from fastapi import APIRouter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.schemas.question import QuestionRequest, QuestionResponse
import os

router = APIRouter()

@router.post("/generate", response_model=QuestionResponse)
def generate_question(request: QuestionRequest):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    parser = JsonOutputParser(pydantic_object=QuestionResponse)

    prompt = PromptTemplate(
        template="""
あなたは中学校の数学教師です。
以下の条件で数学の問題を1問作成してください。

学年: 中学{grade}年生
単元: {unit}
難易度: {difficulty}

以下のJSON形式で返してください。
{format_instructions}
""",
        input_variables=["grade", "unit", "difficulty"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    chain = prompt | llm | parser

    result = chain.invoke({
        "grade": request.grade,
        "unit": request.unit,
        "difficulty": request.difficulty
    })

    return result