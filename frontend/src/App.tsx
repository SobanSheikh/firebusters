import { useQuery } from '@tanstack/react-query'

import { api } from './lib/api'

type Health = {
  api: string
  database: string
  status: string
}

const pillars = [
  ['Prevent', 'Material flammability and flame spread'],
  ['Detect', 'Smoke behavior and detector response'],
  ['Suppress', 'Extinction limits and suppressant evidence'],
  ['Understand', 'Traceable NASA findings and research gaps'],
]

export default function App() {
  const health = useQuery({
    queryKey: ['health'],
    queryFn: async () => (await api.get<Health>('/health')).data,
  })

  return (
    <main className="min-h-screen bg-[#070b14] px-6 py-10 text-slate-100 sm:px-10 lg:px-16">
      <div className="mx-auto max-w-6xl">
        <nav className="flex items-center justify-between border-b border-white/10 pb-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-orange-400">
              Fire Fire Busters
            </p>
            <p className="mt-1 text-lg font-semibold">FlameLens</p>
          </div>
          <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300">
            API: {health.isLoading ? 'checking' : health.data?.status ?? 'offline'}
          </span>
        </nav>

        <section className="py-20 sm:py-28">
          <p className="mb-4 text-sm font-medium text-orange-400">NASA combustion evidence, made usable</p>
          <h1 className="max-w-4xl text-5xl font-semibold leading-[1.05] tracking-tight sm:text-7xl">
            Clear fire-safety answers, with every claim tied to evidence.
          </h1>
          <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-400">
            Find, compare and extract insights from NASA microgravity combustion investigations—without losing experimental context, units or limitations.
          </p>
        </section>

        <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {pillars.map(([title, description]) => (
            <article key={title} className="rounded-2xl border border-white/10 bg-white/[0.035] p-6">
              <div className="mb-8 h-1 w-10 rounded-full bg-gradient-to-r from-orange-500 to-amber-300" />
              <h2 className="text-xl font-semibold">{title}</h2>
              <p className="mt-3 text-sm leading-6 text-slate-400">{description}</p>
            </article>
          ))}
        </section>
      </div>
    </main>
  )
}
