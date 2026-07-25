"""学習指導要領PDFから検索インデックスを構築する（開発時のみ実行）。

出力は app/rag/data/ の2ファイル。実行時（retriever.py）はこの2ファイルだけを
読むので、pypdf / text-splitter / ベクトルDB は実行時依存に入らない。

    uv run --group build python scripts/build_index.py

埋め込みは構築時に L2 正規化して保存する。検索時はクエリベクトルを正規化して
行列積を取るだけでコサイン類似度になる。
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

EMBEDDING_MODEL = "models/gemini-embedding-001"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# 無料枠には RPM / TPM 制限があるため、バッチは控えめにして間に sleep を挟む。
EMBED_BATCH_SIZE = 50
SLEEP_BETWEEN_BATCHES = 1.0
MAX_RETRIES = 6
BACKOFF_SCHEDULE = (5, 15, 30, 60, 120, 120)  # 秒

# 出典情報。生成された JSON に埋め込んでレビュー時に辿れるようにする。
SOURCE = {
    "title": "中学校学習指導要領（平成29年告示）解説 数学編",
    "publisher": "文部科学省",
    "url": "https://www.mext.go.jp/component/a_menu/education/micro_detail/__icsFiles/afieldfile/2019/03/18/1387018_004.pdf",
    "accessed": "2026-07-25",
}

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "rag" / "data"
VECTORS_PATH = DATA_DIR / "guidelines_vectors.npz"
CHUNKS_PATH = DATA_DIR / "guidelines_chunks.json"
# 途中で 429 などで落ちても計算済みの埋め込みを捨てないためのチェックポイント
CHECKPOINT_PATH = DATA_DIR / ".build_checkpoint.npz"

# コンテナ内 (/app/scripts/...) とホスト (<repo>/backend/scripts/...) の
# どちらから実行されても PDF を見つけられるように候補を順に探す。
PDF_CANDIDATES = [
    Path(__file__).resolve().parent.parent / "rag" / "documents" / "math_guidelines.pdf",
    Path(__file__).resolve().parents[2] / "rag" / "documents" / "math_guidelines.pdf",
]


def find_pdf() -> Path:
    for candidate in PDF_CANDIDATES:
        if candidate.exists():
            return candidate
    searched = "\n".join(f"  - {c}" for c in PDF_CANDIDATES)
    raise SystemExit(
        f"math_guidelines.pdf が見つかりません。--pdf で指定してください。\n探索したパス:\n{searched}"
    )


def load_pages(pdf_path: Path) -> list[tuple[int, str]]:
    """(ページ番号, テキスト) のリストを返す。ページ番号は1始まり。"""
    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((i, text))
    return pages


def split_pages(pages: list[tuple[int, str]]) -> list[dict]:
    """ページ単位のテキストをチャンクに分割し、ページ番号を保持する。"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = []
    for page_number, text in pages:
        for piece in splitter.split_text(text):
            piece = piece.strip()
            if piece:
                chunks.append({"id": len(chunks), "page": page_number, "text": piece})
    return chunks


