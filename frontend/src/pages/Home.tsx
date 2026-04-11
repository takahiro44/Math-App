import { useNavigate } from 'react-router-dom'

function Home() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-md p-10 w-full max-w-md text-center">
        <h1 className="text-3xl font-bold text-blue-600 mb-2">数学問題アプリ</h1>
        <p className="text-gray-500 mb-10">中学生向け数学学習サポート</p>

        <div className="flex flex-col gap-4">
          <button
            className="bg-blue-600 text-white rounded-xl p-5 font-medium hover:bg-blue-700 text-left"
            onClick={() => navigate('/practice')}
          >
            <div className="text-lg font-bold mb-1">演習モード</div>
            <div className="text-sm opacity-80">問題を解いて採点してもらおう</div>
          </button>
          <button
            className="bg-purple-600 text-white rounded-xl p-5 font-medium hover:bg-purple-700 text-left"
            onClick={() => navigate('/print')}
          >
            <div className="text-lg font-bold mb-1">プリント作成モード</div>
            <div className="text-sm opacity-80">問題プリントを作成して印刷しよう</div>
          </button>
        </div>
      </div>
    </div>
  )
}

export default Home