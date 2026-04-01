from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.schemas.question import QuestionResponse

parser = JsonOutputParser(pydantic_object=QuestionResponse)

question_prompt = PromptTemplate(
    template="""
あなたは中学校の数学教師です。
以下の条件で数学の計算問題を1問作成してください。

学年: 中学{grade}年生
単元: {unit}
難易度: {difficulty}

【重要な制約】
- 計算で解ける問題のみ出題してください
- 図形の描写やグラフの読み取りを必要とする問題は出題しないでください
- 文章題の場合も、計算で解けるものに限定してください

以下のJSON形式で返してください。
{format_instructions}
""",
    input_variables=["grade", "unit", "difficulty"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)