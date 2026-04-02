type Props = {
  isCorrect: boolean
  feedback: string
}

function GradingResult({ isCorrect, feedback }: Props) {
  return (
    <div className={`mt-4 rounded-lg p-4 ${isCorrect ? 'bg-green-100' : 'bg-red-100'}`}>
      <p className={`font-bold text-lg mb-1 ${isCorrect ? 'text-green-700' : 'text-red-700'}`}>
        {isCorrect ? '✓ 正解！' : '✗ 不正解'}
      </p>
      <p className={`text-sm ${isCorrect ? 'text-green-700' : 'text-red-700'}`}>
        {feedback}
      </p>
    </div>
  )
}

export default GradingResult