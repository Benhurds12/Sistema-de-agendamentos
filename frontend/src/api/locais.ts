import { api } from './client'

export interface Local {
  id: number
  nome: string
  descricao: string
  endereco: string
  ativo: boolean
  criado_em: string
  atualizado_em: string
}

export interface LocalInput {
  nome: string
  descricao: string
  endereco: string
}

export async function listarLocais(): Promise<Local[]> {
  const { data } = await api.get<Local[]>('/locais/')
  return data
}

export async function criarLocal(payload: LocalInput): Promise<Local> {
  const { data } = await api.post<Local>('/locais/', payload)
  return data
}

export async function atualizarLocal(id: number, payload: LocalInput): Promise<Local> {
  const { data } = await api.put<Local>(`/locais/${id}/`, payload)
  return data
}

export async function alternarAtivoLocal(id: number, ativo: boolean): Promise<Local> {
  const { data } = await api.patch<Local>(`/locais/${id}/`, { ativo })
  return data
}
