import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  alternarAtivoCliente,
  atualizarCliente,
  criarCliente,
  listarClientes,
  type Cliente,
  type ClienteInput,
} from '../api/clientes'
import { extrairErrosDeCampo, type ErrosDeCampo } from '../api/errors'

const FORM_VAZIO: ClienteInput = { nome: '', documento: '', telefone: '', email: '' }

export function ClientesPage() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<ClienteInput>(FORM_VAZIO)
  const [erros, setErros] = useState<ErrosDeCampo>({})
  const [editandoId, setEditandoId] = useState<number | null>(null)

  const clientesQuery = useQuery({ queryKey: ['clientes'], queryFn: listarClientes })

  const criarMutation = useMutation({
    mutationFn: criarCliente,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clientes'] })
      setForm(FORM_VAZIO)
      setErros({})
    },
    onError: (erro) => setErros(extrairErrosDeCampo(erro)),
  })

  const atualizarMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: ClienteInput }) =>
      atualizarCliente(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clientes'] })
      setForm(FORM_VAZIO)
      setErros({})
      setEditandoId(null)
    },
    onError: (erro) => setErros(extrairErrosDeCampo(erro)),
  })

  const alternarAtivoMutation = useMutation({
    mutationFn: ({ id, ativo }: { id: number; ativo: boolean }) =>
      alternarAtivoCliente(id, ativo),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['clientes'] }),
  })

  function iniciarEdicao(cliente: Cliente) {
    setEditandoId(cliente.id)
    setErros({})
    setForm({
      nome: cliente.nome,
      documento: cliente.documento,
      telefone: cliente.telefone,
      email: cliente.email,
    })
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
      <h1 className="text-xl font-semibold text-slate-800">Clientes</h1>

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
          label="Documento (CPF ou CNPJ)"
          value={form.documento}
          erro={erros.documento?.[0]}
          onChange={(v) => setForm({ ...form, documento: v })}
        />
        <Campo
          label="Telefone"
          value={form.telefone}
          erro={erros.telefone?.[0]}
          onChange={(v) => setForm({ ...form, telefone: v })}
        />
        <Campo
          label="E-mail"
          type="email"
          value={form.email}
          erro={erros.email?.[0]}
          onChange={(v) => setForm({ ...form, email: v })}
        />

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
                : 'Cadastrar cliente'}
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

      <ListaClientes
        query={clientesQuery}
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
  type = 'text',
}: {
  label: string
  value: string
  erro?: string
  onChange: (value: string) => void
  type?: string
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium text-slate-700">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
        className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 ${
          erro ? 'border-red-400' : 'border-slate-300'
        }`}
      />
      {erro && <span className="mt-1 block text-xs text-red-600">{erro}</span>}
    </label>
  )
}

function ListaClientes({
  query,
  editandoId,
  onEditar,
  onAlternarAtivo,
}: {
  query: ReturnType<typeof useQuery<Awaited<ReturnType<typeof listarClientes>>>>
  editandoId: number | null
  onEditar: (cliente: Cliente) => void
  onAlternarAtivo: (id: number, ativo: boolean) => void
}) {
  if (query.isLoading) {
    return <p className="text-sm text-slate-500">Carregando clientes...</p>
  }

  if (query.isError) {
    return <p className="text-sm text-red-600">Nao foi possivel carregar os clientes.</p>
  }

  const clientes = query.data ?? []

  if (clientes.length === 0) {
    return <p className="text-sm text-slate-500">Nenhum cliente cadastrado ainda.</p>
  }

  return (
    <table className="w-full overflow-hidden rounded-lg border border-slate-200 bg-white text-sm">
      <thead className="bg-slate-50 text-left text-slate-600">
        <tr>
          <th className="px-4 py-2">Nome</th>
          <th className="px-4 py-2">Documento</th>
          <th className="px-4 py-2">Telefone</th>
          <th className="px-4 py-2">E-mail</th>
          <th className="px-4 py-2">Status</th>
          <th className="px-4 py-2" />
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100">
        {clientes.map((cliente) => (
          <tr key={cliente.id} className={editandoId === cliente.id ? 'bg-slate-50' : undefined}>
            <td className="px-4 py-2">{cliente.nome}</td>
            <td className="px-4 py-2">{cliente.documento}</td>
            <td className="px-4 py-2">{cliente.telefone}</td>
            <td className="px-4 py-2">{cliente.email}</td>
            <td className="px-4 py-2">
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  cliente.ativo ? 'bg-green-100 text-green-700' : 'bg-slate-200 text-slate-600'
                }`}
              >
                {cliente.ativo ? 'Ativo' : 'Inativo'}
              </span>
            </td>
            <td className="px-4 py-2 text-right space-x-3 whitespace-nowrap">
              <button
                onClick={() => onEditar(cliente)}
                className="text-xs font-medium text-slate-600 underline hover:text-slate-900"
              >
                Editar
              </button>
              <button
                onClick={() => {
                  if (cliente.ativo && !confirm(`Desativar o cliente "${cliente.nome}"?`)) {
                    return
                  }
                  onAlternarAtivo(cliente.id, !cliente.ativo)
                }}
                className="text-xs font-medium text-slate-600 underline hover:text-slate-900"
              >
                {cliente.ativo ? 'Desativar' : 'Reativar'}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
