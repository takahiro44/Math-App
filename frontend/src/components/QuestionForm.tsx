import { mathUnits } from '../mathUnits'

type Props = {
  grade: string
  unit: string
  difficulty: string
  loading: boolean
  onGradeChange: (grade: string) => void
  onUnitChange: (unit: string) => void
  onDifficultyChange: (difficulty: string) => void
  onSubmit: () => void
}

function QuestionForm({
  grade,
  unit,
  difficulty,
  loading,
  onGradeChange,
  onUnitChange,
  onDifficultyChange,
  onSubmit,
}: Props) {
  return (
    <div>
      {/* 学年選択 */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          学年
        </label>
        <select
          className="w-full border border-gray-300 rounded-lg p-2"
          value={grade}
          onChange={(e) => {
            onGradeChange(e.target.value)
            onUnitChange(mathUnits[e.target.value][0])
          }}
        >
          <option value="1">中学1年生</option>
          <option value="2">中学2年生</option>
          <option value="3">中学3年生</option>
        </select>
      </div>

      {/* 単元選択 */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          単元
        </label>
        <select
          className="w-full border border-gray-300 rounded-lg p-2"
          value={unit}
          onChange={(e) => onUnitChange(e.target.value)}
        >
          {mathUnits[grade].map((u) => (
            <option key={u} value={u}>{u}</option>
          ))}
        </select>
      </div>

      {/* 難易度選択 */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          難易度
        </label>
        <select
          className="w-full border border-gray-300 rounded-lg p-2"
          value={difficulty}
          onChange={(e) => onDifficultyChange(e.target.value)}
        >
          <option value="easy">やさしい</option>
          <option value="normal">標準</option>
          <option value="hard">難しい</option>
        </select>
      </div>

      {/* 生成ボタン */}
      <button
        className="w-full bg-blue-600 text-white rounded-lg p-3 font-medium hover:bg-blue-700 disabled:opacity-50"
        onClick={onSubmit}
        disabled={loading}
      >
        {loading ? '生成中...' : '問題を生成する'}
      </button>
    </div>
  )
}

export default QuestionForm