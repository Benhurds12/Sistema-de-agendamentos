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

export interface FiltrosAtendimento {
  status?: string
  local?: string
  tipo?: string
  cliente_nome?: string
}

function limparFiltrosVazios(filtros: FiltrosAtendimento): Record<string, string> {
  return Object.fromEntries(
    Object.entries(filtros).filter(([, valor]) => valor !== undefined && valor !== ''),
  )
}

export async function listarAtendimentos(filtros: FiltrosAtendimento): Promise<Atendimento[]> {
  const { data } = await api.get<Atendimento[]>('/atendimentos/', {
    params: limparFiltrosVazios(filtros),
  })
  return data
}

export interface Indicadores {
  total: number
  pendentes: number
  realizados: number
  cancelados: number
  nao_compareceram: number
}

export async function buscarIndicadores(filtros: FiltrosAtendimento): Promise<Indicadores> {
  const { data } = await api.get<Indicadores>('/atendimentos/indicadores/', {
    params: limparFiltrosVazios(filtros),
  })
  return data
}

export interface AlterarStatusInput {
  status: StatusAtendimento
  motivo?: string
  descricao?: string
}

export async function alterarStatusAtendimento(
  id: number,
  payload: AlterarStatusInput,
): Promise<Atendimento> {
  const { data } = await api.patch<Atendimento>(`/atendimentos/${id}/status/`, payload)
  return data
}
