type Props = {
  userAnswer: string
  loading: boolean
  disabled?: boolean        // ← 追加
  onAnswerChange: (answer: string) => void
  onSubmit: () => void
}

function AnswerForm({ userAnswer, loading, disabled = false, onAnswerChange, onSubmit }: Props) {
  return (
    <div className="mt-6">
      <div className="mb-3">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          回答を入力してください
        </label>
        <input
          type="text"
          className="w-full border border-gray-300 rounded-lg p-2 disabled:bg-gray-100 disabled:text-gray-500 disabled:cursor-not-allowed"
          placeholder="例：3x+1"
          value={userAnswer}
          onChange={(e) => onAnswerChange(e.target.value)}
          disabled={disabled}
        />
      </div>
      {!disabled && (
        <button
          className="w-full bg-green-600 text-white rounded-lg p-3 font-medium hover:bg-green-700 disabled:opacity-50"
          onClick={onSubmit}
          disabled={loading || !userAnswer}
        >
          {loading ? '採点中...' : '採点する'}
        </button>
      )}
    </div>
  )
}

export default AnswerForm