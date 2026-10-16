import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { TooltipProvider } from '@/components/ui/tooltip'
import { getToken } from '@/lib/api'
import { AuthPage } from '@/pages/Auth'
import { WorkflowsPage } from '@/pages/Workflows'
import { EditorPage } from '@/pages/Editor'

function Protected({ children }: { children: React.ReactElement }) {
  return getToken() ? children : <Navigate to="/login" replace />
}
export default function App() {
  return <TooltipProvider delayDuration={300}><BrowserRouter><Routes>
    <Route path="/login" element={<AuthPage mode="login" />} />
    <Route path="/register" element={<AuthPage mode="register" />} />
    <Route path="/workflows" element={<Protected><WorkflowsPage /></Protected>} />
    <Route path="/workflows/:id" element={<Protected><EditorPage /></Protected>} />
    <Route path="*" element={<Navigate to="/workflows" replace />} />
  </Routes></BrowserRouter></TooltipProvider>
}
