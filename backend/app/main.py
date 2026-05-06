import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import question, grading, print as print_router

app = FastAPI()

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(question.router, prefix="/question", tags=["question"])
app.include_router(grading.router, prefix="/grading", tags=["grading"])
app.include_router(print_router.router, prefix="/print", tags=["print"])

@app.get("/health")
def health():
    return {"status": "ok"}