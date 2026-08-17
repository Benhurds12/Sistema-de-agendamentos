import { api } from './client'

export type StatusAtendimento = 'PENDENTE' | 'CANCELADO' | 'NAO_COMPARECEU' | 'REALIZADO'

export interface Atendimento {
  id: number
  cliente: number
  cliente_nome: string
  local: number
  local_nome: string
  tipo: number
  tipo_nome: string
  horario: number
  data_hora: string
  motivo: string
  descricao: string
  status: StatusAtendimento
  status_display: string
  transicoes_permitidas: StatusAtendimento[]
  criado_em: string
}

export interface AtendimentoInput {
  cliente: number
  local: number
  tipo: number
  horario: number
  descricao?: string
}

export async function criarAtendimento(payload: AtendimentoInput): Promise<Atendimento> {
  const { data } = await api.post<Atendimento>('/atendimentos/', payload)
  return data
}
