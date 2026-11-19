# Contributing to Edit Master Skill

Thanks for wanting to make the skill better. Edit Master is one markdown
file plus templates, examples and docs, so almost every contribution is
prose, not code. The bar is precision: the right number, the right term,
the right failure mode, in the voice the skill already uses.

## Code of Conduct

Everyone participating in this project — issues, pull requests, discussions
— agrees to the [Code of Conduct](CODE_OF_CONDUCT.md). Report problems
privately, the way that document describes.

## Reporting bugs

Open an issue with the bug report template
([.github/ISSUE_TEMPLATE/bug_report.md](.github/ISSUE_TEMPLATE/bug_report.md)).
GitHub pre-fills it when you pick "Bug report" under New issue. The template
asks for:

- a short description of what went wrong;
- the skill version or commit you are on;
- the agent you used (Claude Code, Codex, Cursor, Gemini CLI, chat-only);
- steps to reproduce, and expected versus actual behavior;
- logs or output: transcript, hook panel, humanizer scores, QA report.

## Suggesting features

Feature ideas start in
[GitHub Discussions](https://github.com/Dani-Devlop/edit-master-skill/discussions),
not as pull requests. Say what you were trying to ship when the skill fell
short; a concrete failure mode beats a wishlist. Ideas that hold up in
discussion get an issue, then a pull request.

## Pull request process

1. **Fork** the repository.
2. **Branch** from `main` with a descriptive name: `feat/short-form-hooks`,
   `fix/safe-zone-number`, `docs/faq-expansion`.
3. **Commit** using the conventions below. One logical change per pull
   request.
4. **Open the pull request** with the PR template
   ([.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md)).
5. **Review.** The maintainer reviews prose the way an editor reviews a
   cut: terminology first, numbers second, style last. Expect line notes;
   they are normal, not rejection.

## Commit conventions

Conventional Commits, one type per commit:

- `feat:` a new capability in the skill or tooling —
  `feat(hooks): add a long-form formula for teardowns`
- `fix:` a wrong number, wrong term, broken link or broken command —
  `fix(docs): correct the safe-zone lower bound to y=1440`
- `docs:` prose-only changes — `docs: expand the FAQ with render settings`
- `chore:` repository maintenance — `chore: tighten markdownlint config`
- `test:` test protocol and matrix changes —
  `test: add Fashion/Style category to the matrix`

## Style guide for SKILL.md edits

SKILL.md is the product. Edits to it follow the repo-wide style:

- Markdown, 80-character soft wrap, no trailing whitespace, no emoji.
- Keep the counts in sync everywhere they appear — SKILL.md, README.md,
  these docs, and the CI structure check all agree on:
  - **47 hook formulas = 21 long-form + 26 short-form**
  - **5 phases** in the workflow
  - **12 editing principles**
  - **16 QA gate points**
  - **10 onboarding questions**
- Keep the exact terminology: the 5-property panel is SPECIFICITY /
  ADDRESS / STAKES / CURIOSITY / BREVITY; the verdict is **60% mean + 40%
  weakest property**; bands are STRONG >= 72, WORKABLE >= 55, WEAK < 55;
  the humanizer PASS is overall 70+ with no check below 55; the beat sheet
  plans at **165 wpm**.
- Nothing publishes itself: any new output type still ends in the
  copy-ready block and the question "ship it, or change it?".

## Testing requirements

- **A new hook formula needs four things before it counts:** a shape (the
  pattern), a written example, an on-screen version (six words or fewer for
  short-form), and a failure mode. Update the count text (21 / 26 / 47) and
  `docs/HOOKS.md` in the same change.
- **Docs changes must pass CI:** markdownlint (config
  `.markdownlint.jsonc`) and the lychee link check. If you add a link to a
  file that does not exist yet, ship the file in the same pull request.
- **Changed numbers propagate:** if you touch scoring, beat-sheet timing or
  safe zones, update `docs/WORKFLOWS.md`, `docs/FAQ.md` and
  `docs/EXAMPLES.md` in the same pull request so the docs never disagree.
- Renderer behavior is validated through the test protocol in
  [tests/README.md](tests/README.md); skill prose changes do not require a
  matrix run.
