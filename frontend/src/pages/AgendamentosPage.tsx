import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  alterarStatusAtendimento,
  buscarIndicadores,
  listarAtendimentos,
  type Atendimento,
  type FiltrosAtendimento,
  type StatusAtendimento,
} from '../api/atendimentos'
import { listarLocais } from '../api/locais'
import { listarTiposAtendimento } from '../api/tiposAtendimento'
import { StatusBadge } from '../components/StatusBadge'
import { AtendimentoModal } from '../components/AtendimentoModal'

const OPCOES_STATUS: { value: StatusAtendimento; label: string }[] = [
  { value: 'PENDENTE', label: 'Pendente' },
  { value: 'REALIZADO', label: 'Realizado' },
  { value: 'CANCELADO', label: 'Cancelado' },
  { value: 'NAO_COMPARECEU', label: 'Nao compareceu' },
]

const FILTROS_VAZIOS: FiltrosAtendimento = { status: '', local: '', tipo: '', cliente_nome: '' }

function formatarDataHora(iso: string): string {
  return new Date(iso).toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function AgendamentosPage() {
  const queryClient = useQueryClient()
  const [filtros, setFiltros] = useState<FiltrosAtendimento>(FILTROS_VAZIOS)
  const [atendimentoSelecionado, setAtendimentoSelecionado] = useState<Atendimento | null>(null)

  const locaisQuery = useQuery({ queryKey: ['locais'], queryFn: listarLocais })
  const tiposQuery = useQuery({ queryKey: ['tipos-atendimento'], queryFn: listarTiposAtendimento })

  const atendimentosQuery = useQuery({
    queryKey: ['atendimentos', filtros],
    queryFn: () => listarAtendimentos(filtros),
  })

  const indicadoresQuery = useQuery({
    queryKey: ['indicadores', filtros],
    queryFn: () => buscarIndicadores(filtros),
  })

  const alterarStatusMutation = useMutation({
    mutationFn: ({
      id,
      status,
      motivo,
      descricao,
    }: {
      id: number
      status: StatusAtendimento
      motivo?: string
      descricao?: string
    }) => alterarStatusAtendimento(id, { status, motivo, descricao }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['atendimentos'] })
      queryClient.invalidateQueries({ queryKey: ['indicadores'] })
      setAtendimentoSelecionado(null)
    },
  })

  const atendimentos = atendimentosQuery.data ?? []
  const indicadores = indicadoresQuery.data
  const locaisAtivos = (locaisQuery.data ?? []).filter((l) => l.ativo)
  const tiposAtivos = (tiposQuery.data ?? []).filter((t) => t.ativo)

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-slate-800">Agendamentos</h1>

      {/* Cards de indicadores */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <CardIndicador titulo="Total" valor={indicadores?.total} carregando={indicadoresQuery.isLoading} />
        <CardIndicador
          titulo="Pendentes"
          valor={indicadores?.pendentes}
          carregando={indicadoresQuery.isLoading}
          cor="text-amber-600"
        />
        <CardIndicador
          titulo="Realizados"
          valor={indicadores?.realizados}
          carregando={indicadoresQuery.isLoading}
          cor="text-green-600"
        />
        <CardIndicador
          titulo="Cancelados"
          valor={indicadores?.cancelados}
          carregando={indicadoresQuery.isLoading}
          cor="text-red-600"
        />
      </div>

      {/* Filtros */}
      <div className="flex flex-wrap gap-3 rounded-lg border border-slate-200 bg-white p-4">
        <select
          value={filtros.status}
          onChange={(e) => setFiltros({ ...filtros, status: e.target.value })}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        >
          <option value="">Todos os status</option>
          {OPCOES_STATUS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>

        <select
          value={filtros.local}
          onChange={(e) => setFiltros({ ...filtros, local: e.target.value })}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        >
          <option value="">Todos os locais</option>
          {locaisAtivos.map((l) => (
            <option key={l.id} value={l.id}>
              {l.nome}
            </option>
          ))}
        </select>

        <select
          value={filtros.tipo}
          onChange={(e) => setFiltros({ ...filtros, tipo: e.target.value })}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        >
          <option value="">Todos os tipos</option>
          {tiposAtivos.map((t) => (
            <option key={t.id} value={t.id}>
              {t.nome}
            </option>
          ))}
        </select>

        <input
          type="text"
          placeholder="Buscar por nome do cliente..."
          value={filtros.cliente_nome}
          onChange={(e) => setFiltros({ ...filtros, cliente_nome: e.target.value })}
          className="min-w-48 flex-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        />

        {(filtros.status || filtros.local || filtros.tipo || filtros.cliente_nome) && (
          <button
            type="button"
            onClick={() => setFiltros(FILTROS_VAZIOS)}
            className="text-sm text-slate-500 underline hover:text-slate-800"
          >
            Limpar filtros
          </button>
        )}
      </div>

      {/* Tabela */}
      {atendimentosQuery.isLoading ? (
        <p className="text-sm text-slate-500">Carregando agendamentos...</p>
      ) : atendimentosQuery.isError ? (
        <p className="text-sm text-red-600">Nao foi possivel carregar os agendamentos.</p>
      ) : atendimentos.length === 0 ? (
        <p className="text-sm text-slate-500">Nenhum agendamento encontrado.</p>
      ) : (
        <table className="w-full overflow-hidden rounded-lg border border-slate-200 bg-white text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-4 py-2">Cliente</th>
              <th className="px-4 py-2">Local</th>
              <th className="px-4 py-2">Tipo</th>
              <th className="px-4 py-2">Data/Horario</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {atendimentos.map((atendimento) => (
              <tr key={atendimento.id}>
                <td className="px-4 py-2">{atendimento.cliente_nome}</td>
                <td className="px-4 py-2">{atendimento.local_nome}</td>
                <td className="px-4 py-2">{atendimento.tipo_nome}</td>
                <td className="px-4 py-2">{formatarDataHora(atendimento.data_hora)}</td>
                <td className="px-4 py-2">
                  {atendimento.transicoes_permitidas.length > 0 ? (
                    <select
                      value={atendimento.status}
                      onChange={(e) =>
                        alterarStatusMutation.mutate({
                          id: atendimento.id,
                          status: e.target.value as StatusAtendimento,
                        })
                      }
                      className="rounded-md border border-slate-300 px-2 py-1 text-xs"
                    >
                      <option value={atendimento.status}>{atendimento.status_display}</option>
                      {atendimento.transicoes_permitidas.map((status) => (
                        <option key={status} value={status}>
                          {OPCOES_STATUS.find((o) => o.value === status)?.label ?? status}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <StatusBadge status={atendimento.status} label={atendimento.status_display} />
                  )}
                </td>
                <td className="px-4 py-2 text-right">
                  <button
                    onClick={() => setAtendimentoSelecionado(atendimento)}
                    className="text-xs font-medium text-slate-600 underline hover:text-slate-900"
                  >
                    Detalhes
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {atendimentoSelecionado && (
        <AtendimentoModal
          atendimento={atendimentoSelecionado}
          onClose={() => setAtendimentoSelecionado(null)}
          enviando={alterarStatusMutation.isPending}
          onConfirmar={(status, motivo, descricao) =>
            alterarStatusMutation.mutate({ id: atendimentoSelecionado.id, status, motivo, descricao })
          }
        />
      )}
    </div>
  )
}

function CardIndicador({
  titulo,
  valor,
  carregando,
  cor = 'text-slate-800',
}: {
  titulo: string
  valor?: number
  carregando: boolean
  cor?: string
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-medium text-slate-500">{titulo}</p>
      <p className={`mt-1 text-2xl font-semibold ${cor}`}>{carregando ? '-' : (valor ?? 0)}</p>
    </div>
  )
}
