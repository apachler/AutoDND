## What this changes

<!-- One or two sentences. What and why, not how. -->

## Checklist

- [ ] `python -m unittest discover -s tests` passes locally
- [ ] `ruff check .` is clean
- [ ] `mypy` is clean (only enforced for `files/autodnd`)
- [ ] If you touched a pure function (`expand_days`, `create_datetime`,
      `read_days`, `next_weekday`, `desired_state`, `next_transition`,
      `parse_lines`), there's a corresponding test
- [ ] If you changed installation paths or shipped files, `PKGBUILD`
      and (where relevant) `autodnd.desktop` / `autodnd.service` are
      updated
- [ ] If you added behavior the daemon exposes, `README.md` and/or
      `CLAUDE.md` reflect it
