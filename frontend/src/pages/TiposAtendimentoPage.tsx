import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  alternarAtivoTipoAtendimento,
  criarTipoAtendimento,
  listarTiposAtendimento,
  type TipoAtendimentoInput,
} from '../api/tiposAtendimento'
import { extrairErrosDeCampo, type ErrosDeCampo } from '../api/errors'

interface FormState {
  nome: string
  descricao: string
  duracao_minutos: string
}

const FORM_VAZIO: FormState = { nome: '', descricao: '', duracao_minutos: '' }

export function TiposAtendimentoPage() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<FormState>(FORM_VAZIO)
  const [erros, setErros] = useState<ErrosDeCampo>({})

  const tiposQuery = useQuery({ queryKey: ['tipos-atendimento'], queryFn: listarTiposAtendimento })

  const criarMutation = useMutation({
    mutationFn: (payload: TipoAtendimentoInput) => criarTipoAtendimento(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tipos-atendimento'] })
      setForm(FORM_VAZIO)
      setErros({})
    },
    onError: (erro) => setErros(extrairErrosDeCampo(erro)),
  })

  const alternarAtivoMutation = useMutation({
    mutationFn: ({ id, ativo }: { id: number; ativo: boolean }) =>
      alternarAtivoTipoAtendimento(id, ativo),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tipos-atendimento'] }),
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const duracao = Number(form.duracao_minutos)

    if (!duracao || duracao <= 0) {
      setErros({ duracao_minutos: ['Duracao deve ser maior que zero.'] })
      return
    }

    criarMutation.mutate({
      nome: form.nome,
      descricao: form.descricao,
      duracao_minutos: duracao,
    })
  }

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold text-slate-800">Tipos de Atendimento</h1>

      <form
        onSubmit={handleSubmit}
        className="grid grid-cols-1 gap-4 rounded-lg border border-slate-200 bg-white p-6 sm:grid-cols-2"
      >
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Nome</span>
          <input
            type="text"
            value={form.nome}
            onChange={(e) => setForm({ ...form, nome: e.target.value })}
            required
            className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 ${
              erros.nome ? 'border-red-400' : 'border-slate-300'
            }`}
          />
          {erros.nome && <span className="mt-1 block text-xs text-red-600">{erros.nome[0]}</span>}
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Duracao (minutos)</span>
          <input
            type="number"
            min={1}
            value={form.duracao_minutos}
            onChange={(e) => setForm({ ...form, duracao_minutos: e.target.value })}
            required
            className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 ${
              erros.duracao_minutos ? 'border-red-400' : 'border-slate-300'
            }`}
          />
          {erros.duracao_minutos && (
            <span className="mt-1 block text-xs text-red-600">{erros.duracao_minutos[0]}</span>
          )}
        </label>

        <div className="sm:col-span-2">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Descricao</span>
            <input
              type="text"
              value={form.descricao}
              onChange={(e) => setForm({ ...form, descricao: e.target.value })}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </label>
        </div>

        {erros.nao_campo && (
          <p className="sm:col-span-2 text-sm text-red-600">{erros.nao_campo[0]}</p>
        )}

        <div className="sm:col-span-2">
          <button
            type="submit"
            disabled={criarMutation.isPending}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {criarMutation.isPending ? 'Salvando...' : 'Cadastrar tipo de atendimento'}
          </button>
        </div>
      </form>

      <ListaTipos
        query={tiposQuery}
        onAlternarAtivo={(id, ativo) => alternarAtivoMutation.mutate({ id, ativo })}
      />
    </div>
  )
}

function ListaTipos({
  query,
  onAlternarAtivo,
}: {
  query: ReturnType<typeof useQuery<Awaited<ReturnType<typeof listarTiposAtendimento>>>>
  onAlternarAtivo: (id: number, ativo: boolean) => void
}) {
  if (query.isLoading) {
    return <p className="text-sm text-slate-500">Carregando tipos de atendimento...</p>
  }

  if (query.isError) {
    return <p className="text-sm text-red-600">Nao foi possivel carregar os tipos de atendimento.</p>
  }

  const tipos = query.data ?? []

  if (tipos.length === 0) {
    return <p className="text-sm text-slate-500">Nenhum tipo de atendimento cadastrado ainda.</p>
  }

  return (
    <table className="w-full overflow-hidden rounded-lg border border-slate-200 bg-white text-sm">
      <thead className="bg-slate-50 text-left text-slate-600">
        <tr>
          <th className="px-4 py-2">Nome</th>
          <th className="px-4 py-2">Duracao</th>
          <th className="px-4 py-2">Descricao</th>
          <th className="px-4 py-2">Status</th>
          <th className="px-4 py-2" />
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100">
        {tipos.map((tipo) => (
          <tr key={tipo.id}>
            <td className="px-4 py-2">{tipo.nome}</td>
            <td className="px-4 py-2">{tipo.duracao_minutos} min</td>
            <td className="px-4 py-2 text-slate-500">{tipo.descricao || '-'}</td>
            <td className="px-4 py-2">
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  tipo.ativo ? 'bg-green-100 text-green-700' : 'bg-slate-200 text-slate-600'
                }`}
              >
                {tipo.ativo ? 'Ativo' : 'Inativo'}
              </span>
            </td>
            <td className="px-4 py-2 text-right">
              <button
                onClick={() => {
                  if (tipo.ativo && !confirm(`Desativar o tipo de atendimento "${tipo.nome}"?`)) {
                    return
                  }
                  onAlternarAtivo(tipo.id, !tipo.ativo)
                }}
                className="text-xs font-medium text-slate-600 underline hover:text-slate-900"
              >
                {tipo.ativo ? 'Desativar' : 'Reativar'}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
