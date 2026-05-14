# HAPPY-CODING.md

Persistent engineering backlog. Items the audit identified but deferred,
each annotated with **priority**, **rationale**, **implementation notes**,
**expected impact**, and **estimated effort**.

Conventions:

- **Priority** — `P1` (worth doing soon), `P2` (worthwhile when convenient),
  `P3` (nice-to-have / pending stronger signal), `P4` (not recommended for
  this project — listed for completeness so the question doesn't keep coming
  back).
- **Effort** — `XS` ≤ 30 min, `S` ≤ 2h, `M` ≤ 1d, `L` > 1d.

> Tick items off when implemented. Move "Won't Do (P4)" reasoning into commit
> messages or close issues that re-raise them, rather than re-debating.

---

## P1 — High value, easy wins

### Enable GitHub Private Vulnerability Reporting

- **Rationale:** `SECURITY.md` already advertises the URL
  (`/security/advisories/new`), but the feature must be enabled in repo
  settings or that URL 404s.
- **Implementation:** Settings → Code security → enable "Private vulnerability
  reporting".
- **Impact:** Lowers friction for security reporters who already have a
  GitHub account; populates the repo's published GHSA list.
- **Effort:** XS. UI toggle.

### Configure branch protection on `main`

- **Rationale:** Required-status-check enforcement currently relies on the
  honour system. Rewrites/force-pushes to `main` are possible.
- **Implementation:** Settings → Branches → add rule for `main`:
  - Require pull request before merging (1 approval, or "no approval but PR")
  - Require status checks to pass: `unittest`, `ruff`, `mypy`, `analyze`
    (CodeQL)
  - Require linear history
  - Require signed commits
  - Block force pushes
- **Impact:** Real enforcement of the existing CI checks; aligns with
  Scorecard "Branch-Protection".
- **Effort:** XS. UI change. **Tradeoff:** solo workflow becomes "PR for
  every change"; if that's intolerable, allow self-approving PRs.

### Pre-commit hooks (`.pre-commit-config.yaml`)

- **Rationale:** Catches ruff/mypy issues before they round-trip through CI;
  contributors get the same checks locally.
- **Implementation:** Add `.pre-commit-config.yaml` with `ruff` (lint+format
  in check mode) and `mypy` hooks pinned to the same versions CI uses.
  Document `pre-commit install` in CONTRIBUTING.md.
- **Impact:** Faster contributor feedback loop; fewer "fix lint" commits.
- **Effort:** S. **Tradeoff:** opt-in for contributors; not enforced unless
  CI re-runs the same checks (which it does).

---

## P2 — Worth doing when convenient

### Build provenance attestation for release tarballs

- **Rationale:** Improves Scorecard "Signed-Releases"; distros that consume
  GitHub release tarballs (not the AUR-git path) get verifiable provenance.
- **Implementation:** In `release.yml`, after the version-sync check:
  1. `git archive --format=tar.gz --prefix=autodnd-${VERSION}/ HEAD > autodnd-${VERSION}.tar.gz`
  2. Generate SHA256SUMS
  3. `actions/attest-build-provenance@v2` with `subject-path` pointing at
     the tarball and SHASUMS file
  4. `gh release upload "$GITHUB_REF_NAME" autodnd-*.tar.gz SHA256SUMS`
- **Impact:** Real value only if anyone actually verifies; AUR users won't.
  Skip until a downstream consumer asks.
- **Effort:** S.

### Doc-only path filter on `test`/`lint` workflows

- **Rationale:** README/docs commits currently spin up the full Python matrix
  for nothing.
- **Implementation:** Add `paths-ignore: ['**.md', 'LICENSE', 'docs/**']` to
  `on.push` and `on.pull_request`.
- **Impact:** Faster + cheaper CI on doc PRs.
- **Effort:** XS. **Footgun:** if `unittest` becomes a *required* status
  check on `main`, GitHub treats a skipped workflow as "pending forever" and
  the PR can't merge. The standard fix is a no-op job that always reports
  success on the skipped path. Defer until branch protection is decided.

### Coverage trend tracking

- **Rationale:** The README badge is a static `91%` and will drift. Either
  remove the percent or wire up a real provider.
- **Options:**
  1. Drop the badge and rely on the test workflow's enforced floor.
  2. Use Codecov (free for OSS) — uploads `coverage.xml`, gives PR comments
     and a trend graph.
  3. Generate an SVG with `genbadge` and commit it (repo-internal,
     no external dep).
- **Impact:** Honest coverage signal; PR coverage diff (option 2 only).
- **Effort:** S for option 2; XS for option 1.

### `step-security/harden-runner` egress hardening

- **Rationale:** Scorecard recommends it; pins outbound network policy on
  the runner so a compromised dependency can't exfiltrate or call C2.
- **Implementation:** Add `step-security/harden-runner@<sha>` as the first
  step in each job, audit-only initially, then `egress-policy: block`.
- **Impact:** Real defence-in-depth, but adds a third-party action that runs
  before checkout — read its source and pin to SHA before adopting.
- **Effort:** S.

### `Makefile` (or `justfile`) for common tasks

