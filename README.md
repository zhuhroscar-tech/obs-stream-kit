# OBS Stream Kit

A reproducible, tested OBS Studio 32 scene collection for a Twitch gaming + just-chatting channel on macOS (Apple Silicon). Minimal, xQc-style layout with one restrained design system ("Graphite + Volt"), built entirely from free plugins and services. Scenes are applied to OBS through its built-in obs-websocket by an idempotent Python builder — re-running is safe.

## Scenes and hotkeys

| Hotkey | Scene | What viewers see | Audio |
|---|---|---|---|
| ⌃⌥1 | Starting Soon | Countdown, name, rotating socials, chat | Mic + music |
| ⌃⌥2 | Gaming | Game full-bleed, small rounded cam bottom-left, brand chip | Mic + game |
| ⌃⌥3 | Just Chatting | Hero cam, chat column | Mic + desktop |
| ⌃⌥4 | React | Safari window, cam top-right, chat | Mic + desktop |
| ⌃⌥5 | BRB | Blurred live game, "One sec." | Music only (mic **off**) |
| ⌃⌥6 | Ending | "GGs." + chat | Mic + music |
| ⌃⌥0 | Privacy | Opaque card, instant cut | Music only (mic **off**) |

Other hotkeys: ⌃⌥C / ⌃⌥⇧C show / hide chat in Gaming · ⌃⌥M / ⌃⌥⇧M mute / unmute mic · ⌃⌥S save the last 60 s as a clip (replay buffer, saved to `~/Movies`).

Mic muting on BRB/Privacy is structural — the mic isn't in those scenes — so it cannot fail like an automation macro can. Scene changes use the **Move** transition (450 ms): the cam glides between its corner and hero positions.

## Design system

| Token | Value | Rule |
|---|---|---|
| Background | `#0B0C0F` | Holding screens only |
| Surface | `rgba(18,20,24,.82)` + 1 px `rgba(255,255,255,.10)` | Chips, chat cards |
| Text / secondary | `#F5F6F8` / `#A1A7B0` | |
| Accent (Volt) | `#C8FF2E` | Semantic only — "now/new": status dot, countdown, alert highlight. Never a fill. |

Inter is the only typeface (`brew install --cask font-inter`). 1920×1080 canvas, 48 px safe margin, 16 px gap, 12 px chip radius.

## Free tools used

OBS plugins (all macOS universal, verified on OBS 32.2.2): Move Transition 3.2.1, Advanced Scene Switcher 1.36.1, Source Clone 0.2.3, Composite Blur 1.5.2. Services: StreamElements (alerts, chatbot), jChat (on-screen chat with 7TV/BTTV/FFZ emotes), StreamBeats (DMCA-safe music).

## Commands

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp config/kit.example.json config/kit.json   # fill in your values (kit.json is gitignored)

.venv/bin/python -m obsbuild render         # generate local overlays + cam mask (offline)
.venv/bin/python -m obsbuild probe          # list OBS/plugin kinds
.venv/bin/python -m obsbuild apply          # build/update the "Stream Kit" collection + profile (OBS running)
.venv/bin/python -m obsbuild finish         # Move transition + hotkeys (OBS must be closed)
.venv/bin/python -m obsbuild doctor         # read-only health checks
.venv/bin/python -m obsbuild snapshot       # render every scene to out/snapshots/*.png
.venv/bin/python -m obsbuild check-audio    # mic/desktop audio live state per scene
.venv/bin/python -m obsbuild check-hotkeys  # injects every hotkey and verifies the result

node --test tests/js/kit-lib.test.cjs
.venv/bin/pytest -q
```

The websocket password is read from the macOS Keychain item `obs-websocket` (account `obs`).

`apply` owns the seven main scenes and the `[SRC]` scenes: items you add to them by hand are removed on the next `apply`. Put personal additions in a new scene and nest it.

## One-time setup in OBS / on the web

1. **Twitch account** — OBS → Settings → Stream → Service *Twitch* → *Connect Account*. Adds the chat / stream-info docks.
2. **Alerts** — streamelements.com → Overlays → new 1920×1080 overlay → add *AlertBox* at **x 560, y 48, w 800, h 300**. Per alert: Inter, text `#F5F6F8`, highlight `#C8FF2E`, no background box, fade-up in/out, 6 s. Cheers: TTS for ≥ 100 bits with the profanity filter on. Copy the overlay URL into `streamelements_alertbox_url` in `config/kit.json` (it is a secret — never commit it) and re-run `apply`.
3. **Music** — download a StreamBeats album (streambeats.bandcamp.com, name-your-price → $0) and save one track or mix as `music/streambeats.mp3`.
4. **Per game** — `Game` source → Properties → pick the game window (run games windowed/borderless at 1920×1080 or 1600×900). `Content` → pick the Safari window.
5. **Optional automation** (Tools → Advanced Scene Switcher → Macros): *Go live → Starting Soon* (condition Streaming "started", action Switch scene); *Auto end* (condition Scene is Ending for 120 s, action Stop streaming).

## Engagement loop (matters more than any plugin)

- StreamElements chatbot: `!socials`, `!discord`, `!schedule`; one timer every 15 min.
- Twitch native: Predictions every round, Polls in Just Chatting, a Follower Goal, cheap + pricey Channel Point rewards.
- Press ⌃⌥S after every good moment, cut it vertical, post to TikTok / Shorts.
- Fixed schedule; open on Starting Soon for 3–5 min; raid someone from Ending.

## Performance notes (MacBook Air M4, fanless)

Output 1280×720 at 60 fps, Apple VT H.264 hardware encoder, 6000 kbps; recording reuses the stream encode; browser sources 30 fps (alerts 60). If dropped frames show up, lower `VBitrate` in `obsbuild/build.py` to `4500` and re-run `apply`, and prefer Ethernet.
