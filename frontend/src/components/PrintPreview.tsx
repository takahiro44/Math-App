import { useState } from 'react'
import MathText from './MathText'


type Question = {
  question: string
  answer: string
  explanation: string
  hint: string
}

type Props = {
  grade: string
  unit: string
  difficulty: string
  questions: Question[]
  onClose: () => void
}


function PrintPreview({ grade, unit, difficulty, questions, onClose }: Props) {
  const [mode, setMode] = useState<'question' | 'answer'>('question')

  const difficultyLabel =
    difficulty === 'easy' ? 'やさしい' :
    difficulty === 'normal' ? '標準' : '難しい'

  const handlePrint = () => {
  const printContent = document.getElementById('print-content')?.innerHTML
  if (!printContent) return

  const printWindow = window.open('', '_blank')
  if (!printWindow) return

  const titleLabel = mode === 'question'
    ? `数学プリント_${unit}`
    : `数学プリント_${unit}_解答解説`

  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>${titleLabel}</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.css">
        <style>
          body { font-family: sans-serif; padding: 40px; }
          .question-block { margin-bottom: 40px; }
          .answer-line { border-bottom: 1px solid #999; margin-top: 40px; }
          hr { border-color: #ccc; margin: 16px 0; }
          .katex-mathml { display: none !important; }
        </style>
      </head>
      <body>
        ${printContent}
      </body>
    </html>
  `)
  printWindow.document.close()
  printWindow.focus()

  // フォントの読み込みが完了してから印刷ダイアログを開く
  if (printWindow.document.fonts && printWindow.document.fonts.ready) {
  printWindow.document.fonts.ready.then(() => {
    setTimeout(() => printWindow.print(), 300)
  })
  } else {
  // 古いブラウザ向けのフォールバック：少し待ってから印刷
  setTimeout(() => printWindow.print(), 500)
  }
}

  return (
    <div
      id="print-preview"
      className="fixed inset-0 bg-white z-50 overflow-auto"
    >
      {/* 操作ボタン（印刷時は非表示） */}
      <div className="print:hidden flex gap-4 p-4 border-b sticky top-0 bg-white shadow-sm z-50">
        <button
          className={`px-6 py-2 rounded-lg font-medium ${mode === 'question' ? 'bg-blue-600 text-white' : 'bg-white text-blue-600 border border-blue-600'}`}
          onClick={() => setMode('question')}
        >
          問題用紙
        </button>
        <button
          className={`px-6 py-2 rounded-lg font-medium ${mode === 'answer' ? 'bg-green-600 text-white' : 'bg-white text-green-600 border border-green-600'}`}
          onClick={() => setMode('answer')}
        >
          解答・解説
        </button>
        <button
          className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700"
          onClick={handlePrint}
        >
          印刷・PDF保存
        </button>
        <button
          className="bg-gray-500 text-white px-6 py-2 rounded-lg font-medium hover:bg-gray-600"
          onClick={onClose}
        >
          閉じる
        </button>
      </div>

      <div id="print-content" className="max-w-2xl mx-auto p-8">

        {/* 問題用紙 */}
        {mode === 'question' && (
          <div>
            <h1 className="text-xl font-bold mb-1">
              中学{grade}年生　数学プリント
            </h1>
            <p className="text-sm mb-4">
              単元：{unit}　難易度：{difficultyLabel}
            </p>
            <hr className="border-black mb-6" />
            {questions.map((q, i) => (
              <div key={i} className="mb-10 question-block">
                <p className="font-bold mb-2">問{i + 1}.</p>
                <p className="mb-4 leading-relaxed">
                  <MathText text={q.question} />
                </p>
                <div className="border-b border-gray-400 mt-10 answer-line" />
              </div>
            ))}
          </div>
        )}

        {/* 解答・解説用紙 */}
        {mode === 'answer' && (
          <div>
            <h1 className="text-xl font-bold mb-1">
              中学{grade}年生　数学プリント【解答・解説】
            </h1>
            <p className="text-sm mb-4">
              単元：{unit}　難易度：{difficultyLabel}
            </p>
            <hr className="border-black mb-6" />
            {questions.map((q, i) => (
              <div key={i} className="mb-6">
                <p className="font-bold mb-1">問{i + 1}.</p>
                <p className="mb-1">
                  <span className="font-medium">解答：</span>
                  <MathText text={q.answer} />
                </p>
                <p className="text-sm text-gray-700 leading-relaxed">
                  <span className="font-medium">解説：</span>
                  <MathText text={q.explanation} />
                </p>
                <hr className="border-gray-300 mt-4" />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default PrintPreview