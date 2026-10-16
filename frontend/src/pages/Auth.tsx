import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Workflow, Loader2, AlertCircle, Clock, Check, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { api, scheduleExpiry, setSession } from '@/lib/api'
import { ThemeToggle } from '@/lib/theme'
import { cn } from '@/lib/utils'

const PW_RULES: [string, (p: string) => boolean][] = [
  ['Ít nhất 8 ký tự', p => p.length >= 8],
  ['Có chữ cái', p => /[A-Za-z]/.test(p)],
  ['Có chữ số', p => /\d/.test(p)],
]
const safeNext = (n: string | null) => (n && n.startsWith('/') && !n.startsWith('//') && !n.startsWith('/login') && !n.startsWith('/register') ? n : '/workflows')

export function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const nav = useNavigate(); const isLogin = mode === 'login'
  const [params] = useSearchParams(); const expired = params.get('expired') === '1'; const next = safeNext(params.get('next'))
  const [email, setEmail] = useState(isLogin ? 'admin@example.com' : '')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  const pwOk = PW_RULES.every(([, f]) => f(password))
  const mismatch = !isLogin && confirm.length > 0 && password !== confirm
  const canSubmit = !busy && email.trim() && password && (isLogin || (pwOk && confirm && !mismatch))
  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setError('')
    if (!isLogin && !pwOk) { setError('Mật khẩu chưa đủ mạnh'); return }
    if (!isLogin && password !== confirm) { setError('Mật khẩu xác nhận không khớp'); return }
    setBusy(true)
    try {
      const r = await api(`/api/auth/${mode}`, { method: 'POST', json: { email, password } })
      setSession(r.token, r.user); scheduleExpiry(); nav(next, { replace: true })
    } catch (err: any) { setError(err.message) } finally { setBusy(false) }
  }
  const other = isLogin ? '/register' : '/login'
  return <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4 relative">
    <div className="absolute top-4 right-4"><ThemeToggle /></div>
    <Card className="w-full max-w-sm">
      <CardHeader className="text-center">
        <div className="mx-auto mb-2 rounded-lg bg-primary text-primary-foreground p-2 w-fit"><Workflow className="size-5" /></div>
        <CardTitle className="text-xl">{isLogin ? 'Đăng nhập LangGraph Studio' : 'Tạo tài khoản'}</CardTitle>
        <CardDescription>{isLogin ? 'Demo: admin@example.com / admin123' : 'Tài khoản mới sẽ có sẵn workflow ví dụ'}</CardDescription>
      </CardHeader>
      <form onSubmit={submit} noValidate aria-busy={busy}>
        <CardContent className="space-y-4">
          {expired && !error && <div id="expired-notice" role="status" className="flex items-center gap-2 rounded-md border bg-muted px-3 py-2 text-sm"><Clock className="size-4 shrink-0" />Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.</div>}
          {error && <div id="auth-error" className="flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive" role="alert"><AlertCircle className="size-4 shrink-0" />{error}</div>}
          <div className="space-y-1.5"><Label htmlFor="email">Email</Label><Input id="email" className="h-10" type="email" autoComplete="email" required disabled={busy} value={email} onChange={e => setEmail(e.target.value)} placeholder="you@company.com" /></div>
          <div className="space-y-1.5"><Label htmlFor="password">Mật khẩu</Label>
            <Input id="password" className="h-10" type="password" autoComplete={isLogin ? 'current-password' : 'new-password'} required disabled={busy} value={password} onChange={e => setPassword(e.target.value)} aria-describedby={isLogin ? undefined : 'pw-rules'} />
            {!isLogin && <ul id="pw-rules" className="mt-1.5 space-y-0.5 text-xs">{PW_RULES.map(([t, f]) => { const ok = f(password); return <li key={t} className={cn('flex items-center gap-1.5', ok ? 'text-success' : 'text-muted-foreground')}>{ok ? <Check className="size-3" /> : <X className="size-3" />}{t}</li> })}</ul>}
          </div>
          {!isLogin && <div className="space-y-1.5"><Label htmlFor="confirm">Xác nhận mật khẩu</Label>
            <Input id="confirm" className="h-10" type="password" autoComplete="new-password" required disabled={busy} value={confirm} onChange={e => setConfirm(e.target.value)} aria-invalid={mismatch} />
            {mismatch && <p className="text-xs text-destructive">Mật khẩu xác nhận không khớp</p>}</div>}
        </CardContent>
        <CardFooter className="flex-col gap-3 mt-6">
          <Button type="submit" id="auth-submit" size="lg" className="w-full h-11 text-base" disabled={!canSubmit}>{busy && <Loader2 className="animate-spin" />}{isLogin ? 'Đăng nhập' : 'Đăng ký'}</Button>
          <p className="text-sm text-muted-foreground">{isLogin ? 'Chưa có tài khoản? ' : 'Đã có tài khoản? '}<Link className="underline text-foreground" to={next !== '/workflows' ? `${other}?next=${encodeURIComponent(next)}` : other}>{isLogin ? 'Đăng ký' : 'Đăng nhập'}</Link></p>
        </CardFooter>
      </form>
    </Card>
  </div>
}
