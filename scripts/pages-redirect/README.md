# Redirect for the old docs URL

The handbook was published at `quinguyen1502.github.io/langgraph-studio/` until the project was renamed to Superstep
(TASK-0058). After the repository rename it lives at `quinguyen1502.github.io/superstep/`, and GitHub Pages does not
redirect the old path.

`404.html` fixes that. Published at the root of the **user site** repository `quinguyen1502.github.io`, it is served
for every path that does not exist there, and sends `/langgraph-studio/<page>?<query>#<hash>` to the same page under
`/superstep/`. Other missing paths get a plain "not found" with a link to the docs.

Do not create a new repository named `langgraph-studio` for this: once a repository takes the old name, GitHub stops
redirecting the renamed repository's git and web URLs.

## Publish (owner, after renaming the repository)

1. Create the public repository `quinguyen1502.github.io`.
2. Copy `404.html` to its root and push to `main`.
3. Settings → Pages: Source "Deploy from a branch", branch `main`, folder `/`.
4. Check: `https://quinguyen1502.github.io/langgraph-studio/run/schedules/` opens the Schedules page under
   `/superstep/`, and `/langgraph-studio/vi/` opens the Vietnamese home.
