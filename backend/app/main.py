from fastapi import FastAPI
from app.routers import question

app = FastAPI()

app.include_router(question.router, prefix="/question", tags=["question"])

@app.get("/health")
def health():
    return {"status": "ok"}{
      "grade": 0,
      "unit": "string",
      "difficulty": "string"
    }