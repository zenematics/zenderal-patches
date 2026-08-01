# Contributing

This repo holds the **patch plugins for the Zenderal modlist** (Enderal SE — bug fixes, modern
combat, modern visuals) and the curation docs behind it. Useful contributions are patches the list
actually needs, and improvements to the workspace that builds them.

Read **`CLAUDE.md`** first. It carries the verified Enderal facts — masters, SKSE version, archive
order, Papyrus import order — that a patch has to be correct about before anything else matters.

## What's in scope

- **Patches the list needs.** A compatibility or bugfix `.esp` that serves one of the three pillars.
  Say which pillar in the PR description, and add the mod's row to
  `arch-docs/zenderal-curation.md` so the patch isn't orphaned later.
- **Curation.** Roster entries, load-order reasoning, rejected-mod rationale, conversion hazards.
  "We tried X and it broke Y" is worth as much as a working patch.
- **`arch-docs/enderal-record-patterns.md`.** The highest-value file after `CLAUDE.md` and the one
  most likely to be incomplete. If you have lost an afternoon to a record that built cleanly and did
  nothing in-game, that belongs in the guide. Mark it `[verified]` only if you personally saw it fail
  and then saw the fix work; use `[community]` otherwise.
- **Tooling** — `build/build.ps1`, `build/Test-RecordYaml.ps1`, the GitHub Actions workflows,
  `.claude/config/tools.ps1`, and the skills and subagents under `.claude/`.

## What's out of scope

- **The modlist itself.** The Wabbajack list, its `modlist.txt` and its install machinery live
  elsewhere. This repo builds the patches the list installs.
- **Content that isn't a patch.** New quests, new areas, new gear — Zenderal is not an overhaul.
- **Anything containing Bethesda, SureAI or third-party mod assets.** Nothing under `reference/`,
  `papyrus-source/` or `modlist/` is committed, and it must stay that way. Before opening a PR check
  `git status` — if a `.esp`, `.bsa`, a `.pex` you didn't author, or a decompiled Enderal record has
  crept in, remove it.

## Before you open a PR

1. **The build must pass.** Both of these, from a clean checkout:

   ```powershell
   pwsh build/build.ps1 -CheckFomod
   pwsh build/build.ps1
   ```

2. **The record check must pass** if you touched any plugin YAML:

   ```powershell
   pwsh build/Test-RecordYaml.ps1
   ```

3. **Run the pre-ship checklist** at the bottom of `arch-docs/enderal-record-patterns.md`, or ask the
   `spriggit-formkey-auditor` subagent to. Items 1 and 2 (copied from the *winning* plugin;
   `EnderalSE` release with no DLC master) catch the two mistakes that get through everything else.

4. **Round-trip stability** if you hand-edited a record: deserialize, re-serialize, and confirm the
   YAML comes back identical. Spriggit output is canonical; hand-authored YAML should match it
   byte-for-byte so nobody gets a spurious whole-file diff later.

5. **Say what you actually tested.** "Builds clean" and "played 20 minutes in Ark with the patch
   active" are very different claims and the review depends on which one it is. A clean build is not
   a working patch.

6. **If you changed a `.psc`, recompile and commit the `.pex`.** CI cannot compile Papyrus. The build
   fails on a *missing* `.pex` but cannot detect a *stale* one, so this one is on you. Check the
   import order while you're there — Enderal's source tree must be first.

7. **Don't commit `.claude/config/tools.json`.** It's gitignored because it contains your machine's
   paths. Update `tools.example.json` instead if you're adding a key.

Opening a PR triggers a test build that attaches the resulting archives as an Actions artifact, with
a comment linking to them. A docs-only PR builds no archives and skips that step. Fork PRs get a
read-only token, so the comment step is skipped — the build itself still runs.

## Style

- PowerShell targets **5.1**: `Set-StrictMode` is on, and there is no `&&`, no ternary, and no
  null-coalescing operator. Test on Windows PowerShell, not just `pwsh`.
- Match the surrounding prose. The docs explain *why*, not just *what* — a rule without its reason
  gets dropped the first time it's inconvenient.
- Keep skills declarative: they describe a procedure for an agent to follow. Resolve every tool path
  through `$Tools` from `tools.json`; never hardcode one.
- Mark claims about Enderal's behaviour with how you know: measured on your install, read from
  SureAI's source, or assumed. The distinction is the whole value of `CLAUDE.md`.
