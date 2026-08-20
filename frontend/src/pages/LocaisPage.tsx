import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  alternarAtivoLocal,
  atualizarLocal,
  criarLocal,
  listarLocais,
  type Local,
  type LocalInput,
} from '../api/locais'
import { extrairErrosDeCampo, type ErrosDeCampo } from '../api/errors'

const FORM_VAZIO: LocalInput = { nome: '', descricao: '', endereco: '' }

export function LocaisPage() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<LocalInput>(FORM_VAZIO)
  const [erros, setErros] = useState<ErrosDeCampo>({})
  const [editandoId, setEditandoId] = useState<number | null>(null)

  const locaisQuery = useQuery({ queryKey: ['locais'], queryFn: listarLocais })

  const criarMutation = useMutation({
    mutationFn: criarLocal,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locais'] })
      setForm(FORM_VAZIO)
      setErros({})
    },
    onError: (erro) => setErros(extrairErrosDeCampo(erro)),
  })

  const atualizarMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: LocalInput }) =>
      atualizarLocal(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locais'] })
      setForm(FORM_VAZIO)
      setErros({})
      setEditandoId(null)
    },
    onError: (erro) => setErros(extrairErrosDeCampo(erro)),
  })

  const alternarAtivoMutation = useMutation({
    mutationFn: ({ id, ativo }: { id: number; ativo: boolean }) => alternarAtivoLocal(id, ativo),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['locais'] }),
  })

  function iniciarEdicao(local: Local) {
    setEditandoId(local.id)
    setErros({})
    setForm({ nome: local.nome, descricao: local.descricao, endereco: local.endereco })
  }

  function cancelarEdicao() {
    setEditandoId(null)
    setErros({})
    setForm(FORM_VAZIO)
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (editandoId !== null) {
      atualizarMutation.mutate({ id: editandoId, payload: form })
    } else {
      criarMutation.mutate(form)
    }
  }

  const salvando = criarMutation.isPending || atualizarMutation.isPending

  return (
    <div className="space-y-8">
      <h1 className="text-xl font-semibold text-slate-800">Locais</h1>

      <form
        onSubmit={handleSubmit}
        className="grid grid-cols-1 gap-4 rounded-lg border border-slate-200 bg-white p-6 sm:grid-cols-2"
      >
        <Campo
          label="Nome"
          value={form.nome}
          erro={erros.nome?.[0]}
          onChange={(v) => setForm({ ...form, nome: v })}
        />
        <Campo
          label="Endereco"
          value={form.endereco}
          erro={erros.endereco?.[0]}
          onChange={(v) => setForm({ ...form, endereco: v })}
        />
        <div className="sm:col-span-2">
          <Campo
            label="Descricao"
            value={form.descricao}
            erro={erros.descricao?.[0]}
            onChange={(v) => setForm({ ...form, descricao: v })}
            obrigatorio={false}
          />
        </div>

        {erros.nao_campo && (
          <p className="sm:col-span-2 text-sm text-red-600">{erros.nao_campo[0]}</p>
        )}

        <div className="flex gap-3 sm:col-span-2">
          <button
            type="submit"
            disabled={salvando}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {salvando
              ? 'Salvando...'
              : editandoId !== null
                ? 'Salvar alteracoes'
                : 'Cadastrar local'}
          </button>
          {editandoId !== null && (
            <button
              type="button"
              onClick={cancelarEdicao}
              className="rounded-md px-4 py-2 text-sm text-slate-600 hover:bg-slate-100"
            >
              Cancelar
            </button>
          )}
        </div>
      </form>

      <ListaLocais
        query={locaisQuery}
        editandoId={editandoId}
        onEditar={iniciarEdicao}
        onAlternarAtivo={(id, ativo) => alternarAtivoMutation.mutate({ id, ativo })}
      />
    </div>
  )
}

function Campo({
  label,
  value,
  erro,
  onChange,
  obrigatorio = true,
}: {
  label: string
  value: string
  erro?: string
  onChange: (value: string) => void
  obrigatorio?: boolean
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium text-slate-700">{label}</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={obrigatorio}
        className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 ${
          erro ? 'border-red-400' : 'border-slate-300'
        }`}
      />
      {erro && <span className="mt-1 block text-xs text-red-600">{erro}</span>}
    </label>
  )
}

function ListaLocais({
  query,
  editandoId,
  onEditar,
  onAlternarAtivo,
}: {
  query: ReturnType<typeof useQuery<Awaited<ReturnType<typeof listarLocais>>>>
  editandoId: number | null
  onEditar: (local: Local) => void
  onAlternarAtivo: (id: number, ativo: boolean) => void
}) {
  if (query.isLoading) {
    return <p className="text-sm text-slate-500">Carregando locais...</p>
  }

  if (query.isError) {
    return <p className="text-sm text-red-600">Nao foi possivel carregar os locais.</p>
  }

  const locais = query.data ?? []

  if (locais.length === 0) {
    return <p className="text-sm text-slate-500">Nenhum local cadastrado ainda.</p>
  }

  return (
    <table className="w-full overflow-hidden rounded-lg border border-slate-200 bg-white text-sm">
      <thead className="bg-slate-50 text-left text-slate-600">
        <tr>
          <th className="px-4 py-2">Nome</th>
          <th className="px-4 py-2">Endereco</th>
          <th className="px-4 py-2">Descricao</th>
          <th className="px-4 py-2">Status</th>
          <th className="px-4 py-2" />
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100">
        {locais.map((local) => (
          <tr key={local.id} className={editandoId === local.id ? 'bg-slate-50' : undefined}>
            <td className="px-4 py-2">{local.nome}</td>
            <td className="px-4 py-2">{local.endereco}</td>
            <td className="px-4 py-2 text-slate-500">{local.descricao || '-'}</td>
            <td className="px-4 py-2">
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  local.ativo ? 'bg-green-100 text-green-700' : 'bg-slate-200 text-slate-600'
                }`}
              >
                {local.ativo ? 'Ativo' : 'Inativo'}
              </span>
            </td>
            <td className="px-4 py-2 text-right space-x-3 whitespace-nowrap">
              <button
                onClick={() => onEditar(local)}
                className="text-xs font-medium text-slate-600 underline hover:text-slate-900"
              >
                Editar
              </button>
              <button
                onClick={() => {
                  if (local.ativo && !confirm(`Desativar o local "${local.nome}"?`)) {
                    return
                  }
                  onAlternarAtivo(local.id, !local.ativo)
                }}
                className="text-xs font-medium text-slate-600 underline hover:text-slate-900"
              >
                {local.ativo ? 'Desativar' : 'Reativar'}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
