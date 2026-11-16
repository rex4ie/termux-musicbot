# termux-musicbot

A Telegram userbot that plays music and video in group voice chats, built to run on an Android phone with [Termux](https://termux.dev).
Uses [Kurigram](https://github.com/KurimuzonAkuma/pyrogram) + [py-tgcalls](https://github.com/pytgcalls/pytgcalls) 2.x.

## Install

1. Install **Termux from F-Droid** (https://f-droid.org/packages/com.termux/), not the Play Store.
2. Open Termux and run:
   ```bash
   yes | pkg upgrade && pkg install -y curl && curl -fsSL https://raw.githubusercontent.com/rex4ie/termux-musicbot/main/termux-setup.sh | bash
   ```
   The first install takes 10 to 20 minutes.
3. Log in to Telegram (skip this if the installer says it found your `.env`):
   ```bash
   musicbot session
   ```
   You need **API_ID / API_HASH** from https://my.telegram.org (API development tools), your phone number, and the code Telegram sends. Answer `Y` to save.
4. Start it:
   ```bash
   musicbot
   ```
   Wait for `UserBot + VC client started`, then send `!ping` in Telegram.

## Update
```bash
musicbot update
```
This pulls the latest code from this repo and upgrades packages. Your `.env` is kept.

## Day to day
| Command | What it does |
|---|---|
| `musicbot` | Start the bot (auto-restarts on crash; Ctrl+C twice to stop) |
| `musicbot update` | Get the latest version |
| `musicbot session` | Log in again / new session |
| `musicbot env` | Edit settings (`.env`) |
| `musicbot shell` | Shell inside the bot's Debian container |

**Keep it alive:** set Termux's battery usage to **Unrestricted** in Android settings. `musicbot` takes a wakelock automatically.

**Only run one copy.** Don't run this session on two devices at once (e.g. phone + PC). Telegram can revoke a session used from two places simultaneously.

## Settings (`.env`)
| Var | Description |
|---|---|
| `API_ID` / `API_HASH` | From my.telegram.org |
| `SESSION` | String session (made by `musicbot session`). **Never share it.** |
| `HNDLR` | Command prefix, default `!` |
| `GROUP_MODE` | `True`: anyone can play. `False`: only you and your contacts |

## Bot commands
- `!play <search | link>`, or reply `!play` to an audio/video file, a YouTube or stream link, or a `t.me/...` post link (public or private channel).
- `!vplay` does the same with video. Add `480` or `360` for lower quality.
- `!playfrom <channel> ; <n>` plays the last *n* audio files from a channel.
- `!playlist`, `!skip [n...]`, `!pause`, `!resume`, `!stop`, `!ping`, `!help`, `!restart`

## Why a Debian container?
py-tgcalls' native engine (ntgcalls) only ships glibc builds, and Termux uses Android's libc. `proot-distro` gives a Debian userland without root. Python 3.12 is installed with [uv](https://github.com/astral-sh/uv) because ntgcalls has no wheels for Debian's default Python 3.13.
