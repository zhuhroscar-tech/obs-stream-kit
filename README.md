# OBS Stream Kit

A reproducible, tested OBS Studio 32 scene collection for a Twitch gaming + just-chatting channel on macOS (Apple Silicon). Minimal, xQc-style layout with one restrained design system ("Graphite + Volt"), built entirely from free plugins and services. Scenes are applied to OBS through its built-in obs-websocket by an idempotent Python builder — re-running is safe.

## Commands

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp config/kit.example.json config/kit.json   # fill in your values (kit.json is gitignored)

.venv/bin/python -m obsbuild render        # generate local overlays + cam mask (offline)
.venv/bin/python -m obsbuild probe         # list OBS/plugin kinds
.venv/bin/python -m obsbuild apply         # build/update the "Stream Kit" collection + profile
.venv/bin/python -m obsbuild doctor        # health checks
.venv/bin/python -m obsbuild snapshot      # render every scene to out/snapshots/*.png
.venv/bin/python -m obsbuild check-macros  # verify mic auto-mute automation

node --test tests/js/kit-lib.test.cjs
.venv/bin/pytest -q
```

The websocket password is read from the macOS Keychain item `obs-websocket` (account `obs`):
`security add-generic-password -s obs-websocket -a obs -w`

## Manual steps

Plugin installs, the Move transition, hotkeys and Advanced Scene Switcher macros are done once in the OBS UI — see the operating guide below.
