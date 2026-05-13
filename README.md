# Auto Do Not Disturb

[![tests](https://github.com/apachler/AutoDND/actions/workflows/test.yml/badge.svg)](https://github.com/apachler/AutoDND/actions/workflows/test.yml)
[![codeql](https://github.com/apachler/AutoDND/actions/workflows/codeql.yml/badge.svg)](https://github.com/apachler/AutoDND/actions/workflows/codeql.yml)
[![coverage](https://img.shields.io/badge/coverage-91%25-brightgreen)](https://github.com/apachler/AutoDND/actions/workflows/test.yml)
[![release](https://img.shields.io/github/v/release/apachler/AutoDND?display_name=tag&sort=semver)](https://github.com/apachler/AutoDND/releases)
[![AUR](https://img.shields.io/aur/version/autodnd-git?label=AUR)](https://aur.archlinux.org/packages/autodnd-git)
[![python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![license](https://img.shields.io/github/license/apachler/AutoDND)](LICENSE)

A small Python daemon that turns the GNOME "Do Not Disturb" mode on and off on a
weekly schedule — e.g. silence notifications every night between 22:00 and 10:00,
or during a school day from 8:00 to 14:00.

No external dependencies beyond Python 3 (stdlib) and the `gsettings` command
that ships with GNOME.

## Install

### Arch Linux (AUR / PKGBUILD)

```sh
makepkg -si
```

This installs `/usr/bin/autodnd`, a `.desktop` autostart entry, a systemd user
unit, and the sample config.

### Other distributions

Copy `files/autodnd` somewhere on your `PATH` and make it executable. The
script depends only on Python 3 and `gsettings`.

```sh
install -Dm755 files/autodnd ~/.local/bin/autodnd
```

## Configure

Edit `~/.config/autodnd/config.txt` (created automatically on first run).
Each non-comment line is one event:

```
# <days> <start-time> <end-time>
```

`days` accepts several forms, comma-mixed if you like:

| form        | example          | meaning                        |
|-------------|------------------|--------------------------------|
| number(s)   | `0,1,2,3,4`      | 0=Mon, 6=Sun                   |
| name(s)     | `mon,wed,fri`    |                                |
| range       | `0-4`, `mon-fri` |                                |
| alias       | `weekdays`       | mon–fri                        |
|             | `weekends`       | sat, sun                       |
|             | `all`            | every day                      |

Times are `HH:MM` (24-hour). If `end < start` the event wraps midnight.

`#` starts a comment.

Example config:

```
# Night, every day
all  22:00 10:00

# School day
weekdays  8:00 14:00

# Saturday morning meeting
sat 9:00 11:00
```

After editing, reload without restarting:

```sh
systemctl --user reload autodnd   # or:  kill -HUP $(pgrep -f autodnd)
```

## Run

Pick one of the two autostart options.

**Systemd user service** (recommended — gets you `Restart=on-failure`, journald
logs, and `systemctl --user reload`):

```sh
systemctl --user enable --now autodnd
```

**XDG autostart** — the shipped `autodnd.desktop` runs `autodnd` on login under
GNOME / KDE / etc. No extra setup if you installed via PKGBUILD.

### CLI

```sh
autodnd              # run as a daemon
autodnd -d           # daemon with DEBUG logging
autodnd --check      # validate config and print expanded occurrences
autodnd --status     # print current desired DnD state and next transition
autodnd --once       # apply the current desired state once and exit
```

`--once` makes the scheduler cron-friendly:

```cron
* * * * *   /usr/bin/autodnd --once
```

## Develop

The schedule logic has unit tests using only `unittest` from the standard
library:

```sh
python3 -m unittest discover -s tests -v
```

See `CLAUDE.md` for architecture notes.

## License

GPL-3.0 — see `LICENSE`.
