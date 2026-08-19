import { api } from './client'

export interface GerarGradeInput {
  local: number
  inicio: string
  fim: string
  duracao_minutos: number
  apenas_dias_uteis?: boolean
}

export interface GerarGradeResultado {
  criadas: number
  mensagem: string
}

export async function gerarGrade(payload: GerarGradeInput): Promise<GerarGradeResultado> {
  const { data } = await api.post<GerarGradeResultado>('/horarios/gerar-grade/', payload)
  return data
}

export interface DataDisponivel {
  data: string
  total_horarios: number
}

export async function listarDatasDisponiveis(localId: number): Promise<DataDisponivel[]> {
  const { data } = await api.get<DataDisponivel[]>('/horarios/datas-disponiveis/', {
    params: { local: localId },
  })
  return data
}

export interface HorarioDisponivel {
  id: number
  local: number
  local_nome: string
  inicio: string
  fim: string
  disponivel: boolean
}

export async function listarHorariosDisponiveis(
  localId: number,
  data: string,
): Promise<HorarioDisponivel[]> {
  const { data: resposta } = await api.get<HorarioDisponivel[]>('/horarios/horarios-disponiveis/', {
    params: { local: localId, data },
  })
  return resposta
}
