import { Navigate, Outlet } from 'react-router-dom'
import { estaAutenticado } from '../api/auth'

export function RotaProtegida() {
  if (!estaAutenticado()) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}
