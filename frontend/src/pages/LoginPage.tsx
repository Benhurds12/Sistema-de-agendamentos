import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { isAxiosError } from 'axios'
import { login } from '../api/auth'

export function LoginPage() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await login(username, password)
      navigate('/agendamentos', { replace: true })
    } catch (e) {
      const mensagem = isAxiosError(e)
        ? 'Usuario ou senha invalidos.'
        : 'Nao foi possivel conectar ao servidor.'
      setErro(mensagem)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-lg border border-slate-200 bg-white p-8 shadow-sm"
      >
        <h1 className="text-center text-lg font-semibold text-slate-800">
          Sistema de Agendamento
        </h1>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Usuario</span>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoFocus
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
        </label>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Senha</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
        </label>

        {erro && <p className="text-sm text-red-600">{erro}</p>}

        <button
          type="submit"
          disabled={enviando}
          className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {enviando ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  )
}
