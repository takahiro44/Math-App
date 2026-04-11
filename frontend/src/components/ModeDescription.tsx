import type { ReactNode } from 'react'

type Step = {
  number: number
  text: string
}

type Props = {
  description: ReactNode  // string から ReactNode に変更
  steps: Step[]
  color: 'blue' | 'purple'
}

function ModeDescription({ description, steps, color }: Props) {
  const colorClass = {
    blue: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      badge: 'bg-blue-600',
      text: 'text-blue-700',
    },
    purple: {
      bg: 'bg-purple-50',
      border: 'border-purple-200',
      badge: 'bg-purple-600',
      text: 'text-purple-700',
    },
  }[color]

  return (
    <div className={`${colorClass.bg} border ${colorClass.border} rounded-xl p-4 mb-6`}>
      <p className={`text-sm ${colorClass.text} mb-3`}>{description}</p>
      <div className="space-y-2">
        {steps.map((step) => (
          <div key={step.number} className="flex items-start gap-3">
            <span className={`${colorClass.badge} text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center flex-shrink-0 mt-0.5`}>
              {step.number}
            </span>
            <p className="text-sm text-gray-700">{step.text}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ModeDescription