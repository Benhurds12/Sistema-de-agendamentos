import { useState } from 'react'
import type { Atendimento, StatusAtendimento } from '../api/atendimentos'
import { StatusBadge } from './StatusBadge'

const LABELS: Record<StatusAtendimento, string> = {
  PENDENTE: 'Pendente',
  REALIZADO: 'Realizado',
  CANCELADO: 'Cancelado',
  NAO_COMPARECEU: 'Nao compareceu',
}

function formatarDataHora(iso: string): string {
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function AtendimentoModal({
  atendimento,
  onClose,
  onConfirmar,
  enviando,
}: {
  atendimento: Atendimento
  onClose: () => void
  onConfirmar: (status: StatusAtendimento, motivo: string, descricao: string) => void
  enviando: boolean
}) {
  const [novoStatus, setNovoStatus] = useState<StatusAtendimento | ''>('')
  const [motivo, setMotivo] = useState('')
  const [descricao, setDescricao] = useState('')

  const podeAlterar = atendimento.transicoes_permitidas.length > 0

  function handleConfirmar() {
    if (!novoStatus) return
    onConfirmar(novoStatus, motivo, descricao)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <div className="mb-4 flex items-start justify-between">
          <h2 className="text-lg font-semibold text-slate-800">Detalhes do agendamento</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            ✕
          </button>
        </div>

        <dl className="mb-6 space-y-2 text-sm">
          <Linha rotulo="Cliente" valor={atendimento.cliente_nome} />
          <Linha rotulo="Local" valor={atendimento.local_nome} />
          <Linha rotulo="Tipo" valor={atendimento.tipo_nome} />
          <Linha rotulo="Data e horario" valor={formatarDataHora(atendimento.data_hora)} />
          <div className="flex items-center justify-between">
            <dt className="text-slate-500">Status atual</dt>
            <dd>
              <StatusBadge status={atendimento.status} label={atendimento.status_display} />
            </dd>
          </div>
          {atendimento.descricao && <Linha rotulo="Observacoes/relatorio" valor={atendimento.descricao} />}
          {atendimento.motivo && <Linha rotulo="Motivo do cancelamento" valor={atendimento.motivo} />}
        </dl>

        {podeAlterar ? (
          <div className="space-y-3 border-t border-slate-200 pt-4">
            <label className="block text-sm">
              <span className="mb-1 block font-medium text-slate-700">Alterar status para</span>
              <select
                value={novoStatus}
                onChange={(e) => setNovoStatus(e.target.value as StatusAtendimento)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
              >
                <option value="" disabled>
                  Selecione...
                </option>
                {atendimento.transicoes_permitidas.map((status) => (
                  <option key={status} value={status}>
                    {LABELS[status]}
                  </option>
                ))}
              </select>
              <span className="mt-1 block text-xs text-slate-500">
                Ao escolher "Cancelado" ou "Realizado", um campo para detalhar o motivo ou o
                relatório do atendimento aparece aqui embaixo.
              </span>
            </label>

            {novoStatus === 'CANCELADO' && (
              <label className="block text-sm">
                <span className="mb-1 block font-medium text-slate-700">
                  Motivo do cancelamento (opcional)
                </span>
                <textarea
                  value={motivo}
                  onChange={(e) => setMotivo(e.target.value)}
                  rows={2}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
                />
              </label>
            )}

            {novoStatus === 'REALIZADO' && (
              <label className="block text-sm">
                <span className="mb-1 block font-medium text-slate-700">
                  Relatorio do atendimento (opcional)
                </span>
                <textarea
                  value={descricao}
                  onChange={(e) => setDescricao(e.target.value)}
                  rows={2}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
                />
              </label>
            )}

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-md px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
              >
                Fechar
              </button>
              <button
                type="button"
                onClick={handleConfirmar}
                disabled={!novoStatus || enviando}
                className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
              >
                {enviando ? 'Salvando...' : 'Confirmar alteracao'}
              </button>
            </div>
          </div>
        ) : (
          <div className="border-t border-slate-200 pt-4">
            <p className="text-sm text-slate-500">
              Este atendimento esta em status final e nao pode mais ser alterado.
            </p>
            <div className="mt-3 flex justify-end">
              <button
                type="button"
                onClick={onClose}
                className="rounded-md px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100"
              >
                Fechar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function Linha({ rotulo, valor }: { rotulo: string; valor: string }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <dt className="shrink-0 text-slate-500">{rotulo}</dt>
      <dd className="text-right text-slate-800">{valor}</dd>
    </div>
  )
}
