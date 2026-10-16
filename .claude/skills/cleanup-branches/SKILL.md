---
name: cleanup-branches
description: Audit and clean local Git branches and stale remote-tracking references after pull requests merge or when the user explicitly declares old branches obsolete. Use when the user asks to clean, prune, or delete old branches.
---

# Cleanup Branches

1. Require a clean working tree and switch to the integration branch.
2. Fetch or inspect remote state, then classify local branches as merged, unmerged, or stale.
3. Preserve `main`, the integration branch, and the current branch.
4. Delete merged local branches with the non-forced form.
5. Inspect unmerged branches with `git cherry`, commit logs, and diff stats.
6. Delete an unmerged branch only when the user explicitly confirms it is no longer needed.
7. Prune stale remote-tracking references.
8. Delete actual remote branches only when the user explicitly requests remote deletion and the branch still exists.
9. Verify the final local and remote branch lists and report branches intentionally retained.

Never discard a dirty worktree or use `git reset --hard` as part of cleanup.