- **Rationale:** `make test`, `make lint`, `make fmt`, `make package` is a
  smaller cognitive load than remembering each invocation.
- **Implementation:** Tiny Makefile wrapping the commands already in
  CONTRIBUTING.md.
- **Impact:** Lower onboarding friction.
- **Effort:** XS.

---

## P3 — Optional / situational

### `.github/FUNDING.yml`

- **Rationale:** Lets users sponsor via GitHub Sponsors / Ko-fi / etc.
- **When:** Only if a sponsorship channel is actually set up.
- **Effort:** XS.

### Enable Discussions and link from issue templates

- **Rationale:** Channel for questions vs. bug reports. Requires a maintainer
  who reads it.
- **Implementation:** Settings → Features → Discussions; update
  `.github/ISSUE_TEMPLATE/config.yml` with a `contact_links` entry.
- **Effort:** XS.

### `CHANGELOG.md` (Keep-a-Changelog format)

- **Rationale:** Some users prefer a curated changelog over GitHub's
  auto-generated release notes.
- **Tradeoff:** Duplicates the Releases page; another file to keep in sync
  on every release.
- **Recommendation:** Skip unless a downstream packager asks for it.
- **Effort:** S per release.

### `SUPPORT.md`

- **Rationale:** Already covered by `bug_report.yml`, `feature_request.yml`,
  `SECURITY.md`, and the README. A separate file would just duplicate.
- **Recommendation:** Skip.

### `ROADMAP.md` / `GOVERNANCE.md`

- **Rationale:** Single-maintainer project; governance is "ask Andreas".
  Roadmap is implicit (the issues list).
- **Recommendation:** Skip until there's a second regular contributor.

### Refactor `files/autodnd` → installable package

- **Rationale:** A `src/autodnd/__init__.py` + `[project]` table in
  `pyproject.toml` would let users `pip install`, simplify imports in
  tests (no `SourceFileLoader`), and enable `pip`-ecosystem Dependabot.
- **Tradeoff:** Distribution policy is **AUR-only on purpose**; the
  current header-of-`pyproject.toml` even calls this out. Adding PyPI
  publishing is a strategy decision, not a tooling tweak.
- **Recommendation:** Defer until there's user demand for non-Arch installs.
- **Effort:** M (refactor + tests rewrite + docs + CI release-to-PyPI step).

### Multi-platform support

- **Rationale:** `set_dnd` only knows `gsettings` (GNOME). KDE
  (`qdbus org.kde.plasmashell …`), macOS Focus modes, Windows Focus Assist
  could be plugged in.
- **Tradeoff:** Major scope expansion; would justify the package refactor
  above.
- **Effort:** L.

### Workflow SHA-pin GitHub-owned actions

- **Rationale:** Currently `actions/checkout@v4` etc. use major-version
  tags. Scorecard accepts this for GitHub-owned actions but pure-SHA pinning
  is the strictest interpretation.
- **Tradeoff:** Doubles the volume of Dependabot PRs (each major-version
  bump becomes many SHA bumps); marginal security gain since GitHub controls
  the tag mutability for these.
- **Recommendation:** Skip unless the `Pinned-Dependencies` Scorecard score
  is the limiting factor on the overall grade.

---

## P4 — Won't do (logged so the question doesn't return)

### Docker / OCI image

- **Why no:** AutoDND drives the user's GNOME session via `gsettings`/DBus.
  A container would need full DBus and X/Wayland passthrough — at which
  point you've reinvented "running it on the host". No value.

### Kubernetes manifests / Helm chart / IaC

- **Why no:** It's a single-user desktop daemon. No service to deploy.

### Conventional Commits + semantic-release

- **Why no:** The release flow is `git tag v0.X.Y && git push`, releases
  use auto-generated notes from commit messages. The current commit-message
  style is descriptive prose, which the maintainer prefers over mechanical
  type-prefix subjects. Switching imposes ceremony for no functional gain
  on a project this small.

### SBOM (CycloneDX / SPDX) generation

- **Why no:** Zero non-stdlib dependencies. The SBOM would have one entry
  ("Python") and provide no signal beyond what `PKGBUILD`'s `depends=` array
  already states.

### Container image vulnerability scanning (Trivy, Grype, etc.)

- **Why no:** No image to scan.

### E2E / browser tests

- **Why no:** No UI surface; the DnD toggle's "UI" is a single GNOME
  setting, already exercised by `gsettings` itself.

### Performance benchmarks

- **Why no:** The hot path is "wake every N minutes, run one `gsettings`
  command". Any benchmark would measure GNOME, not autodnd.

---

## Notes on existing technical debt

- **`_last_state` is a module global.** Intentional state-cache pattern,
  documented in `CLAUDE.md`. Tests reset it via `autodnd._last_state = None`.
  A class-based redesign would be cleaner but adds nothing the comment
  doesn't already convey.
- **`tests/test_schedule.py` loads the script via `SourceFileLoader`** because
  `files/autodnd` has no `.py` extension. Acceptable; rewriting would mean
  the package refactor (P3 above).
- **`run` from `subprocess` is used unguarded.** The argv is a constant list
  with one boolean cast — no shell injection surface. `check=True` is set,
  so failures propagate. No change needed.
