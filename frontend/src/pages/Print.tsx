import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { mathUnits } from '../mathUnits'
import QuestionForm from '../components/QuestionForm'
import PrintForm from '../components/PrintForm'
import PrintPreview from '../components/PrintPreview'
import ModeDescription from '../components/ModeDescription'
import { API_BASE_URL } from '../config'

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
  const [numQuestions, setNumQuestions] = useState(5)

  const generatePrint = async () => {
    setPrintLoading(true)
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
      setPrintData(data)
    } catch (error) {
      console.error(error)
    } finally {
      setPrintLoading(false)
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
        <ModeDescription
          description={
                <>
                  <p>学年・単元・難易度と問題数を選んで、問題プリントを作成できます。</p>
                  <p>解答・解説のプリントも作成できます。</p>
                </>
              }
          steps={[
            { number: 1, text: '学年・単元・難易度を選ぶ' },
            { number: 2, text: '問題数をスライダーで選ぶ' },
            { number: 3, text: '「プリントを作成する」を押す' },
            { number: 4, text: '問題用紙・解答解説を印刷する' },
          ]}
          color="purple"
        />
        <QuestionForm
          grade={grade}
          unit={unit}
          difficulty={difficulty}
          onGradeChange={setGrade}
          onUnitChange={setUnit}
          onDifficultyChange={setDifficulty}
        />
        <PrintForm
          loading={printLoading}
          numQuestions={numQuestions}
          onNumQuestionsChange={setNumQuestions}
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