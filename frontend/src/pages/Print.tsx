import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { mathUnits } from '../mathUnits'
import QuestionForm from '../components/QuestionForm'
import PrintForm from '../components/PrintForm'
import PrintPreview from '../components/PrintPreview'

type QuestionItem = {
  question: string
  answer: string
  explanation: string
  hint: string
}

function Print() {
  const navigate = useNavigate()
  const [grade, setGrade] = useState('1')
  const [unit, setUnit] = useState(mathUnits['1'][0])
  const [difficulty, setDifficulty] = useState('normal')
  const [printData, setPrintData] = useState<{ questions: QuestionItem[] } | null>(null)
  const [printLoading, setPrintLoading] = useState(false)
  const [printLoadingNum, setPrintLoadingNum] = useState<number | null>(null)

  const generatePrint = async (numQuestions: number) => {
    setPrintLoading(true)
    setPrintLoadingNum(numQuestions)
    try {
      const response = await fetch('http://localhost:8000/print/generate', {
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
      setPrintData(data)
    } catch (error) {
      console.error(error)
    } finally {
      setPrintLoading(false)
      setPrintLoadingNum(null)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-md p-8 w-full max-w-lg">
        <div className="flex items-center mb-6">
          <button
            className="text-gray-400 hover:text-gray-600 mr-3"
            onClick={() => navigate('/')}
          >
            ← 戻る
          </button>
          <h1 className="text-2xl font-bold text-purple-600">プリント作成モード</h1>
        </div>
        <QuestionForm
          grade={grade}
          unit={unit}
          difficulty={difficulty}
          loading={false}
          onGradeChange={setGrade}
          onUnitChange={setUnit}
          onDifficultyChange={setDifficulty}
          onSubmit={() => {}}
        />
        <PrintForm
          grade={grade}
          unit={unit}
          difficulty={difficulty}
          loading={printLoading}
          loadingNum={printLoadingNum}
          onSubmit={generatePrint}
        />
        {printData && (
          <PrintPreview
            grade={grade}
            unit={unit}
            difficulty={difficulty}
            questions={printData.questions}
            onClose={() => setPrintData(null)}
          />
        )}
      </div>
    </div>
  )
}

export default Print