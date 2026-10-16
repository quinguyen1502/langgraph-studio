import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Workflow, Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { api, setSession } from '@/lib/api'
import { ThemeToggle } from '@/lib/theme'

export function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const nav = useNavigate(); const isLogin = mode === 'login'
  const [email, setEmail] = useState(isLogin ? 'admin@example.com' : '')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setError('')
    if (!isLogin && password !== confirm) { setError('Mật khẩu xác nhận không khớp'); return }
    setBusy(true)
    try {
      const r = await api(`/api/auth/${mode}`, { method: 'POST', json: { email, password } })
      setSession(r.token, r.user); nav('/workflows')
    } catch (err: any) { setError(err.message) } finally { setBusy(false) }
  }
  return <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4 relative">
    <div className="absolute top-4 right-4"><ThemeToggle /></div>
    <Card className="w-full max-w-sm">
      <CardHeader className="text-center">
        <div className="mx-auto mb-2 rounded-lg bg-primary text-primary-foreground p-2 w-fit"><Workflow className="size-5" /></div>
        <CardTitle className="text-xl">{isLogin ? 'Đăng nhập LangGraph Studio' : 'Tạo tài khoản'}</CardTitle>
        <CardDescription>{isLogin ? 'Demo: admin@example.com / admin123' : 'Tài khoản mới sẽ có sẵn workflow ví dụ'}</CardDescription>
      </CardHeader>
      <form onSubmit={submit}>
        <CardContent className="space-y-4">
          {error && <div className="flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive" role="alert"><AlertCircle className="size-4" />{error}</div>}
          <div className="space-y-1.5"><Label htmlFor="email">Email</Label><Input id="email" type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="you@company.com" /></div>
          <div className="space-y-1.5"><Label htmlFor="password">Mật khẩu</Label><Input id="password" type="password" required value={password} onChange={e => setPassword(e.target.value)} /></div>
          {!isLogin && <div className="space-y-1.5"><Label htmlFor="confirm">Xác nhận mật khẩu</Label><Input id="confirm" type="password" required value={confirm} onChange={e => setConfirm(e.target.value)} /></div>}
        </CardContent>
        <CardFooter className="flex-col gap-3 mt-6">
          <Button type="submit" className="w-full" disabled={busy}>{busy && <Loader2 className="animate-spin" />}{isLogin ? 'Đăng nhập' : 'Đăng ký'}</Button>
          <p className="text-sm text-muted-foreground">{isLogin ? <>Chưa có tài khoản? <Link className="underline text-foreground" to="/register">Đăng ký</Link></> : <>Đã có tài khoản? <Link className="underline text-foreground" to="/login">Đăng nhập</Link></>}</p>
        </CardFooter>
      </form>
    </Card>
  </div>
}
