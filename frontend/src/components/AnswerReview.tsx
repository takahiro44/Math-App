import { InlineMath } from 'react-katex'
import 'katex/dist/katex.min.css'

type Props = {
  answer: string
  explanation: string
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

function AnswerReview({ answer, explanation }: Props) {
  return (
    <div className="space-y-4 mt-4">
      <div className="bg-green-50 rounded-lg p-4">
        <h2 className="font-bold text-gray-700 mb-2">解答</h2>
        <p className="text-gray-800 whitespace-pre-wrap">
          <MathText text={answer} />
        </p>
      </div>
      <div className="bg-gray-50 rounded-lg p-4">
        <h2 className="font-bold text-gray-700 mb-2">解説</h2>
        <p className="text-gray-800 whitespace-pre-wrap">
          <MathText text={explanation} />
        </p>
      </div>
    </div>
  )
}

export default AnswerReview