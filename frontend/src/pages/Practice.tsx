import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { mathUnits } from '../mathUnits'
import QuestionDisplay from '../components/QuestionDisplay'
import AnswerForm from '../components/AnswerForm'
import GradingResult from '../components/GradingResult'
import AnswerReview from '../components/AnswerReview'
import QuestionForm from '../components/QuestionForm'
import ModeDescription from '../components/ModeDescription'
import { API_BASE_URL } from '../config'

type Question = {
  question: string
  answer: string
  explanation: string
  hint: string
}

type GradingResponse = {
  is_correct: boolean
  feedback: string
}

type PracticeState = 'setup' | 'loading' | 'practicing' | 'result'

function Practice() {
  const navigate = useNavigate()

  // 設定
  const [grade, setGrade] = useState('1')
  const [unit, setUnit] = useState(mathUnits['1'][0])
  const [difficulty, setDifficulty] = useState('normal')
  const [numQuestions, setNumQuestions] = useState(5)

  // 演習状態
  const [state, setState] = useState<PracticeState>('setup')
  const [questions, setQuestions] = useState<Question[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [userAnswer, setUserAnswer] = useState('')
  const [gradingResult, setGradingResult] = useState<GradingResponse | null>(null)
  const [gradingLoading, setGradingLoading] = useState(false)
  const [results, setResults] = useState<boolean[]>([])
  const [showHint, setShowHint] = useState(false)

  const currentQuestion = questions[currentIndex]

  // 全問一括生成
  const startPractice = async () => {
    setState('loading')
    try {
      const response = await fetch(`${API_BASE_URL}/print/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grade: Number(grade),
          unit,
          difficulty,
          num_questions: numQuestions,
        }),
      })
      const data = await response.json()
      setQuestions(data.questions)
      setCurrentIndex(0)
      setResults([])
      setState('practicing')
    } catch (error) {
      console.error(error)
      setState('setup')
    }
  }

  // 採点
  const gradeAnswer = async () => {
    if (!currentQuestion) return
    setGradingLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/grading/grade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: currentQuestion.question,
          correct_answer: currentQuestion.answer,
          user_answer: userAnswer,
        }),
      })
      const data = await response.json()
      setGradingResult(data)
      setResults(prev => [...prev, data.is_correct])
    } catch (error) {
      console.error(error)
    } finally {
      setGradingLoading(false)
    }
  }

  // 次の問題へ
  const nextQuestion = () => {
    if (currentIndex + 1 >= questions.length) {
      setState('result')
    } else {
      setCurrentIndex(prev => prev + 1)
      setUserAnswer('')
      setGradingResult(null)
      setShowHint(false)
    }
  }

  const difficultyLabel =
    difficulty === 'easy' ? 'やさしい' :
    difficulty === 'normal' ? '標準' : '難しい'

  const correctCount = results.filter(r => r).length

  // 結果メッセージ
  const getResultMessage = () => {
    const rate = correctCount / numQuestions
    if (rate === 1) return '完璧です！全問正解おめでとうございます！'
    if (rate >= 0.8) return 'よくできました！あと少しで完璧です！'
    if (rate >= 0.6) return 'もう少し練習が必要ですが、頑張りました！'
    return 'まだ難しいかもしれません。もう一度挑戦してみましょう！'
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-md p-8 w-full max-w-lg">

        {/* 設定画面 */}
        {state === 'setup' && (
          <>
            <div className="flex items-center mb-6">
              <button
                className="text-gray-400 hover:text-gray-600 mr-3"
                onClick={() => navigate('/')}
              >
                ← 戻る
              </button>
              <h1 className="text-2xl font-bold text-blue-600">演習モード</h1>
            </div>

            <ModeDescription
              description={
                <>
                  <p>学年・単元・難易度を選んで演習を始めましょう。</p>
                  <p>問題を解いて採点し、解説で理解を深めることができます。</p>
                </>
              }
              steps={[
                { number: 1, text: '学年・単元・難易度・問題数を選ぶ' },
                { number: 2, text: '「演習開始」を押すと問題が出題される' },
                { number: 3, text: '回答を入力して採点する' },
                { number: 4, text: '全問終了後に結果を確認する' },
              ]}
              color="blue"
            />
            <QuestionForm
              grade={grade}
              unit={unit}
              difficulty={difficulty}
              onGradeChange={setGrade}
              onUnitChange={setUnit}
              onDifficultyChange={setDifficulty}
            />

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                問題数：<span className="text-blue-600 font-bold">{numQuestions}問</span>
              </label>
              <input
                type="range"
                min="1"
                max="10"
                value={numQuestions}
                onChange={(e) => setNumQuestions(Number(e.target.value))}
                className="w-full accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>1問</span>
                <span>10問</span>
              </div>
            </div>

            <button
              className="w-full bg-blue-600 text-white rounded-lg p-3 font-medium hover:bg-blue-700"
              onClick={startPractice}
            >
              演習開始
            </button>
          </>
        )}

        {/* ローディング画面 */}
        {state === 'loading' && (
          <div className="text-center py-16">
            <div className="text-gray-500 mb-2">問題を生成中...</div>
            <div className="text-sm text-gray-400">{numQuestions}問分の問題を準備しています</div>
          </div>
        )}

        {/* 演習画面 */}
        {state === 'practicing' && currentQuestion && (
          <>
            {/* ヘッダー */}
            <div className="mb-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm text-gray-500">
                  {unit}　{difficultyLabel}
                </span>
                <span className="text-sm font-medium text-gray-700">
                  {currentIndex + 1} / {numQuestions}問
                </span>
              </div>
              {/* 進捗バー */}
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${((currentIndex + 1) / numQuestions) * 100}%` }}
                />
              </div>
            </div>

            {/* 問題 */}
            <QuestionDisplay question={currentQuestion} />

            {/* ヒントトグル */}
            <div className="mt-4">
              <button
                className="text-sm text-blue-500 hover:text-blue-700 flex items-center gap-1"
                onClick={() => setShowHint(!showHint)}
              >
                {showHint ? '▼ ヒントを隠す' : '▶ ヒントを見る'}
              </button>
              {showHint && (
                <div className="mt-2 bg-yellow-50 rounded-lg p-3 text-sm text-gray-700">
                  {currentQuestion.hint}
                </div>
              )}
            </div>

            {/* 回答入力 */}
            
            <AnswerForm
              userAnswer={userAnswer}
              loading={gradingLoading}
              disabled={!!gradingResult}
              onAnswerChange={setUserAnswer}
              onSubmit={gradeAnswer}
            />
            

            {/* 採点結果 */}
            {gradingResult && (
              <>
                <GradingResult
                  isCorrect={gradingResult.is_correct}
                  feedback={gradingResult.feedback}
                />
                <AnswerReview
                  answer={currentQuestion.answer}
                  explanation={currentQuestion.explanation}
                />
                <button
                  className="w-full mt-4 bg-blue-600 text-white rounded-lg p-3 font-medium hover:bg-blue-700"
                  onClick={nextQuestion}
                >
                  {currentIndex + 1 >= numQuestions ? '結果を見る' : '次の問題へ'}
                </button>
              </>
            )}
          </>
        )}

        {/* 結果画面 */}
        {state === 'result' && (
          <>
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-2">演習完了！</h2>
              <p className="text-gray-500">{unit}　{difficultyLabel}</p>
            </div>

            <div className="bg-blue-50 rounded-xl p-6 text-center mb-6">
              <div className="text-5xl font-bold text-blue-600 mb-1">
                {correctCount} / {numQuestions}
              </div>
              <div className="text-gray-600">問正解</div>
            </div>

            <p className="text-center text-gray-700 mb-6">{getResultMessage()}</p>

            {/* 問題ごとの結果 */}
            <div className="space-y-2 mb-6">
              {results.map((isCorrect, i) => (
                <div
                  key={i}
                  className={`flex items-center gap-3 p-3 rounded-lg ${isCorrect ? 'bg-green-50' : 'bg-red-50'}`}
                >
                  <span className={`font-bold ${isCorrect ? 'text-green-600' : 'text-red-600'}`}>
                    {isCorrect ? '✓' : '✗'}
                  </span>
                  <span className="text-sm text-gray-700">問{i + 1}</span>
                </div>
              ))}
            </div>

            <div className="flex gap-3">
              <button
                className="flex-1 bg-blue-600 text-white rounded-lg p-3 font-medium hover:bg-blue-700"
                onClick={() => {
                  setState('setup')
                  setResults([])
                  setQuestions([])
                  setCurrentIndex(0)
                  setUserAnswer('')
                  setGradingResult(null)
                  setShowHint(false)
                }}
              >
                もう一度
              </button>
              <button
                className="flex-1 bg-gray-500 text-white rounded-lg p-3 font-medium hover:bg-gray-600"
                onClick={() => navigate('/')}
              >
                ホームに戻る
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default Practice