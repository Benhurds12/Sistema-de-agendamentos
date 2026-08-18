import axios, { type InternalAxiosRequestConfig } from 'axios'
import { logout, obterAccessToken, renovarAccessToken } from './auth'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api',
})

api.interceptors.request.use((config) => {
  const token = obterAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

interface ConfigComRetry extends InternalAxiosRequestConfig {
  _jaTentouRenovar?: boolean
}

api.interceptors.response.use(
  (response) => response,
  async (erro) => {
    const config = erro.config as ConfigComRetry

    // Access token expirado: tenta renovar UMA vez com o refresh token e
    // repete a requisicao original. Se falhar de novo (refresh tambem
    // expirado), desloga e manda para o login.
    if (erro.response?.status === 401 && !config._jaTentouRenovar) {
      config._jaTentouRenovar = true
      try {
        const novoToken = await renovarAccessToken()
        config.headers.Authorization = `Bearer ${novoToken}`
        return api(config)
      } catch {
        logout()
        window.location.href = '/login'
      }
    }

    return Promise.reject(erro)
  },
)
