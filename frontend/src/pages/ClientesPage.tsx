import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  alternarAtivoCliente,
  criarCliente,
  listarClientes,
  type ClienteInput,
} from '../api/clientes'
import { extrairErrosDeCampo, type ErrosDeCampo } from '../api/errors'

const FORM_VAZIO: ClienteInput = { nome: '', documento: '', telefone: '', email: '' }

export function ClientesPage() {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<ClienteInput>(FORM_VAZIO)
  const [erros, setErros] = useState<ErrosDeCampo>({})

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

  const alternarAtivoMutation = useMutation({
    mutationFn: ({ id, ativo }: { id: number; ativo: boolean }) =>
      alternarAtivoCliente(id, ativo),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['clientes'] }),
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    criarMutation.mutate(form)
  }

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

        <div className="sm:col-span-2">
          <button
            type="submit"
            disabled={criarMutation.isPending}
            className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {criarMutation.isPending ? 'Salvando...' : 'Cadastrar cliente'}
          </button>
        </div>
      </form>

      <ListaClientes
        query={clientesQuery}
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
  onAlternarAtivo,
}: {
  query: ReturnType<typeof useQuery<Awaited<ReturnType<typeof listarClientes>>>>
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
          <tr key={cliente.id}>
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
            <td className="px-4 py-2 text-right">
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
