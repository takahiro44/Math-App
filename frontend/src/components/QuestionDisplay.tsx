import { InlineMath } from 'react-katex'
import 'katex/dist/katex.min.css'

type Question = {
  question: string
  answer: string
  explanation: string
  hint: string
}

type Props = {
  question: Question
}

const MathText = ({ text }: { text: string }) => {
  const parts = text.split(/(\$[^$]+\$)/)
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('$') && part.endsWith('$')) {
          const math = part.slice(1, -1)
          return <InlineMath key={i} math={math} />
        }
        return <span key={i}>{part}</span>
      })}
    </>
  )
}

function QuestionDisplay({ question }: Props) {
  return (
    <div className="mt-6 space-y-4">
      <div className="bg-blue-50 rounded-lg p-4">
        <h2 className="font-bold text-gray-700 mb-2">問題</h2>
        <p className="text-gray-800 whitespace-pre-wrap">
          <MathText text={question.question} />
        </p>
      </div>
      <div className="bg-yellow-50 rounded-lg p-4">
        <h2 className="font-bold text-gray-700 mb-2">ヒント</h2>
        <p className="text-gray-800">
          <MathText text={question.hint} />
        </p>
      </div>
      <div className="bg-green-50 rounded-lg p-4">
        <h2 className="font-bold text-gray-700 mb-2">解答</h2>
        <p className="text-gray-800 whitespace-pre-wrap">
          <MathText text={question.answer} />
        </p>
      </div>
      <div className="bg-gray-50 rounded-lg p-4">
        <h2 className="font-bold text-gray-700 mb-2">解説</h2>
        <p className="text-gray-800 whitespace-pre-wrap">
          <MathText text={question.explanation} />
        </p>
      </div>
    </div>
  )
}

export default QuestionDisplay