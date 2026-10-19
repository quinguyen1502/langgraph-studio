# LangGraph Studio handbook

Source of the public MkDocs Material site. English is the default (`/`),
Vietnamese is `/vi/`; every page is a pair `*.en.md` / `*.vi.md`.

Pinned toolchain: `mkdocs-material==9.6.21`, `mkdocs-static-i18n==1.3.0`.

## Preview

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve -a 127.0.0.1:8001
```

`mkdocs.yml` sets `strict: true`, so `.venv/bin/mkdocs build` is the same
check CI runs.

## Content sources

| Content | From |
| --- | --- |
| Screenshots `docs/images/<en|vi>/*.png` | `HANDBOOK_SHOTS=1 npm run e2e -- handbook` in `frontend/` |
| Intro video `docs/assets/video/` | `scripts/promo/` (see its README) |
| Error codes page | Included from `docs/api-errors.md` |

Keep the two languages in step: a change to one page changes its sibling in
the same commit.
