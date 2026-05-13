import MathText from './MathText'

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

function QuestionDisplay({ question }: Props) {
  return (
    <div className="mt-6 space-y-4">
      <div className="bg-blue-50 rounded-lg p-4">
        <h2 className="font-bold text-gray-700 mb-2">問題</h2>
        <div className="text-gray-800 whitespace-pre-wrap">
          <MathText text={question.question} />
        </div>
      </div>
    </div>
  )
}

export default QuestionDisplay