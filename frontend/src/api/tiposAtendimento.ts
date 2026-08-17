import { api } from './client'

export interface TipoAtendimento {
  id: number
  nome: string
  descricao: string
  duracao_minutos: number
  ativo: boolean
  criado_em: string
  atualizado_em: string
}

export interface TipoAtendimentoInput {
  nome: string
  descricao: string
  duracao_minutos: number
}

export async function listarTiposAtendimento(): Promise<TipoAtendimento[]> {
  const { data } = await api.get<TipoAtendimento[]>('/tipos-atendimento/')
  return data
}

export async function criarTipoAtendimento(
  payload: TipoAtendimentoInput,
): Promise<TipoAtendimento> {
  const { data } = await api.post<TipoAtendimento>('/tipos-atendimento/', payload)
  return data
}

export async function alternarAtivoTipoAtendimento(
  id: number,
  ativo: boolean,
): Promise<TipoAtendimento> {
  const { data } = await api.patch<TipoAtendimento>(`/tipos-atendimento/${id}/`, { ativo })
  return data
}
