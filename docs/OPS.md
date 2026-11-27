# OPS — internal operations notes

> **INTERNAL.** Repo-internal operational memory for the maintainer agent.
> Must NOT be advertised on the public surface (README carries no
> signing/GPG/scopes narrative; the badge policy lives here, marked internal).

## Badge policy (internal agent rule)
- Every commit pushed to `main` shows either the blue **Verified** badge or
  NO signature badge at all. A yellow *Unverified* badge is NEVER acceptable.
- The signing key is NOT published in this repository (`GPG-PUBLIC-KEY.asc`
  was removed in Phase 26 — the public README must stay free of any
  GPG/registration/scope narrative). Registering a key with the GitHub
  account requires an API token with the `admin:gpg_key` scope; when that
  scope is unavailable, commits are intentionally left **unsigned**
  (no-badge policy) rather than signed-but-unverified.
- After every push: badge audit — 0 *Unverified*; report "unsigned fallback"
  honestly when no key scope exists.

## Delivery / reporting ops (internal)
- Telegram owner 2040835005 via bot mystationZworkbot. LIVE-only inline
  reports every ~30 min at step boundaries. NO scheduler/cron/delayed jobs.
- Report format: "Report of Make Edit Skill / edit-master-skill Progress
  Report / UTC time / 20-block progress bar (5% per block from task.md) /
  Done(n/N) list / In Progress(n) / Blocked(n)+reason / badge / temp+freed /
  chat clean". Milestones immediate; final report at end.
- Hygiene: TEMP under /tmp/ems-work/<run>/ deleted after output; KEEP-LIST
  honored (masters + proofs + verdicts + plans); chat surface clean (no
  edit-*/TEMP); task.md kept and committed.
- Tokens silent everywhere; only Dani-Devlop; only main.

## Phase 26 acceptance reframe (internal)
- PASS-to-post = binary **B1-B10 ALL YES** + IG-native match >= 70% (blind
  independent critic). Absolute aesthetic 8.5 = STRETCH, never a blocker.
- Stop-loss: after the single Phase 26 round, an unmet stretch goes to USER
  decision (post-as-is OR hybrid human-polish / executor swap). Never fake;
  never drift the frozen ledger (G1-G8 / LF1-LF8 / IG1-IG10 / WC1-WC4).
