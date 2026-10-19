// The English and Vietnamese sites are two builds with the same page tree (en at /, vi at /vi/).
// The language selector in extra.alternate links to each site's root; point it at the same page instead.
function linkAlternates() {
  const lang = document.documentElement.lang
  const links = [...document.querySelectorAll('a[hreflang]')]
  const own = links.find(a => a.hreflang === lang)
  if (!own) return
  const root = new URL(own.href).pathname
  if (!location.pathname.startsWith(root)) return
  const page = location.pathname.slice(root.length) + location.hash
  for (const a of links) if (a !== own) a.href = new URL(a.href).pathname + page
}
if (window.document$) window.document$.subscribe(linkAlternates)
else document.addEventListener('DOMContentLoaded', linkAlternates)
