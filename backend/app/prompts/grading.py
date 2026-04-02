from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.schemas.grading import GradingResponse

parser = JsonOutputParser(pydantic_object=GradingResponse)

grading_prompt = PromptTemplate(
    template="""
あなたは中学校の数学教師です。
生徒の回答を採点してください。

問題: {question}
正解: {correct_answer}
生徒の回答: {user_answer}

【採点のルール】
- 数式の表記が多少違っても、意味が正しければ正解としてください
- 例：「3x+1」と「3x＋1」は同じ正解とする
- is_correctにtrue/falseで正誤を返してください
- feedbackには生徒への一言コメントを日本語で返してください
  - 正解の場合：褒めるコメント
  - 不正解の場合：どこが違うかを優しく説明するコメント

以下のJSON形式で返してください。
{format_instructions}
""",
    input_variables=["question", "correct_answer", "user_answer"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)