from pydantic import BaseModel
from app.schemas.question import QuestionResponse

class PrintRequest(BaseModel):
    grade: int
    unit: str
    difficulty: str
    num_questions: int

class PrintResponse(BaseModel):
    questions: list[QuestionResponse]