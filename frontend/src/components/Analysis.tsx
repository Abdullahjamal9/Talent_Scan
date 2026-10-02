import { Check, CircleDashed, HelpCircle, Sparkles, X } from 'lucide-react'
import type { Analysis } from '../api'
import { cn } from '../lib'

const statusStyle = {
  met: { icon: Check, color: 'text-good', label: 'Met' },
  partial: { icon: CircleDashed, color: 'text-warn', label: 'Partly' },
  missing: { icon: X, color: 'text-bad', label: 'Not shown' },
} as const

/** The AI's reasoning behind a match score: summary, requirement checklist and (for recruiters) interview questions. */
export default function AnalysisPanel({ analysis, className }: { analysis?: Analysis | null; className?: string }) {
  if (!analysis) return null

  const requirements = analysis.requirements?.length
    ? analysis.requirements
    : [
        ...(analysis.strengths ?? []).map((requirement) => ({ requirement, status: 'met' as const })),
        ...(analysis.gaps ?? []).map((requirement) => ({ requirement, status: 'missing' as const })),
      ]

  return (
    <div className={cn('space-y-4', className)}>
      {analysis.summary && (
        <p className="flex gap-2 text-sm leading-relaxed text-ink/90">
          <Sparkles size={15} className="mt-0.5 shrink-0 text-brand" />
          {analysis.summary}
        </p>
      )}

      {requirements.length > 0 && (
        <ul className="space-y-1.5">
          {requirements.map((r, i) => {
            const style = statusStyle[r.status]
            const Icon = style.icon
            return (
              <li key={i} className="flex items-center gap-2.5 text-sm">
                <Icon size={15} className={cn('shrink-0', style.color)} />
                <span className="flex-1 text-ink/90">{r.requirement}</span>
                <span className={cn('text-xs', style.color)}>{style.label}</span>
              </li>
            )
          })}
        </ul>
      )}

      {!!analysis.questions?.length && (
        <div>
          <h4 className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted">
            <HelpCircle size={13} /> Suggested interview questions
          </h4>
          <ol className="list-decimal space-y-1.5 pl-5 text-sm text-ink/90">
            {analysis.questions.map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}
