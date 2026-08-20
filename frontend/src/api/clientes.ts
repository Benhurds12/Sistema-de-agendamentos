import { api } from './client'

export interface Cliente {
  id: number
  nome: string
  documento: string
  telefone: string
  email: string
  ativo: boolean
  criado_em: string
  atualizado_em: string
}

export interface ClienteInput {
  nome: string
  documento: string
  telefone: string
  email: string
}

export async function listarClientes(): Promise<Cliente[]> {
  const { data } = await api.get<Cliente[]>('/clientes/')
  return data
}

export async function criarCliente(payload: ClienteInput): Promise<Cliente> {
  const { data } = await api.post<Cliente>('/clientes/', payload)
  return data
}

export async function atualizarCliente(id: number, payload: ClienteInput): Promise<Cliente> {
  const { data } = await api.put<Cliente>(`/clientes/${id}/`, payload)
  return data
}

export async function alternarAtivoCliente(id: number, ativo: boolean): Promise<Cliente> {
  const { data } = await api.patch<Cliente>(`/clientes/${id}/`, { ativo })
  return data
}
