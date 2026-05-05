from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
from typing import List
from app.schemas.question import QuestionResponse


class QuestionItem(BaseModel):
    question: str
    answer: str
    explanation: str
    hint: str


class QuestionsResponse(BaseModel):
    questions: List[QuestionItem]


# ① 制御文字を「本来あるべきLaTeXコマンド」に戻す前処理
def _restore_latex_escapes(text: str) -> str:
    """
    LLMが \\frac のつもりで \frac と返したとき、JSONデコード前の段階では
    まだ「\f + rac」の制御文字には化けていないが、Geminiの出力時点で既に
    バックスラッシュが1つだとJSONパーサが \f をform feedと解釈してしまう。

    そこで、JSONパースを通す前に「制御文字 + 既知のLaTeXコマンド名の残骸」
    というパターンを見つけて、正しいLaTeX記法に戻す。
    """
    replacements = {
        '\x0crac': r'\\frac',    # \f + rac → \\frac
    }
    for broken, fixed in replacements.items():
        text = text.replace(broken, fixed)
    return text


# ② Gemini の生出力（AIMessage）から content 文字列を取り出して修復するRunnable
def _preprocess(message):
    """LLMの返答を JsonOutputParser に渡す前にクリーニングする"""
    content = message.content if hasattr(message, 'content') else str(message)
    return _restore_latex_escapes(content)


# ③ 修復処理を挟んだチェーン用パーサ
_json_parser = JsonOutputParser(pydantic_object=QuestionsResponse)
parser = RunnableLambda(_preprocess) | _json_parser

_single_json_parser = JsonOutputParser(pydantic_object=QuestionResponse)
single_parser = RunnableLambda(_preprocess) | _single_json_parser


# ④ 難易度ごとの詳細ガイドライン
DIFFICULTY_GUIDELINES = {
    "easy": """
- やさしい：その単元を習いたての段階の問題
- 計算の手順は最小限で、定義や基本ルールが正しく使えれば解ける
- 例（中1・正負の数）：(-3) + 5、(-4) × 2 のような1ステップで解ける問題
- 例（中3・因数分解）：x^2 + 5x + 6 のような単純な共通因数や基本的な因数分解
""",
    "normal": """
- 標準：定期テストに出題される普通のレベル
- 教科書の例題や基本問題と同程度。決して難しくはなく、本当に「普通の問題」
- 例（中1・方程式）：3(x - 4) = 9 のような分配法則 + 移項を含む問題
- 例（中3・因数分解）：x^2 + 3x - 18 のような典型的な因数分解
- 例（中2・連立方程式）：加減法または代入法ですぐ解ける2元1次連立方程式
""",
    "hard": """
- 難しい：計算の過程が多い問題
- 複数の手順を組み合わせる必要があり、ミスをしやすい
- ただし高校レベルの内容や、その単元の範囲外の知識は使わない
- 中学校で習う公式や手順の範囲内で完結すること
- 例（中3・式の計算）：分子に多項式があり、分母が異なる分数式の通分が必要なもの
- 例（中1・方程式）：分数を含む方程式で、両辺を最小公倍数で払う必要があるもの
- 例（中3・因数分解）：4x^2 + 12x + 9 のような、係数の工夫が必要なもの
"""
}


# ⑤ 難易度パラメータ → ガイドライン文字列の変換関数
def get_difficulty_guideline(difficulty: str) -> str:
    """
    難易度パラメータ（"easy"/"normal"/"hard"）を、
    LLMに渡す詳細なガイドライン文字列に変換する。
    未知の値が来た場合は "normal" のガイドラインをフォールバックとして返す。
    """
    return DIFFICULTY_GUIDELINES.get(difficulty, DIFFICULTY_GUIDELINES["normal"])


question_prompt = PromptTemplate(
    template="""
あなたは中学校の数学教師です。
以下の条件で数学の計算問題を{num_questions}問作成してください。

学年: 中学{grade}年生
単元: {unit}
難易度: {difficulty}

【学習指導要領の参考情報】
{context}

【難易度の基準】
{difficulty_guideline}

【重要な制約】
- 上記の学習指導要領の内容に沿った問題を出題してください
- 計算で解ける問題のみ出題してください
- 図形の描写やグラフの読み取りを必要とする問題は出題しないでください
- 文章題の場合も、計算で解けるものに限定してください
- 問題同士が似たパターンにならないようにバリエーションを持たせてください
- 数式は必ず $...$ で囲んでLaTeX記法で出力してください
- 例：x² は $x^2$、(2x-3)² は $(2x-3)^2$ と表記してください
- 数式を $...$ で囲まずにプレーンテキストで出力しないでください
- 連立方程式の問題は「次の連立方程式を解きなさい」という形式で、式を $$\begin{{cases}} 式1 \\ 式2 \end{{cases}}$$ の形で出力してください
- 文章題は出題しないでください。式がそのまま与えられる計算問題のみ出題してください

【JSON出力時の重要な注意】
- 出力はJSON文字列です。LaTeXコマンドのバックスラッシュは必ず2つ重ねて出力してください
- 例：分数は \\\\frac{{x}}{{3}} と書く（\\frac ではなく）
- 例：掛け算記号は \\\\times と書く（\\times ではなく）
- 例：連立方程式は \\\\begin{{cases}} ... \\\\end{{cases}} と書く
- 単一のバックスラッシュ（\\frac など）はJSONエスケープとして解釈され壊れます

以下のJSON形式で返してください。
{format_instructions}
""",
    input_variables=["grade", "unit", "difficulty", "difficulty_guideline", "num_questions", "context"],  # ★
    partial_variables={"format_instructions": _json_parser.get_format_instructions()}
)


single_question_prompt = PromptTemplate(
    template="""
あなたは中学校の数学教師です。
以下の条件で数学の計算問題を1問作成してください。

学年: 中学{grade}年生
単元: {unit}
難易度: {difficulty}

【学習指導要領の参考情報】
{context}

【難易度の基準】
{difficulty_guideline}

【重要な制約】
- 上記の学習指導要領の内容に沿った問題を出題してください
- 計算で解ける問題のみ出題してください
- 図形の描写やグラフの読み取りを必要とする問題は出題しないでください
- 文章題の場合も、計算で解けるものに限定してください
- 数式は必ず $...$ で囲んでLaTeX記法で出力してください
- 例：x² は $x^2$、(2x-3)² は $(2x-3)^2$ と表記してください
- 数式を $...$ で囲まずにプレーンテキストで出力しないでください
- 連立方程式の問題は「次の連立方程式を解きなさい」という形式で、式を $$\begin{{cases}} 式1 \\ 式2 \end{{cases}}$$ の形で出力してください
- 文章題は出題しないでください。式がそのまま与えられる計算問題のみ出題してください

【JSON出力時の重要な注意】
- 出力はJSON文字列です。LaTeXコマンドのバックスラッシュは必ず2つ重ねて出力してください
- 例：分数は \\\\frac{{x}}{{3}} と書く（\\frac ではなく）
- 例：掛け算記号は \\\\times と書く（\\times ではなく）

以下のJSON形式で返してください。
{format_instructions}
""",
    input_variables=["grade", "unit", "difficulty", "difficulty_guideline", "context"],  # ★
    partial_variables={"format_instructions": _single_json_parser.get_format_instructions()}
)