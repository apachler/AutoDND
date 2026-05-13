# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

AutoDND is a small Python daemon that schedules the GNOME "Do Not Disturb" state. The main application is a single script: `files/autodnd`. It is shipped as an Arch Linux package via `PKGBUILD`.

Runtime depends only on Python 3 (stdlib) and the `gsettings` command from GNOME. The repo also ships a desktop entry, a systemd user unit, and a unit test file under `tests/`.

## Running locally

```sh
# Run as a daemon (creates ~/.config/autodnd/ and an empty config.txt on first run)
./files/autodnd

# DEBUG-level logging (events, sleep deltas, SIGHUP wake-ups)
./files/autodnd -d

# Validate config and exit
./files/autodnd --check

# Print desired DnD state and next transition, then exit
./files/autodnd --status

# Apply current desired state once and exit (cron-friendly)
./files/autodnd --once
```

Populate `~/.config/autodnd/config.txt` before running. The format is documented in `files/config-sample.txt`:

```
# <days> <start-time> <end-time>
# days: 0..6 (0=Mon), names (mon-sun), ranges (0-4, mon-fri), aliases (weekdays/weekends/all), comma-mixed
weekdays 22:00 10:00
```

## Tests

```sh
python3 -m unittest discover -s tests -v
```

There is no test dependency beyond stdlib. `tests/test_schedule.py` loads `files/autodnd` via `SourceFileLoader` (the script has no `.py` extension) and monkeypatches `autodnd.get_now` to fix "now" per test.

## Building the package

```sh
makepkg -si    # builds and installs the Arch package using PKGBUILD
```

`PKGBUILD` installs `files/autodnd` to `/usr/bin/`, the desktop entry to `/usr/share/applications/`, the icon to `/usr/share/icons/hicolor/192x192/`, the systemd user unit to `/usr/lib/systemd/user/`, and `config-sample.txt` to `/usr/share/autodnd/`.

After install, either keep the existing XDG autostart (`autodnd.desktop`) or enable the systemd user unit:

```sh
systemctl --user enable --now autodnd
systemctl --user reload autodnd    # SIGHUP, picks up config.txt changes
```

## Architecture

The script is a single event loop in `main()` → `execute()`:

1. **Config is read at startup and again on SIGHUP.** Editing `config.txt` does not require a restart — send SIGHUP (or `systemctl --user reload autodnd`). The sleep in the main loop uses `threading.Event.wait(timeout)` rather than `time.sleep()` so SIGHUP wakes the daemon mid-sleep; `time.sleep()` would not, because PEP 475 makes it retry through EINTR.
2. **Every loop iteration re-parses the cached lines and recomputes upcoming event boundaries** via `parse_lines` → `read_days` → `expand_days` + `next_weekday`. `next_weekday` always advances each event into the future *and* additionally yields the previous-week occurrence when its `end` is still in the future. That second occurrence is what makes cross-midnight events work: at Tue 02:00, the Mon 22:00 → Tue 10:00 event must still be detectable, and a naïve forward-only roll would skip it.
3. **`execute()` is state-based.** It computes `desired_state(events, now)` ("is `now` inside any event's `[start, end)`?"), compares against a module-level `_last_state` cache, and only calls `gsettings` when the state actually changes. This makes wake-from-suspend correct (whatever the desired state is *now* gets applied) and removes any need for special trailing-window logic.
4. **DnD is toggled via `gsettings set org.gnome.desktop.notifications show-banners <bool>`** (`set_dnd`). The flag is inverted: DnD enabled = `show-banners false`.
5. **Empty config exits the process** (`execute()` calls `sys.exit(0)` when `events` is empty), so an empty `config.txt` is a valid "disable" state — useful to know when reasoning about systemd/autostart behaviour.
6. **CLI modes that bypass the loop:** `--check`, `--status`, and `--once` all parse the config, do their one-shot work, and exit before `signal.signal(SIGHUP, …)` is registered.

### Cross-midnight intervals

`read_days` handles `end < start` (e.g. `22:00 10:00`) by `end + timedelta(days=1)`. Combined with `next_weekday` also returning the previous-week occurrence when its end is in the future, this correctly covers both halves of the span.

### Time handling

`get_now()` truncates to whole minutes (`second=0, microsecond=0`). All comparisons inside `desired_state` / `next_transition` assume minute-resolution `current`; the actual `datetime.now()` is only used in `execute()` when computing the final `timedelta` returned for sleeping (plus a 5-second safety margin).

### Config validation

`parse_lines` wraps each line's parse error in `ValueError(f"line {n}: …")`, and `read_days` / `create_datetime` / `expand_days` each raise informative `ValueError`s for malformed input. `main()` runs `parse_lines` once at startup (and on every reload) and prints `autodnd: config error: line N: …` then exits 2 on failure, so misconfigured users see a useful message instead of a traceback.

## Conventions

- Type annotations are used throughout, including on locals and on `None` returns. Preserve them when editing. Don't use `NoReturn` unless the function genuinely never returns (e.g. unconditional `sys.exit`/`raise`).
- No external dependencies beyond the Python standard library and `gsettings`. Do not add libraries without a strong reason — the package's `depends` array in `PKGBUILD` would need updating too.
- When changing behaviour that affects installation paths or new shipped files, update both `PKGBUILD`'s `package()` function and (if relevant) `autodnd.desktop` / `autodnd.service`.
- The pure functions (`expand_days`, `create_datetime`, `read_days`, `next_weekday`, `desired_state`, `next_transition`, `parse_lines`) have tests in `tests/test_schedule.py`. Add tests alongside changes to these.
- Side effects live in three places: `set_dnd` (shells out to `gsettings`), the module-level `_last_state` cache, and the `_reload_event` signal flag. Tests should stay on the pure side; if you need to exercise `execute()` directly, reset `autodnd._last_state = None` first.
