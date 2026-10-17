import { useTranslation } from 'react-i18next'
import { ErrorAlert } from '@/components/approvals/channel-parts'
import { IdentityRow, slotKey, useSlots } from '@/components/approvals/identity-row'

/** My chat accounts across every platform / workspace. */
export function AccountsSection() {
  const { t } = useTranslation(); const { slots, setData, err } = useSlots()
  return <div className="space-y-3">
    {err && <ErrorAlert>{err}</ErrorAlert>}
    {slots && !slots.length && <p className="text-sm text-muted-foreground">{t('approvals.noChannels')}</p>}
    {slots?.map(s => <IdentityRow key={slotKey(s)} slot={s} onChange={setData} />)}
  </div>
}
