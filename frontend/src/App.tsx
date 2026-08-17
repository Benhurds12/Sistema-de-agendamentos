import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { AgendamentosPage } from './pages/AgendamentosPage'
import { ClientesPage } from './pages/ClientesPage'
import { GerarGradePage } from './pages/GerarGradePage'
import { LocaisPage } from './pages/LocaisPage'
import { NovoAgendamentoPage } from './pages/NovoAgendamentoPage'
import { TiposAtendimentoPage } from './pages/TiposAtendimentoPage'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/agendamentos" replace />} />
        <Route path="/agendamentos" element={<AgendamentosPage />} />
        <Route path="/agendamentos/novo" element={<NovoAgendamentoPage />} />
        <Route path="/grade" element={<GerarGradePage />} />
        <Route path="/clientes" element={<ClientesPage />} />
        <Route path="/locais" element={<LocaisPage />} />
        <Route path="/tipos-atendimento" element={<TiposAtendimentoPage />} />
        <Route path="*" element={<Navigate to="/agendamentos" replace />} />
      </Route>
    </Routes>
  )
}

export default App
