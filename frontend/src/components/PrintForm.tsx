type Props = {
  grade: string
  unit: string
  difficulty: string
  loading: boolean
  loadingNum: number | null
  onSubmit: (numQuestions: number) => void
}

function PrintForm({ grade, unit, difficulty, loading, loadingNum, onSubmit }: Props) {
  const options = [3, 5, 10]
  const difficultyLabel =
    difficulty === 'easy' ? 'やさしい' :
    difficulty === 'normal' ? '標準' : '難しい'

  return (
    <div className="mt-8 border-t pt-6">
      <h2 className="text-lg font-bold text-gray-700 mb-4">
        問題プリントを作成する
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        中学{grade}年生 / {unit} / {difficultyLabel}
      </p>
      <div className="flex gap-3">
        {options.map((num) => (
          <button
            key={num}
            className="flex-1 bg-purple-600 text-white rounded-lg p-3 font-medium hover:bg-purple-700 disabled:opacity-50"
            onClick={() => onSubmit(num)}
            disabled={loading}
          >
            {loading && loadingNum === num ? '生成中...' : `${num}問`}
          </button>
        ))}
      </div>
    </div>
  )
}

export default PrintForm