import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

const CHAVE_ACCESS = 'agendamento_access_token'
const CHAVE_REFRESH = 'agendamento_refresh_token'

export interface TokensAutenticacao {
  access: string
  refresh: string
}

export async function login(username: string, password: string): Promise<TokensAutenticacao> {
  // Chamada crua com axios (nao a instancia `api`) porque o login nao deve
  // enviar um Authorization header antigo, nem disparar o interceptor de
  // refresh caso essa propria chamada falhe com 401 (credenciais erradas).
  const { data } = await axios.post<TokensAutenticacao>(`${BASE_URL}/auth/token/`, {
    username,
    password,
  })
  salvarTokens(data)
  return data
}

export function salvarTokens(tokens: TokensAutenticacao): void {
  localStorage.setItem(CHAVE_ACCESS, tokens.access)
  localStorage.setItem(CHAVE_REFRESH, tokens.refresh)
}

export function obterAccessToken(): string | null {
  return localStorage.getItem(CHAVE_ACCESS)
}

export function obterRefreshToken(): string | null {
  return localStorage.getItem(CHAVE_REFRESH)
}

export function logout(): void {
  localStorage.removeItem(CHAVE_ACCESS)
  localStorage.removeItem(CHAVE_REFRESH)
}

export function estaAutenticado(): boolean {
  return obterAccessToken() !== null
}

export async function renovarAccessToken(): Promise<string> {
  const refresh = obterRefreshToken()
  if (!refresh) throw new Error('Sem refresh token disponivel.')

  const { data } = await axios.post<{ access: string }>(`${BASE_URL}/auth/token/refresh/`, {
    refresh,
  })
  localStorage.setItem(CHAVE_ACCESS, data.access)
  return data.access
}
