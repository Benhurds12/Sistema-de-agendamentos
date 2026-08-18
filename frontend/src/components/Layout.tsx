import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { logout } from '../api/auth'

const links = [
  { to: '/agendamentos', label: 'Agendamentos' },
  { to: '/agendamentos/novo', label: 'Novo Agendamento' },
  { to: '/grade', label: 'Gerar Grade' },
  { to: '/clientes', label: 'Clientes' },
  { to: '/locais', label: 'Locais' },
  { to: '/tipos-atendimento', label: 'Tipos de Atendimento' },
]

function linkClasses(isActive: boolean) {
  const base = 'block rounded-md px-3 py-2 text-sm font-medium transition-colors'
  return isActive
    ? `${base} bg-slate-900 text-white`
    : `${base} text-slate-600 hover:bg-slate-100`
}

export function Layout() {
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white p-4">
        <h2 className="mb-6 px-2 text-lg font-bold text-slate-900">Agendamento</h2>
        <nav className="flex-1 space-y-1">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/agendamentos'}
              className={({ isActive }) => linkClasses(isActive)}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <button
          onClick={handleLogout}
          className="block rounded-md px-3 py-2 text-left text-sm font-medium text-slate-500 hover:bg-slate-100"
        >
          Sair
        </button>
      </aside>

      <main className="flex-1 p-8">
        <Outlet />
      </main>
    </div>
  )
}
