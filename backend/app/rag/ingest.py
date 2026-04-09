from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
import os

DOCUMENTS_PATH = "/app/rag/documents/math_guidelines.pdf"
VECTORSTORE_PATH = "/app/rag/vectorstore"

def ingest():
    print("PDFを読み込み中...")
    loader = PyPDFLoader(DOCUMENTS_PATH)
    documents = loader.load()
    print(f"{len(documents)}ページ読み込みました")

    print("チャンク分割中...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(documents)
    print(f"{len(chunks)}チャンクに分割しました")

    print("ベクトル化してChromaに保存中...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTORSTORE_PATH
    )
    print("完了しました！")

if __name__ == "__main__":
    ingest()