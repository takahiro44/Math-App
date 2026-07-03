from fastapi import APIRouter
from langchain_google_genai import ChatGoogleGenerativeAI
from app.schemas.print import PrintRequest, PrintResponse
from app.prompts.question import question_prompt, parser, get_difficulty_guideline
from app.rag.retriever import get_retriever
import os

# ===== [PERF] instrumentation start (計測専用・削除可) =====
import time
import logging
import sys

# uvicorn のログ設定に依存せず docker compose logs (stdout) に確実に出すための専用ロガー
perf_logger = logging.getLogger("perf")
if not perf_logger.handlers:
    _perf_handler = logging.StreamHandler(sys.stdout)
    _perf_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    perf_logger.addHandler(_perf_handler)
    perf_logger.setLevel(logging.INFO)
    perf_logger.propagate = False
# ===== [PERF] instrumentation end =====

router = APIRouter()

@router.post("/generate", response_model=PrintResponse)
def generate_print(request: PrintRequest):
    # ===== [PERF] endpoint 全体の開始時刻 =====
    _t_endpoint_start = time.perf_counter()

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    # ===== [PERF] RAG: retriever 構築 + 検索 (リクエストごとに1回) =====
    _t_build_start = time.perf_counter()
    retriever = get_retriever()
    _t_build_end = time.perf_counter()

    _t_search_start = time.perf_counter()
    docs = retriever.invoke(f"中学{request.grade}年生 {request.unit}")
    _t_search_end = time.perf_counter()

    _retriever_build_s = _t_build_end - _t_build_start
    _rag_search_s = _t_search_end - _t_search_start
    _search_total_s = _retriever_build_s + _rag_search_s
    perf_logger.info("[PERF] retriever_build took %.3fs", _retriever_build_s)
    perf_logger.info(
        "[PERF] rag_search took %.3fs (calls=1, docs=%d)",
        _rag_search_s, len(docs),
    )
    # ===== [PERF] RAG 計測ここまで =====

    context = "\n".join([doc.page_content for doc in docs])

    chain = question_prompt | llm | parser

    # ===== [PERF] LLM 生成: このエンドポイントでは全 num_questions 問を 1 回で生成 =====
    _t_llm_start = time.perf_counter()
    result = chain.invoke({
        "grade": request.grade,
        "unit": request.unit,
        "difficulty": request.difficulty,
        "difficulty_guideline": get_difficulty_guideline(request.difficulty),
        "num_questions": request.num_questions,
        "context": context
    })
    _t_llm_end = time.perf_counter()

    _llm_invoke_s = _t_llm_end - _t_llm_start
    _llm_total_s = _llm_invoke_s  # 呼び出しは 1 回のみ（Python ループなし）
    perf_logger.info(
        "[PERF] llm_invoke #%d took %.3fs (num_questions=%d)",
        0, _llm_invoke_s, request.num_questions,
    )
    perf_logger.info("[PERF] llm_total took %.3fs (invokes=1)", _llm_total_s)
    # ===== [PERF] LLM 計測ここまで =====

    print(result)

    # ===== [PERF] endpoint 全体 + 内訳の集計 =====
    _t_endpoint_end = time.perf_counter()
    _endpoint_total_s = _t_endpoint_end - _t_endpoint_start
    _other_overhead_s = _endpoint_total_s - _llm_total_s - _search_total_s
    perf_logger.info("[PERF] endpoint_total took %.3fs", _endpoint_total_s)
    perf_logger.info(
        "[PERF] breakdown: llm=%.3fs search=%.3fs other=%.3fs "
        "(other = total - llm - search)",
        _llm_total_s, _search_total_s, _other_overhead_s,
    )
    # ===== [PERF] 集計ここまで =====

    return PrintResponse(questions=result["questions"])