def fingerprint(texts: list[str]) -> str:
    """チェックポイントが同じ入力に対するものか判定するための指紋。"""
    h = hashlib.sha256()
    h.update(f"{EMBEDDING_MODEL}|{CHUNK_SIZE}|{CHUNK_OVERLAP}|{len(texts)}".encode())
    for t in texts:
        h.update(t.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def load_checkpoint(expected: str) -> list[list[float]]:
    """入力が一致するチェックポイントがあれば計算済みベクトルを返す。"""
    if not CHECKPOINT_PATH.exists():
        return []
    try:
        with np.load(CHECKPOINT_PATH) as npz:
            if str(npz["fingerprint"]) != expected:
                print("  チェックポイントは別の入力のものなので破棄します")
                return []
            done = npz["vectors"]
    except (OSError, KeyError, ValueError) as e:
        print(f"  チェックポイントを読めませんでした ({type(e).__name__}: {e})。最初から計算します")
        return []
    print(f"  チェックポイントから {len(done)} 件を復元しました")
    return [row.tolist() for row in done]


def save_checkpoint(vectors: list[list[float]], expected: str) -> None:
    """一時ファイルに書いてから置き換える（書き込み中の中断で壊さない）。"""
    tmp = CHECKPOINT_PATH.with_suffix(".tmp.npz")
    np.savez(tmp, vectors=np.asarray(vectors, dtype=np.float32), fingerprint=np.array(expected))
    tmp.replace(CHECKPOINT_PATH)


def embed_batch_with_retry(
    embeddings: GoogleGenerativeAIEmbeddings, batch: list[str]
) -> list[list[float]]:
    """1バッチを埋め込む。429 や一時的なエラーは指数バックオフでリトライする。"""
    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            return embeddings.embed_documents(batch)
        except Exception as e:  # API 側のエラー型に依存したくないので広く捕まえる
            last_error = e
            wait = BACKOFF_SCHEDULE[min(attempt, len(BACKOFF_SCHEDULE) - 1)]
            print(
                f"    埋め込み失敗 ({type(e).__name__}: {str(e)[:200]})。"
                f"{wait}秒待って再試行 ({attempt + 1}/{MAX_RETRIES})"
            )
            time.sleep(wait)
    raise RuntimeError(f"バッチの埋め込みに{MAX_RETRIES}回失敗しました: {last_error}") from last_error


def embed_chunks(texts: list[str], batch_size: int, sleep_s: float) -> np.ndarray:
    """チャンク本文を埋め込み、L2正規化した float32 行列を返す。

    バッチごとにチェックポイントを書くので、途中で落ちても再実行すれば
    計算済みのぶんは再利用される。
    """
    # ホストから実行するとき用にリポジトリルートの .env を読む（コンテナでは env_file 済み）
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    except ImportError:
        pass

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise SystemExit("GOOGLE_API_KEY が設定されていません。")

    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=api_key,
    )

    expected = fingerprint(texts)
    vectors = load_checkpoint(expected)
    if len(vectors) > len(texts):  # 念のため（指紋が一致していれば起きない）
        vectors = []

    try:
        while len(vectors) < len(texts):
            start = len(vectors)
            batch = texts[start : start + batch_size]
            vectors.extend(embed_batch_with_retry(embeddings, batch))
            save_checkpoint(vectors, expected)
            print(f"  埋め込み {len(vectors)}/{len(texts)} 件完了")
            if len(vectors) < len(texts) and sleep_s > 0:
                time.sleep(sleep_s)
    except (RuntimeError, KeyboardInterrupt) as e:
        # 部分結果はチェックポイントに残っているので、再実行で続きから再開できる
        raise SystemExit(
            f"埋め込みを中断しました: {e}\n"
            f"計算済み {len(vectors)}/{len(texts)} 件は {CHECKPOINT_PATH.name} に保存済みです。"
            f"再実行すると続きから再開します。"
        ) from e

    matrix = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    # ゼロベクトルでのゼロ除算を避ける（正規化後もゼロのまま残る）
    norms[norms == 0] = 1.0
    return matrix / norms


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=None, help="入力PDFのパス")
    parser.add_argument(
        "--batch-size", type=int, default=EMBED_BATCH_SIZE, help="1リクエストあたりのチャンク数"
    )
    parser.add_argument(
        "--sleep", type=float, default=SLEEP_BETWEEN_BATCHES, help="バッチ間の待機秒数"
    )
    args = parser.parse_args()

    pdf_path = args.pdf if args.pdf else find_pdf()
    if not pdf_path.exists():
        raise SystemExit(f"PDFが存在しません: {pdf_path}")

    print(f"PDFを読み込み中: {pdf_path}")
    pages = load_pages(pdf_path)
    print(f"{len(pages)}ページ（テキストあり）読み込みました")

    print(f"チャンク分割中 (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
    chunks = split_pages(pages)
    print(f"{len(chunks)}チャンクに分割しました")
    if not chunks:
        raise SystemExit("チャンクが0件です。PDFからテキストを抽出できていません。")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print(f"埋め込みを計算中 (batch={args.batch_size}, sleep={args.sleep}s)...")
    matrix = embed_chunks([c["text"] for c in chunks], args.batch_size, args.sleep)
    print(f"埋め込み行列: shape={matrix.shape}, dtype={matrix.dtype}")

    np.savez_compressed(VECTORS_PATH, vectors=matrix)

    payload = {
        "source": SOURCE,
        "embedding_model": EMBEDDING_MODEL,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "normalized": True,
        "dimensions": int(matrix.shape[1]),
        "chunk_count": len(chunks),
        "chunks": chunks,
    }
    with CHUNKS_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    CHECKPOINT_PATH.unlink(missing_ok=True)

    print(f"書き出しました:\n  {VECTORS_PATH} ({VECTORS_PATH.stat().st_size / 1e6:.2f} MB)")
    print(f"  {CHUNKS_PATH} ({CHUNKS_PATH.stat().st_size / 1e6:.2f} MB)")
    print("完了しました！")


if __name__ == "__main__":
    sys.exit(main())
