import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { TooltipProvider } from '@/components/ui/tooltip'
import { hadSession, loginUrl, scheduleExpiry, signedIn, wasExpired } from '@/lib/api'
import { AuthPage } from '@/pages/Auth'
import { WorkflowsPage } from '@/pages/Workflows'
import { ForgotPasswordPage, ResetPasswordPage } from '@/pages/PasswordReset'
import { ApprovePage } from '@/pages/Approve'
import { ApprovalsPage } from '@/pages/Approvals'
import { CommandPalette } from '@/components/command-palette'

// The editor (React Flow, CodeMirror, dagre) and Settings load as their own chunks (TASK-0039).
const EditorPage = lazy(() => import('@/pages/Editor').then(m => ({ default: m.EditorPage })))
const SettingsPage = lazy(() => import('@/pages/settings/SettingsPage').then(m => ({ default: m.SettingsPage })))

function Protected({ children }: { children: React.ReactElement }) {
  const loc = useLocation()
  if (signedIn()) return children
  return <Navigate to={loginUrl(hadSession() || wasExpired(), loc.pathname + loc.search)} replace />
}
scheduleExpiry()
export default function App() {
  return <TooltipProvider delayDuration={300}><BrowserRouter><CommandPalette /><Suspense fallback={null}><Routes>
    <Route path="/login" element={<AuthPage mode="login" />} />
    <Route path="/register" element={<AuthPage mode="register" />} />
    <Route path="/forgot-password" element={<ForgotPasswordPage />} />
    <Route path="/reset-password" element={<ResetPasswordPage />} />
    <Route path="/workflows" element={<Protected><WorkflowsPage /></Protected>} />
    <Route path="/workflows/:id" element={<Protected><EditorPage /></Protected>} />
    <Route path="/approve" element={<Protected><ApprovePage /></Protected>} />
    <Route path="/approvals" element={<Protected><ApprovalsPage /></Protected>} />
    <Route path="/settings/:section?" element={<Protected><SettingsPage /></Protected>} />
    <Route path="*" element={<Navigate to="/workflows" replace />} />
  </Routes></Suspense></BrowserRouter></TooltipProvider>
}
