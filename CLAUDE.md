# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

AutoDND is a small Python daemon that schedules the GNOME "Do Not Disturb" state. The entire application is a single script: `files/autodnd`. It is shipped as an Arch Linux package via `PKGBUILD`.

There is no build step, no test suite, no linter configuration, and no dependency manifest — runtime depends only on Python 3 and the `gsettings` command from GNOME.

## Running locally

```sh
# Run directly (creates ~/.config/autodnd/ and an empty config.txt on first run)
./files/autodnd

# Verbose mode prints parsed events and the sleep delta before each wait
./files/autodnd -d
```

Before running, populate `~/.config/autodnd/config.txt`. The format is documented in `files/config-sample.txt`:

```
# day1,day2,... start-time end-time   (0=Mon … 6=Sun, '#' starts a comment)
0,1,2,3,4 22:00 10:00
```

## Building the package

```sh
makepkg -si    # builds and installs the Arch package using PKGBUILD
```

`PKGBUILD` installs `files/autodnd` to `/usr/bin/`, the desktop entry to `/usr/share/applications/`, the icon to `/usr/share/icons/hicolor/192x192/`, and `config-sample.txt` to `/usr/share/autodnd/`.

## Architecture

The script is a single event loop in `main()` → `execute()`:

1. **Config is read once at startup** (`main()`, before the `while True`). Editing `config.txt` requires restarting the process — do not assume changes are picked up between iterations.
2. **Every loop iteration re-parses the cached lines and recomputes upcoming event boundaries** via `parse_lines` → `read_days` → `next_weekday`. `next_weekday` always advances each event into the future (delta < 0 or expired ⇒ +7 days), so events are stateless relative weekly recurrences, not absolute dates.
3. **`execute()` decides the DnD state for *right now*** by scanning every event:
   - `event_start <= current < event_end` → DnD on.
   - `event_end <= current <= event_end + 1min` → DnD off. This one-minute trailing window is what guarantees the "off" transition is actually written on the next wake-up; widening or removing it will break wake-and-disable behavior.
   - It then returns the time until the soonest upcoming boundary plus a 5-second safety margin, which becomes the `sleep()` duration.
4. **DnD is toggled via `gsettings set org.gnome.desktop.notifications show-banners <bool>`** (`set_dnd`). The flag is inverted: DnD enabled = `show-banners false`.
5. **Empty config exits the process** (`execute` calls `exit(0)` when `events` is empty), so an empty `config.txt` is a valid "disable" state — useful to know when reasoning about systemd/autostart behavior.

### Cross-midnight intervals

`read_days` handles `end < start` (e.g. `22:00 10:00`) by setting `end.day += 1`. Note this uses naive day arithmetic and will raise on month boundaries — be careful when changing this logic.

### Time handling

`get_now()` truncates to whole minutes (`second=0, microsecond=0`). All comparisons in `execute()` assume minute-resolution `current`; the actual `datetime.now()` is only used when computing the final `timedelta` returned for sleeping.

## Conventions

- Type annotations are used throughout, including `NoReturn` on side-effecting functions. Preserve them when editing.
- No external dependencies beyond the Python standard library and `gsettings`. Do not add libraries without a strong reason — the package's `depends` array in `PKGBUILD` would need updating too.
- When bumping behavior that affects installation paths or new shipped files, update both `PKGBUILD`'s `package()` function and (if relevant) `autodnd.desktop`.
