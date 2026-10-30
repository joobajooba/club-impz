# CLUB_IMPZ

Club Impz, a Godot game in `godot-game/`, shared by two collaborators. See `README.md` for how to run it (open `godot-game/project.godot` in Godot 4.7). The IMPLINGZ work moved here from the old COLLAB_IMPZ repo on 2026-10-30.

## Session start

At the start of every session in this repo, before anything else, open the repo in GitHub Desktop by running GitHub Desktop's command-line tool from the repo root: `github .` (on Windows it is `%LOCALAPPDATA%\GitHubDesktop\bin\github.bat`). If GitHub Desktop is already open, this brings it to the front. If it isn't installed, skip this step.

## GitHub workflow

Both collaborators review every change before it reaches the default branch. Follow these rules for any work in this repo.

**The default branch.** The rules below call it `main`. club-impz has no `main` yet: its default branch is `claude/project-thread-w0l9g3`. Until a `main` exists, read `main` below as that branch.

### Every change goes to staging

- Never commit or push directly to `main`.
- Create a branch named `staging/<topic>`, commit to it, push it, and open a **draft** pull request against `main` (`gh pr create --draft`).
- If the change depends on another open staging PR, branch from that one and set the PR base to it (a stacked PR), so the diff shows only the new change.
- Afterwards, tell the user what changed, the branch name and the PR link.

### "Commit to main"

Merge only when the user says **"commit to main"**. Then:

1. `git fetch` and list the open staging PRs. If it's unclear which ones to merge, ask.
2. **Back up first.** Tag the current `origin/main` as `backup/main-YYYYMMDD-HHMM` (an annotated tag whose message says what is about to be merged) and push the tag.
3. Merge each PR, oldest in the stack first: `gh pr ready <n>`. If its base is another staging branch, retarget it with `gh pr edit <n> --base main`. Then `gh pr merge <n> --merge`. Always use a merge commit, never squash or rebase, so the history stays intact.
4. Pull `main`, run the game and confirm it still loads.
5. Report what was merged and the name of the backup tag.

Delete the merged staging branches only when the user asks, and only after confirming they are fully merged (`git merge-base --is-ancestor origin/<branch> origin/main`).

### Rolling back

- Default: open a PR that reverts the bad merge (`git revert -m 1 <merge-sha>`). History is kept and nothing is force-pushed.
- Resetting `main` to a `backup/main-*` tag needs a force-push. Do it only after the user explicitly confirms that specific reset.
- Never delete or move `backup/*` tags.

### This repo is public

Never commit secrets (`.env`, Supabase keys other than the public anon key) or assets whose licence forbids sharing them. The Tin vein model from the first test upload was left out on 2026-10-30 for that reason, until its source is confirmed.

## Retiring the old COLLAB_IMPZ folder (one-time task)

Everything from COLLAB_IMPZ is now in this repo (checked file by file on 2026-10-30), so the old local folder `C:\Desktop\project\collab_impz` should be deleted, leaving this repo as the one place for up-to-date work. Never work in that folder again. If it still exists at the start of a session, do this, in order:

1. **The ported work is on GitHub.** `git ls-remote origin staging/move-collab-drafts` in this repo must list the branch. If it doesn't, ask the user to approve the push first (this repo is public).
2. **Nothing is only in the old folder.** In `collab_impz`, run `git fetch`, then `git log --branches --not --remotes --oneline` (it must print nothing) and `git status --short`. On 2026-10-30 the only untracked files were `image.png` (a meme, not for this public repo) and `miningexample.png` (an ore table reference), plus `node_modules/`, which is safe to lose. Ask the user whether to keep either image, and where, before going on.
3. **Move Claude's memory.** Claude's memory for this project is saved under the old folder's path: copy `%USERPROFILE%\.claude\projects\C--Desktop-project-collab-impz\memory\` to `%USERPROFILE%\.claude\projects\C--Desktop-project-club-impz\memory\`, and update any paths in it that still point to `collab_impz`.
4. **Ask the user to confirm, then delete.** Deleting can't be undone, so get a clear yes. Then run `Remove-Item -Recurse -Force C:\Desktop\project\collab_impz` from outside that folder. Ask the user to remove it from GitHub Desktop's repository list too.
5. **Keep the GitHub repo.** `joobajooba/COLLAB_IMPZ` stays as the private archive: don't delete it, and don't archive it unless the user asks. Then remove this section from this file, in a staging PR.

## Game design

The IMPLINGZ design lives in `docs/` and follows its own rules in `docs/CLAUDE.md`: a roadmap worked in passes, no deviating from what was asked, quality first, and a report at the end of each pass. Read that file before doing any design work. J00BA's Club Impz docs (`game_direction.md` and the docs that point to it) are in `docs/` too; which set wins where they disagree is not decided yet (see `docs/README.md`).
