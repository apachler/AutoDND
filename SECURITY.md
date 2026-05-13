# Security Policy

## Supported versions

AutoDND is a rolling-release desktop utility. Only the `main` branch
and the most recent tagged release receive security fixes.

## Reporting a vulnerability

Please do **not** open a public GitHub issue for security reports.

Email **apachler@paan-systems.com** with:

- A description of the issue and its impact.
- Steps to reproduce or a proof of concept.
- The version (commit hash or release tag) where you observed it.

You can expect an initial response within seven days. If the report
is confirmed, a fix will land on `main` and be tagged as a release;
the report will be credited in the release notes unless you ask
otherwise.

## Scope

AutoDND has a narrow attack surface: it reads a user-owned config
file, shells out to `gsettings`, and listens for `SIGHUP`. Reports
of concrete bugs in parsing, signal handling, or the subprocess
invocation are in scope; reports about GNOME's `gsettings` or
notifications stack itself should go upstream.
