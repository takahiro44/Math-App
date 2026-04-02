from pydantic import BaseModel

class GradingRequest(BaseModel):
    question: str    # 問題文
    correct_answer: str  # 正解
    user_answer: str     # 生徒の回答

class GradingResponse(BaseModel):
    is_correct: bool     # 正誤
    feedback: str        # フィードバックコメント