import type { StatusAtendimento } from '../api/atendimentos'

const CORES: Record<StatusAtendimento, string> = {
  PENDENTE: 'bg-amber-100 text-amber-700',
  REALIZADO: 'bg-green-100 text-green-700',
  CANCELADO: 'bg-red-100 text-red-700',
  NAO_COMPARECEU: 'bg-slate-200 text-slate-600',
}

export function StatusBadge({ status, label }: { status: StatusAtendimento; label: string }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${CORES[status]}`}>
      {label}
    </span>
  )
}
