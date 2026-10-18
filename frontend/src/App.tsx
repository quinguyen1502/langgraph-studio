import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { TooltipProvider } from '@/components/ui/tooltip'
import { getToken, loginUrl, scheduleExpiry, tokenValid, wasExpired } from '@/lib/api'
import { AuthPage } from '@/pages/Auth'
import { WorkflowsPage } from '@/pages/Workflows'
import { CommandPalette } from '@/components/command-palette'

// The editor (React Flow, CodeMirror, dagre) and Settings load as their own chunks (TASK-0039).
const EditorPage = lazy(() => import('@/pages/Editor').then(m => ({ default: m.EditorPage })))
const SettingsPage = lazy(() => import('@/pages/settings/SettingsPage').then(m => ({ default: m.SettingsPage })))

function Protected({ children }: { children: React.ReactElement }) {
  const loc = useLocation()
  if (tokenValid()) return children
  return <Navigate to={loginUrl(!!getToken() || wasExpired(), loc.pathname + loc.search)} replace />
}
scheduleExpiry()
export default function App() {
  return <TooltipProvider delayDuration={300}><BrowserRouter><CommandPalette /><Suspense fallback={null}><Routes>
    <Route path="/login" element={<AuthPage mode="login" />} />
    <Route path="/register" element={<AuthPage mode="register" />} />
    <Route path="/workflows" element={<Protected><WorkflowsPage /></Protected>} />
    <Route path="/workflows/:id" element={<Protected><EditorPage /></Protected>} />
    <Route path="/settings/:section?" element={<Protected><SettingsPage /></Protected>} />
    <Route path="*" element={<Navigate to="/workflows" replace />} />
  </Routes></Suspense></BrowserRouter></TooltipProvider>
}
