import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { listarClientes } from '../api/clientes'
import { listarLocais } from '../api/locais'
import { listarTiposAtendimento } from '../api/tiposAtendimento'
import {
  listarDatasDisponiveis,
  listarHorariosDisponiveis,
  type HorarioDisponivel,
} from '../api/horarios'
import { criarAtendimento } from '../api/atendimentos'
import { extrairErrosDeCampo, type ErrosDeCampo } from '../api/errors'

function formatarData(dataISO: string): string {
  const [ano, mes, dia] = dataISO.split('-')
  return `${dia}/${mes}/${ano}`
}

function formatarHora(horarioISO: string): string {
  return new Date(horarioISO).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function NovoAgendamentoPage() {
  const queryClient = useQueryClient()

  const [clienteId, setClienteId] = useState('')
  const [tipoId, setTipoId] = useState('')
  const [localId, setLocalId] = useState('')
  const [data, setData] = useState('')
  const [horarioId, setHorarioId] = useState('')
  const [descricao, setDescricao] = useState('')

  const [erros, setErros] = useState<ErrosDeCampo>({})
  const [sucesso, setSucesso] = useState(false)

  const clientesQuery = useQuery({ queryKey: ['clientes'], queryFn: listarClientes })
  const locaisQuery = useQuery({ queryKey: ['locais'], queryFn: listarLocais })
  const tiposQuery = useQuery({ queryKey: ['tipos-atendimento'], queryFn: listarTiposAtendimento })

  const datasQuery = useQuery({
    queryKey: ['datas-disponiveis', localId],
    queryFn: () => listarDatasDisponiveis(Number(localId)),
    enabled: localId !== '',
  })

  const horariosQuery = useQuery({
    queryKey: ['horarios-disponiveis', localId, data],
    queryFn: () => listarHorariosDisponiveis(Number(localId), data),
    enabled: localId !== '' && data !== '',
  })

  const criarMutation = useMutation({
    mutationFn: criarAtendimento,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['atendimentos'] })
      setSucesso(true)
      setErros({})
      setClienteId('')
      setTipoId('')
      setLocalId('')
      setData('')
      setHorarioId('')
      setDescricao('')
    },
    onError: (erro) => {
      setSucesso(false)
      setErros(extrairErrosDeCampo(erro))
    },
  })

  function handleLocalChange(novoLocalId: string) {
    setLocalId(novoLocalId)
    setData('')
    setHorarioId('')
  }

  function handleDataChange(novaData: string) {
    setData(novaData)
    setHorarioId('')
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSucesso(false)

    if (!clienteId || !tipoId || !localId || !horarioId) {
      setErros({ nao_campo: ['Preencha todos os campos obrigatorios.'] })
      return
    }

    criarMutation.mutate({
      cliente: Number(clienteId),
      local: Number(localId),
      tipo: Number(tipoId),
      horario: Number(horarioId),
      descricao,
    })
  }

  const clientesAtivos = (clientesQuery.data ?? []).filter((c) => c.ativo)
  const locaisAtivos = (locaisQuery.data ?? []).filter((l) => l.ativo)
  const tiposAtivos = (tiposQuery.data ?? []).filter((t) => t.ativo)
  const datas = datasQuery.data ?? []
  const horarios = horariosQuery.data ?? []

  return (
    <div className="max-w-xl space-y-6">
      <h1 className="text-xl font-semibold text-slate-800">Novo Agendamento</h1>

      <form
        onSubmit={handleSubmit}
        className="space-y-5 rounded-lg border border-slate-200 bg-white p-6"
      >
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Cliente</span>
          <select
            value={clienteId}
            onChange={(e) => setClienteId(e.target.value)}
            required
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
          >
            <option value="" disabled>
              {clientesQuery.isLoading ? 'Carregando clientes...' : 'Selecione um cliente'}
            </option>
            {clientesAtivos.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nome}
              </option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Tipo de atendimento</span>
          <select
            value={tipoId}
            onChange={(e) => setTipoId(e.target.value)}
            required
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
          >
            <option value="" disabled>
              {tiposQuery.isLoading ? 'Carregando tipos...' : 'Selecione um tipo'}
            </option>
            {tiposAtivos.map((t) => (
              <option key={t.id} value={t.id}>
                {t.nome} ({t.duracao_minutos} min)
              </option>
            ))}
          </select>
        </label>

        {/* Passo 1: local */}
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">1. Local</span>
          <select
            value={localId}
            onChange={(e) => handleLocalChange(e.target.value)}
            required
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
          >
            <option value="" disabled>
              {locaisQuery.isLoading ? 'Carregando locais...' : 'Selecione um local'}
            </option>
            {locaisAtivos.map((l) => (
              <option key={l.id} value={l.id}>
                {l.nome}
              </option>
            ))}
          </select>
        </label>

        {/* Passo 2: data, so aparece apos escolher local */}
        {localId && (
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">2. Data</span>
            {datasQuery.isLoading ? (
              <p className="text-sm text-slate-500">Carregando datas disponiveis...</p>
            ) : datas.length === 0 ? (
              <p className="text-sm text-amber-600">
                Nenhuma data com horario disponivel para este local.
              </p>
            ) : (
              <select
                value={data}
                onChange={(e) => handleDataChange(e.target.value)}
                required
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
              >
                <option value="" disabled>
                  Selecione uma data
                </option>
                {datas.map((d) => (
                  <option key={d.data} value={d.data}>
                    {formatarData(d.data)} ({d.total_horarios} horario
                    {d.total_horarios > 1 ? 's' : ''} disponivel
                    {d.total_horarios > 1 ? 'is' : ''})
                  </option>
                ))}
              </select>
            )}
          </label>
        )}

        {/* Passo 3: horario, so aparece apos escolher data */}
        {localId && data && (
          <fieldset className="block text-sm">
            <legend className="mb-2 font-medium text-slate-700">3. Horario</legend>
            {horariosQuery.isLoading ? (
              <p className="text-sm text-slate-500">Carregando horarios disponiveis...</p>
            ) : horarios.length === 0 ? (
              <p className="text-sm text-amber-600">Nenhum horario disponivel nesta data.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {horarios.map((h: HorarioDisponivel) => (
                  <button
                    key={h.id}
                    type="button"
                    onClick={() => setHorarioId(String(h.id))}
                    className={`rounded-md border px-3 py-1.5 text-sm font-medium transition-colors ${
                      horarioId === String(h.id)
                        ? 'border-slate-900 bg-slate-900 text-white'
                        : 'border-slate-300 text-slate-700 hover:border-slate-400'
                    }`}
                  >
                    {formatarHora(h.inicio)}
                  </button>
                ))}
              </div>
            )}
          </fieldset>
        )}

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Observacoes (opcional)</span>
          <textarea
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            rows={2}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
        </label>

        {erros.nao_campo && <p className="text-sm text-red-600">{erros.nao_campo[0]}</p>}
        {erros.horario && <p className="text-sm text-red-600">{erros.horario[0]}</p>}
        {erros.cliente && <p className="text-sm text-red-600">{erros.cliente[0]}</p>}
        {erros.tipo && <p className="text-sm text-red-600">{erros.tipo[0]}</p>}

        {sucesso && (
          <p className="rounded-md bg-green-50 px-3 py-2 text-sm font-medium text-green-700">
            Agendamento criado com sucesso.
          </p>
        )}

        <button
          type="submit"
          disabled={criarMutation.isPending || !horarioId}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {criarMutation.isPending ? 'Agendando...' : 'Confirmar agendamento'}
        </button>
      </form>
    </div>
  )
}
