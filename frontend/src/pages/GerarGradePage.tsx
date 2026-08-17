import { useState, type FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { listarLocais } from '../api/locais'
import { gerarGrade, type GerarGradeResultado } from '../api/horarios'
import { extrairErrosDeCampo, type ErrosDeCampo } from '../api/errors'

interface FormState {
  local: string
  inicio: string
  fim: string
  duracao_minutos: string
}

const FORM_VAZIO: FormState = { local: '', inicio: '', fim: '', duracao_minutos: '' }

export function GerarGradePage() {
  const [form, setForm] = useState<FormState>(FORM_VAZIO)
  const [erros, setErros] = useState<ErrosDeCampo>({})
  const [resultado, setResultado] = useState<GerarGradeResultado | null>(null)

  const locaisQuery = useQuery({ queryKey: ['locais'], queryFn: listarLocais })
  const locaisAtivos = (locaisQuery.data ?? []).filter((local) => local.ativo)

  const gerarMutation = useMutation({
    mutationFn: gerarGrade,
    onSuccess: (dados) => {
      setResultado(dados)
      setErros({})
    },
    onError: (erro) => {
      setResultado(null)
      setErros(extrairErrosDeCampo(erro))
    },
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setResultado(null)

    if (!form.local || !form.inicio || !form.fim || !form.duracao_minutos) {
      setErros({ nao_campo: ['Preencha todos os campos.'] })
      return
    }

    gerarMutation.mutate({
      local: Number(form.local),
      inicio: form.inicio,
      fim: form.fim,
      duracao_minutos: Number(form.duracao_minutos),
    })
  }

  return (
    <div className="max-w-xl space-y-6">
      <h1 className="text-xl font-semibold text-slate-800">Gerar Grade de Horarios</h1>
      <p className="text-sm text-slate-500">
        Gera automaticamente a quantidade maxima de horarios completos dentro do intervalo
        informado, sem ultrapassar a data/hora final.
      </p>

      <form
        onSubmit={handleSubmit}
        className="space-y-4 rounded-lg border border-slate-200 bg-white p-6"
      >
        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Local</span>
          <select
            value={form.local}
            onChange={(e) => setForm({ ...form, local: e.target.value })}
            required
            className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 ${
              erros.local ? 'border-red-400' : 'border-slate-300'
            }`}
          >
            <option value="" disabled>
              {locaisQuery.isLoading ? 'Carregando locais...' : 'Selecione um local'}
            </option>
            {locaisAtivos.map((local) => (
              <option key={local.id} value={local.id}>
                {local.nome}
              </option>
            ))}
          </select>
          {erros.local && <span className="mt-1 block text-xs text-red-600">{erros.local[0]}</span>}
          {!locaisQuery.isLoading && locaisAtivos.length === 0 && (
            <span className="mt-1 block text-xs text-amber-600">
              Nenhum local ativo cadastrado. Cadastre um local antes de gerar a grade.
            </span>
          )}
        </label>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Data/hora de inicio</span>
            <input
              type="datetime-local"
              value={form.inicio}
              onChange={(e) => setForm({ ...form, inicio: e.target.value })}
              required
              className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 ${
                erros.inicio ? 'border-red-400' : 'border-slate-300'
              }`}
            />
            {erros.inicio && (
              <span className="mt-1 block text-xs text-red-600">{erros.inicio[0]}</span>
            )}
          </label>

          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">Data/hora de fim</span>
            <input
              type="datetime-local"
              value={form.fim}
              onChange={(e) => setForm({ ...form, fim: e.target.value })}
              required
              className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 ${
                erros.fim ? 'border-red-400' : 'border-slate-300'
              }`}
            />
            {erros.fim && <span className="mt-1 block text-xs text-red-600">{erros.fim[0]}</span>}
          </label>
        </div>

        <label className="block text-sm">
          <span className="mb-1 block font-medium text-slate-700">Duracao do atendimento (minutos)</span>
          <input
            type="number"
            min={1}
            value={form.duracao_minutos}
            onChange={(e) => setForm({ ...form, duracao_minutos: e.target.value })}
            required
            className={`w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 ${
              erros.duracao_minutos ? 'border-red-400' : 'border-slate-300'
            }`}
          />
          {erros.duracao_minutos && (
            <span className="mt-1 block text-xs text-red-600">{erros.duracao_minutos[0]}</span>
          )}
        </label>

        {erros.nao_campo && <p className="text-sm text-red-600">{erros.nao_campo[0]}</p>}

        {resultado && (
          <p className="rounded-md bg-green-50 px-3 py-2 text-sm font-medium text-green-700">
            {resultado.mensagem}
          </p>
        )}

        <button
          type="submit"
          disabled={gerarMutation.isPending}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          {gerarMutation.isPending ? 'Gerando...' : 'Gerar grade'}
        </button>
      </form>
    </div>
  )
}
