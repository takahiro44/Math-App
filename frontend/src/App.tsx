import { useState } from 'react'

function App() {
  const [grade, setGrade] = useState('1')
  const [unit, setUnit] = useState('')
  const [difficulty, setDifficulty] = useState('normal')

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-md p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold text-blue-600 mb-6">
          数学問題アプリ
        </h1>

        {/* 学年選択 */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            学年
          </label>
          <select
            className="w-full border border-gray-300 rounded-lg p-2"
            value={grade}
            onChange={(e) => setGrade(e.target.value)}
          >
            <option value="1">中学1年生</option>
            <option value="2">中学2年生</option>
            <option value="3">中学3年生</option>
          </select>
        </div>

        {/* 単元入力 */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            単元
          </label>
          <input
            type="text"
            className="w-full border border-gray-300 rounded-lg p-2"
            placeholder="例：一次関数"
            value={unit}
            onChange={(e) => setUnit(e.target.value)}
          />
        </div>

        {/* 難易度選択 */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            難易度
          </label>
          <select
            className="w-full border border-gray-300 rounded-lg p-2"
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
          >
            <option value="easy">やさしい</option>
            <option value="normal">標準</option>
            <option value="hard">難しい</option>
          </select>
        </div>

        {/* 生成ボタン */}
        <button
          className="w-full bg-blue-600 text-white rounded-lg p-3 font-medium hover:bg-blue-700"
          onClick={() => console.log({ grade, unit, difficulty })}
        >
          問題を生成する
        </button>
      </div>
    </div>
  )
}

export default App