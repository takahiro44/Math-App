"""ChromaDB 版 retriever の検索結果をベースラインとして保存する（一度だけ実行）。

numpy 実装へのリファクタが検索品質を落としていないかを比較検証するための
スナップショット。ChromaDB は実行時依存から外したので、このスクリプトは
レガシー依存を一時的に入れて実行する:

    uv run --with 'chromadb==1.5.7' --with 'langchain-community==0.4.1' \
        python scripts/capture_baseline.py

出力: tests/fixtures/retrieval_baseline.json（本文とスコアの両方を含む）
"""

import argparse
import json
import os
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

EMBEDDING_MODEL = "models/gemini-embedding-001"
TOP_K = 3

# frontend/src/mathUnits.ts の写し。ベースライン取得は一度だけなので同期は不要。
MATH_UNITS: dict[str, list[str]] = {
    "1": ["正負の数", "文字と式", "方程式"],
    "2": ["式の計算", "連立方程式"],
    "3": ["式の展開", "因数分解", "平方根", "二次方程式"],
}

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "retrieval_baseline.json"

# コンテナ内 (/app/rag/vectorstore) とホスト (<repo>/rag/vectorstore) の両対応
VECTORSTORE_CANDIDATES = [
    Path(__file__).resolve().parent.parent / "rag" / "vectorstore",
    Path(__file__).resolve().parents[2] / "rag" / "vectorstore",
]


def find_vectorstore() -> Path:
    for candidate in VECTORSTORE_CANDIDATES:
        if (candidate / "chroma.sqlite3").exists():
            return candidate
    searched = "\n".join(f"  - {c}" for c in VECTORSTORE_CANDIDATES)
    raise SystemExit(f"Chroma vectorstore が見つかりません。\n探索したパス:\n{searched}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vectorstore", type=Path, default=None)
    args = parser.parse_args()

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("GOOGLE_API_KEY が設定されていません。")

    vectorstore_path = args.vectorstore or find_vectorstore()
    print(f"vectorstore: {vectorstore_path}")

    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL, google_api_key=api_key)
    vectorstore = Chroma(
        persist_directory=str(vectorstore_path),
        embedding_function=embeddings,
    )
    print(f"収録件数: {vectorstore._collection.count()}")

    queries = []
    for grade, units in MATH_UNITS.items():
        for unit in units:
            queries.append({"grade": grade, "unit": unit, "query": f"中学{grade}年生 {unit}"})

    results = []
    for item in queries:
        # スコアも欲しいので as_retriever ではなく similarity_search_with_score を使う。
        # 検索対象・k は本番の retriever と同じ。
        hits = vectorstore.similarity_search_with_score(item["query"], k=TOP_K)
        results.append(
            {
                **item,
                "hits": [
                    {
                        "rank": rank,
                        "score": float(score),
                        "page": doc.metadata.get("page"),
                        "text": doc.page_content,
                    }
                    for rank, (doc, score) in enumerate(hits, start=1)
                ],
            }
        )
        print(f"  {item['query']}: {len(hits)}件")

    payload = {
        "captured_with": "chromadb==1.5.7 langchain-community==0.4.1",
        "embedding_model": EMBEDDING_MODEL,
        "top_k": TOP_K,
        "score_semantics": "Chroma の similarity_search_with_score が返す距離（小さいほど近い）",
        "collection_count": vectorstore._collection.count(),
        "queries": results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"書き出しました: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
