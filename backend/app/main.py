from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import question, grading

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(question.router, prefix="/question", tags=["question"])
app.include_router(grading.router, prefix="/grading", tags=["grading"])

@app.get("/health")
def health():
    return {"status": "ok"}