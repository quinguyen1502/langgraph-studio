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
import { useTranslation } from 'react-i18next'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { LanguageSwitcher } from '@/components/language-switcher'

const PW_RULES: [string, (p: string) => boolean][] = [
  ['auth.ruleLength', p => p.length >= 8],
  ['auth.ruleLetter', p => /[A-Za-z]/.test(p)],
  ['auth.ruleDigit', p => /\d/.test(p)],
]
const safeNext = (n: string | null) => (n && n.startsWith('/') && !n.startsWith('//') && !n.startsWith('/login') && !n.startsWith('/register') ? n : '/workflows')

export function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const { t } = useTranslation(); const nav = useNavigate(); const isLogin = mode === 'login'
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
    if (!isLogin && !pwOk) { setError(t('auth.weak')); return }
    if (!isLogin && password !== confirm) { setError(t('auth.mismatch')); return }
    setBusy(true)
    try {
      const r = await api(`/api/auth/${mode}`, { method: 'POST', json: { email, password } })
      setSession(r.token, r.user); scheduleExpiry(); nav(next, { replace: true })
    } catch (err: any) { setError(err.message) } finally { setBusy(false) }
  }
  const other = isLogin ? '/register' : '/login'
  return <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4 relative">
    <div className="absolute top-4 right-4 flex gap-1"><LanguageSwitcher /><ThemeToggle /></div>
    <Card className="w-full max-w-sm">
      <CardHeader className="text-center">
        <div className="mx-auto mb-2 rounded-lg bg-primary text-primary-foreground p-2 w-fit"><Workflow className="size-5" /></div>
        <CardTitle className="text-xl">{t(isLogin ? 'auth.loginTitle' : 'auth.registerTitle')}</CardTitle>
        <CardDescription>{t(isLogin ? 'auth.loginHint' : 'auth.registerHint')}</CardDescription>
      </CardHeader>
      <form onSubmit={submit} noValidate aria-busy={busy}>
        <CardContent className="space-y-4">
          {expired && !error && <div id="expired-notice" role="status" className="flex items-center gap-2 rounded-md border bg-muted px-3 py-2 text-sm"><Clock className="size-4 shrink-0" />{t('auth.expired')}</div>}
          {error && <Alert variant="destructive" id="auth-error"><AlertCircle /><AlertDescription>{error}</AlertDescription></Alert>}
          <div className="space-y-1.5"><Label htmlFor="email">{t('auth.email')}</Label><Input id="email" className="h-10" type="email" autoComplete="email" required disabled={busy} value={email} onChange={e => setEmail(e.target.value)} placeholder="you@company.com" /></div>
          <div className="space-y-1.5"><Label htmlFor="password">{t('auth.password')}</Label>
            <Input id="password" className="h-10" type="password" autoComplete={isLogin ? 'current-password' : 'new-password'} required disabled={busy} value={password} onChange={e => setPassword(e.target.value)} aria-describedby={isLogin ? undefined : 'pw-rules'} />
            {!isLogin && <ul id="pw-rules" className="mt-1.5 space-y-0.5 text-xs">{PW_RULES.map(([k, f]) => { const ok = f(password); return <li key={k} className={cn('flex items-center gap-1.5', ok ? 'text-success' : 'text-muted-foreground')}>{ok ? <Check className="size-3" /> : <X className="size-3" />}{t(k)}</li> })}</ul>}
          </div>
          {!isLogin && <div className="space-y-1.5"><Label htmlFor="confirm">{t('auth.confirm')}</Label>
            <Input id="confirm" className="h-10" type="password" autoComplete="new-password" required disabled={busy} value={confirm} onChange={e => setConfirm(e.target.value)} aria-invalid={mismatch} />
            {mismatch && <p className="text-xs text-destructive">{t('auth.mismatch')}</p>}</div>}
        </CardContent>
        <CardFooter className="flex-col gap-3 mt-6">
          <Button type="submit" id="auth-submit" size="lg" className="w-full h-11 text-base" disabled={!canSubmit}>{busy && <Loader2 className="animate-spin" />}{t(isLogin ? 'auth.login' : 'auth.register')}</Button>
          <p className="text-sm text-muted-foreground">{t(isLogin ? 'auth.noAccount' : 'auth.haveAccount')}<Link className="underline text-foreground" to={next !== '/workflows' ? `${other}?next=${encodeURIComponent(next)}` : other}>{t(isLogin ? 'auth.register' : 'auth.login')}</Link></p>
        </CardFooter>
      </form>
    </Card>
  </div>
}
