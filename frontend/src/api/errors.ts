import { isAxiosError } from 'axios'

/** Formato padrao de erro do DRF: { campo: ["mensagem", ...] } */
export type ErrosDeCampo = Record<string, string[]>

export function extrairErrosDeCampo(erro: unknown): ErrosDeCampo {
  if (isAxiosError(erro) && erro.response?.data && typeof erro.response.data === 'object') {
    return erro.response.data as ErrosDeCampo
  }
  return { nao_campo: ['Ocorreu um erro inesperado. Tente novamente.'] }
}

export function primeiraMensagemDeErro(erro: unknown): string {
  const erros = extrairErrosDeCampo(erro)
  const primeiraLista = Object.values(erros)[0]
  return primeiraLista?.[0] ?? 'Ocorreu um erro inesperado.'
}
