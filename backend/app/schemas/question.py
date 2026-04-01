from pydantic import BaseModel

class QuestionRequest(BaseModel):
    grade: int        # 学年（1〜3）
    unit: str         # 単元名（例：一次関数）
    difficulty: str   # 難易度（easy / normal / hard）

class QuestionResponse(BaseModel):
    question: str     # 問題文
    answer: str       # 解答
    explanation: str  # 解説
    hint: str         # ヒント