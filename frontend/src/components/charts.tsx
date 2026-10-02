import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { FunnelStep } from '../api'
import { scoreColor, stageMeta } from '../lib'

const axis = { stroke: '#5d6377', fontSize: 11, tickLine: false, axisLine: false } as const

const tooltipStyle = {
  contentStyle: { background: '#181b25', border: '1px solid #242836', borderRadius: 8, fontSize: 12, color: '#e8eaf0' },
  labelStyle: { color: '#8a90a2' },
  cursor: { stroke: '#242836' },
}

/** Circular score indicator (0-100) */
export function ScoreRing({ score, size = 44 }: { score: number | null | undefined; size?: number }) {
  const stroke = 4
  const r = (size - stroke) / 2
  const circumference = 2 * Math.PI * r
  const value = score ?? 0
  const color = score == null ? '#242836' : scoreColor(value)
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }} title={score == null ? 'Not scored' : `AI match ${Math.round(value)}%`}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#242836" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - value / 100)}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[11px] font-semibold text-ink">
        {score == null ? '-' : Math.round(value)}
      </span>
    </div>
  )
}

/** Horizontal funnel: one bar per pipeline stage, relative to the biggest stage */
export function Funnel({ steps }: { steps: FunnelStep[] }) {
  const max = Math.max(1, ...steps.map((s) => s.count))
  return (
    <div className="space-y-3">
      {steps.map((s) => {
        const meta = stageMeta(s.stage)
        return (
          <div key={s.stage}>
            <div className="mb-1 flex justify-between text-xs">
              <span className="text-muted">{meta.label}</span>
              <span className="font-medium text-ink">{s.count}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-raised">
              <div className="h-full rounded-full transition-all" style={{ width: `${(s.count / max) * 100}%`, background: meta.color }} />
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function TrendChart({ data }: { data: { date: string; count: number }[] }) {
  const rows = data.map((d) => ({ ...d, label: new Date(d.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) }))
  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={rows} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
        <defs>
          <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#7c6cf0" stopOpacity={0.45} />
            <stop offset="100%" stopColor="#7c6cf0" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#242836" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" {...axis} interval="preserveStartEnd" />
        <YAxis {...axis} allowDecimals={false} />
        <Tooltip {...tooltipStyle} formatter={(v) => [v, 'Applications']} />
        <Area type="monotone" dataKey="count" stroke="#7c6cf0" strokeWidth={2} fill="url(#trendFill)" />
      </AreaChart>
    </ResponsiveContainer>
  )
}

const BUCKET_COLORS = ['#f87171', '#fbbf24', '#38bdf8', '#34d399']

export function ScoreDistribution({ data }: { data: { label: string; count: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -24, bottom: 0 }}>
        <CartesianGrid stroke="#242836" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" {...axis} />
        <YAxis {...axis} allowDecimals={false} />
        <Tooltip {...tooltipStyle} cursor={{ fill: '#ffffff08' }} formatter={(v) => [v, 'Candidates']} />
        <Bar dataKey="count" radius={[6, 6, 0, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={BUCKET_COLORS[i % BUCKET_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
