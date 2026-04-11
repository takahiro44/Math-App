type Props = {
  grade: string
  unit: string
  difficulty: string
  loading: boolean
  numQuestions: number
  onNumQuestionsChange: (num: number) => void
  onSubmit: () => void
}

function PrintForm({
  grade,
  unit,
  difficulty,
  loading,
  numQuestions,
  onNumQuestionsChange,
  onSubmit,
}: Props) {
  const difficultyLabel =
    difficulty === 'easy' ? 'やさしい' :
    difficulty === 'normal' ? '標準' : '難しい'

  return (
    <div className="mt-8">
      <h2 className="text-lg font-bold text-gray-700 mb-4">
        問題プリントを作成する
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        中学{grade}年生 / {unit} / {difficultyLabel}
      </p>
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          問題数：<span className="text-purple-600 font-bold">{numQuestions}問</span>
        </label>
        <input
          type="range"
          min="1"
          max="10"
          value={numQuestions}
          onChange={(e) => onNumQuestionsChange(Number(e.target.value))}
          className="w-full accent-purple-600"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>1問</span>
          <span>10問</span>
        </div>
      </div>
      <button
        className="w-full bg-purple-600 text-white rounded-lg p-3 font-medium hover:bg-purple-700 disabled:opacity-50"
        onClick={onSubmit}
        disabled={loading}
      >
        {loading ? '生成中...' : 'プリントを作成する'}
      </button>
    </div>
  )
}

export default PrintForm