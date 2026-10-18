/** UI language + the account's chat language (TASK-0022 follow-up): approval requests and verification codes sent
 *  to Slack/Telegram use the language the user works in, stored as `lang` in the notification preferences. */
import i18n from '@/lib/i18n'
import { api, signedIn } from '@/lib/api'

const SYNCED = 'lgs_lang_synced'
const save = (lang: string) => { if (signedIn()) api('/api/notifications/preferences', { method: 'PUT', json: { lang } }).then(() => sessionStorage.setItem(SYNCED, lang)).catch(() => {}) }

export function setLanguage(lang: string) { i18n.changeLanguage(lang); save(lang) }

/** Once per browser session after sign-in: tell the server which language this user sees. */
export function syncLanguage() { const l = i18n.resolvedLanguage; if (l && sessionStorage.getItem(SYNCED) !== l) save(l) }
