# Superstep handbook

Source of the public documentation site, built with
[Zensical](https://zensical.org) from MkDocs-format config. English is the
root (`/`), Vietnamese is `/vi/`. The two sites are separate builds with the
same page tree:

| Path | Contents |
| --- | --- |
| `mkdocs.base.yml` | Theme, Markdown extensions and everything else both sites share |
| `mkdocs.yml`, `mkdocs.vi.yml` | Per-language URL, folders, palette labels and nav |
| `docs/en/`, `docs/vi/` | Pages, screenshots (`images/`) and the intro video (`assets/video/`) |

`docs/vi/` links `stylesheets/extra.css`, `assets/logo.svg` and
`javascripts/lang-switch.js` to the English copies, so edit those in
`docs/en/`.

## Preview

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/zensical serve -a 127.0.0.1:8001                      # English
.venv/bin/zensical serve -f mkdocs.vi.yml -a 127.0.0.1:8002     # Vietnamese
```

## Build

```bash
.venv/bin/zensical build && .venv/bin/zensical build -f mkdocs.vi.yml
```

`strict: true` fails the build on a broken link or anchor. It does not look
at images, so CI also runs `python3 check_images.py site`, which fails on an
`<img>` or `<video>` whose file is missing. Build English first: it writes `site/`, and the Vietnamese build writes
`site/vi/` inside it.

## Content sources

| Content | From |
| --- | --- |
| Screenshots `docs/<en|vi>/images/*.png` | `HANDBOOK_SHOTS=1 npm run e2e -- handbook` in `frontend/` |
| Intro video `docs/<en|vi>/assets/video/` | `scripts/promo/` (see its README) |
| Error codes page | Included from `docs/api-errors.md` |

Keep the two languages in step: a change to a page in `docs/en/` changes the
same path in `docs/vi/` in the same commit. CI fails when the trees differ.
