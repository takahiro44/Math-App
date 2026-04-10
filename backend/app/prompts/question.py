from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from typing import List
from app.schemas.question import QuestionResponse

class QuestionItem(BaseModel):
    question: str
    answer: str
    explanation: str
    hint: str

class QuestionsResponse(BaseModel):
    questions: List[QuestionItem]

parser = JsonOutputParser(pydantic_object=QuestionsResponse)

question_prompt = PromptTemplate(
    template="""
あなたは中学校の数学教師です。
以下の条件で数学の計算問題を{num_questions}問作成してください。

学年: 中学{grade}年生
単元: {unit}
難易度: {difficulty}

【学習指導要領の参考情報】
{context}

【重要な制約】
- 上記の学習指導要領の内容に沿った問題を出題してください
- 計算で解ける問題のみ出題してください
- 図形の描写やグラフの読み取りを必要とする問題は出題しないでください
- 文章題の場合も、計算で解けるものに限定してください
- 問題同士が似たパターンにならないようにバリエーションを持たせてください

以下のJSON形式で返してください。
{format_instructions}
""",
    input_variables=["grade", "unit", "difficulty", "num_questions", "context"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)

single_parser = JsonOutputParser(pydantic_object=QuestionResponse)

single_question_prompt = PromptTemplate(
    template="""
あなたは中学校の数学教師です。
以下の条件で数学の計算問題を1問作成してください。

学年: 中学{grade}年生
単元: {unit}
難易度: {difficulty}

【学習指導要領の参考情報】
{context}

【重要な制約】
- 上記の学習指導要領の内容に沿った問題を出題してください
- 計算で解ける問題のみ出題してください
- 図形の描写やグラフの読み取りを必要とする問題は出題しないでください
- 文章題の場合も、計算で解けるものに限定してください

以下のJSON形式で返してください。
{format_instructions}
""",
    input_variables=["grade", "unit", "difficulty", "context"],
    partial_variables={"format_instructions": single_parser.get_format_instructions()}
)