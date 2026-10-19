// The same rules as the backend's security.password_problem (8+ characters, a letter and a digit)
export const PASSWORD_RULES: [string, (p: string) => boolean][] = [
  ['auth.ruleLength', p => p.length >= 8],
  ['auth.ruleLetter', p => /[A-Za-z]/.test(p)],
  ['auth.ruleDigit', p => /\d/.test(p)],
]
export const passwordOk = (p: string) => PASSWORD_RULES.every(([, f]) => f(p))
