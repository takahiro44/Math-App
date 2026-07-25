"""事前計算した埋め込みに対する numpy ベースの意味検索。

インデックスは scripts/build_index.py が生成する data/ 配下の2ファイル。
永続ディスクを必要としないため、コンテナはステートレスに保てる。

任意のクエリ文字列で上位k件を引けるインターフェースを維持しているので、
将来「講師の自由記述が指定学年の範囲を超えていないか検証する」といった
用途にもそのまま使える。
"""

import json
import logging
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "models/gemini-embedding-001"

DATA_DIR = Path(__file__).parent / "data"
VECTORS_PATH = DATA_DIR / "guidelines_vectors.npz"
CHUNKS_PATH = DATA_DIR / "guidelines_chunks.json"


def _load_index() -> tuple[np.ndarray, list[dict]]:
    """インデックスを読み込む。欠損していても import は落とさず空で縮退する。"""
    try:
        with np.load(VECTORS_PATH) as npz:
            vectors = npz["vectors"]
        with CHUNKS_PATH.open(encoding="utf-8") as f:
            payload = json.load(f)
        chunks = payload["chunks"]
    except (OSError, KeyError, ValueError) as e:
        logger.error(
            "RAGインデックスを読み込めませんでした (%s: %s)。"
            "context なしで生成を続行します。scripts/build_index.py を実行してください。",
            type(e).__name__,
            e,
        )
        return np.zeros((0, 0), dtype=np.float32), []

    if len(vectors) != len(chunks):
        logger.error(
            "インデックスの件数が不一致です (vectors=%d, chunks=%d)。RAGを無効化します。",
            len(vectors),
            len(chunks),
        )
        return np.zeros((0, 0), dtype=np.float32), []

    logger.info(
        "RAGインデックスを読み込みました: %d チャンク, %d 次元",
        len(chunks),
        vectors.shape[1],
    )
    return vectors, chunks


# モジュールロード時に一度だけ読み込む（リクエストごとの再読み込みを避ける）
_VECTORS, _CHUNKS = _load_index()


@lru_cache(maxsize=1)
def _get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """embeddings クライアントも一度だけ生成する。"""
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


@lru_cache(maxsize=512)
def _embed_query(query: str) -> tuple[float, ...]:
    """クエリを埋め込んで L2 正規化する。

    現状のクエリは「中学{grade}年生 {unit}」で組み合わせが有限なので、
    実質すべてキャッシュヒットして API 呼び出しはゼロになる。
    失敗時は例外を投げる（lru_cache は例外をキャッシュしないので、
    一時的な API エラーが恒久的に焼き付くことはない）。
    """
    vector = np.asarray(_get_embeddings().embed_query(query), dtype=np.float32)
    norm = float(np.linalg.norm(vector))
    if norm == 0:
        raise ValueError("クエリの埋め込みがゼロベクトルです")
    return tuple((vector / norm).tolist())


def retrieve(query: str, k: int = 3) -> list[str]:
    """クエリに意味的に近いチャンク本文を上位k件返す。

    インデックス欠損や埋め込みAPIの失敗時は例外を投げず空リストを返す。
    呼び出し側は context なしで生成を続行できる。
    """
    if len(_CHUNKS) == 0:
        return []

    try:
        query_vector = np.asarray(_embed_query(query), dtype=np.float32)
    except Exception as e:
        logger.warning(
            "クエリの埋め込みに失敗しました (%s: %s)。context なしで続行します。query=%r",
            type(e).__name__,
            e,
            query,
        )
        return []

    if query_vector.shape[0] != _VECTORS.shape[1]:
        logger.error(
            "クエリの次元がインデックスと一致しません (query=%d, index=%d)。"
            "build_index.py と同じ埋め込みモデルか確認してください。",
            query_vector.shape[0],
            _VECTORS.shape[1],
        )
        return []

    # 両辺 L2 正規化済みなので内積がそのままコサイン類似度になる
    scores = _VECTORS @ query_vector

    k = min(k, len(scores))
    # 上位k件だけ必要なので全体ソートはしない
    top = np.argpartition(-scores, k - 1)[:k]
    top = top[np.argsort(-scores[top])]

    for rank, i in enumerate(top, start=1):
        chunk = _CHUNKS[i]
        logger.info(
            "[RAG] query=%r rank=%d score=%.4f page=%s text=%s",
            query,
            rank,
            float(scores[i]),
            chunk.get("page"),
            chunk["text"][:120].replace("\n", " "),
        )

    return [_CHUNKS[i]["text"] for i in top]
