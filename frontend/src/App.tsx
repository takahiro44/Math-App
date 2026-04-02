import { useState } from 'react'
import { mathUnits } from './mathUnits'
import QuestionForm from './components/QuestionForm'
import QuestionDisplay from './components/QuestionDisplay'
import AnswerForm from './components/AnswerForm'
import GradingResult from './components/GradingResult'
import AnswerReview from './components/AnswerReview'

type QuestionResponse = {
  question: string
  answer: string
  explanation: string
  hint: string
}

type GradingResponse = {
  is_correct: boolean
  feedback: string
}

function App() {
  const [grade, setGrade] = useState('1')
  const [unit, setUnit] = useState(mathUnits['1'][0])
  const [difficulty, setDifficulty] = useState('normal')
  const [question, setQuestion] = useState<QuestionResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [userAnswer, setUserAnswer] = useState('')
  const [gradingResult, setGradingResult] = useState<GradingResponse | null>(null)
  const [gradingLoading, setGradingLoading] = useState(false)

  const generateQuestion = async () => {
    setLoading(true)
    setUserAnswer('')
    setGradingResult(null)
    try {
      const response = await fetch('http://localhost:8000/question/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grade: Number(grade),
          unit,
          difficulty,
        }),
      })
      const data = await response.json()
      setQuestion(data)
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const gradeAnswer = async () => {
    if (!question) return
    setGradingLoading(true)
    try {
      const response = await fetch('http://localhost:8000/grading/grade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question.question,
          correct_answer: question.answer,
          user_answer: userAnswer,
        }),
      })
      const data = await response.json()
      setGradingResult(data)
    } catch (error) {
      console.error(error)
    } finally {
      setGradingLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-md p-8 w-full max-w-lg">
        <h1 className="text-2xl font-bold text-blue-600 mb-6">
          数学問題アプリ
        </h1>
        <QuestionForm
          grade={grade}
          unit={unit}
          difficulty={difficulty}
          loading={loading}
          onGradeChange={setGrade}
          onUnitChange={setUnit}
          onDifficultyChange={setDifficulty}
          onSubmit={generateQuestion}
        />
        {question && (
          <>
            <QuestionDisplay question={question} />
            <AnswerForm
              userAnswer={userAnswer}
              loading={gradingLoading}
              onAnswerChange={setUserAnswer}
              onSubmit={gradeAnswer}
            />
            {gradingResult && (
              <>
                <GradingResult
                  isCorrect={gradingResult.is_correct}
                  feedback={gradingResult.feedback}
                />
                <AnswerReview
                  answer={question.answer}
                  explanation={question.explanation}
                />
              </>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default App