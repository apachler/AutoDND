# Contributing

Thanks for your interest. AutoDND is small enough that most contributions are
a single PR; please skim this first.

## Development setup

```sh
git clone https://github.com/apachler/AutoDND
cd AutoDND
python -m unittest discover -s tests -v
```

Runtime needs only Python 3.9+ and (for actually toggling DnD) `gsettings`
from GNOME. The test suite uses only the standard library.

Optional dev tools:

```sh
pip install ruff mypy coverage
ruff check .
mypy
coverage run -m unittest discover -s tests && coverage report
```

CI runs all three on every push and PR.

## Coding conventions

The script follows a deliberately terse style — comma-tight type
annotations, no spaces around `:`/`,` inside annotations, single-quoted
strings. Match the surrounding code rather than reformatting it; ruff's
pycodestyle (E/W) rules are intentionally off for that reason.

Other rules worth knowing:

- Annotate locals, parameters, and `None` returns. Don't use `NoReturn`
  unless the function genuinely never returns.
- Don't add runtime dependencies. The Arch package's `depends=()`
  array is minimal on purpose.
- Pure functions live alongside `desired_state`, `next_transition`,
  `parse_lines`, etc. — add a test in `tests/test_schedule.py` whenever
  you change them.
- Side effects live in three places: `set_dnd` (subprocess to
  `gsettings`), the module-level `_last_state` cache, and the
  `_reload_event` signal flag. Keep them there.

## Testing

```sh
python -m unittest discover -s tests -v          # all tests
python -m unittest tests.test_schedule.MainCLI   # one TestCase
coverage run -m unittest discover -s tests && coverage report -m
```

CI enforces a coverage floor of 80% (configured in `pyproject.toml`).

## Releasing (maintainers)

Push a `v*` tag. The release workflow creates a GitHub Release with
auto-generated notes from commits since the previous tag:

```sh
git tag v0.2.0
git push origin v0.2.0
```

AUR users continue to track git via `autodnd-git`; no manual AUR step
is needed.

## Reporting bugs

Use the bug-report issue template — it asks for the config, `--status`
output, logs, and versions, which are usually enough to triage.
