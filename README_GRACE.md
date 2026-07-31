# GraceAshcroftBot — Setup Guide

A professional Telegram group moderation bot inspired by **Grace Ashcroft** from *Resident Evil: Requiem*.
FBI Technical Analyst personality — anxious, intelligent, determined.

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_grace.txt
# Additionally install spotdl for music features
pip install spotdl
```
> **Note**: `ffmpeg` must be installed on your system and added to your `PATH`.

### 2. Configure `.env`
Open `.env` and configure your credentials:
```env
BOT_TOKEN=YOUR_TOKEN_FROM_BOTFATHER
```

<!-- AI Features Removed -->

### 4. Run the Bot
```bash
python gracebot.py
```

---

## Commands

| Command | Permission | Description |
|---|---|---|
| `/gstart` | Everyone | Interactive guide with buttons |
| `/ghelp` | Everyone | Full command list |
| `/gabout` | Everyone | About Grace Ashcroft |
| `/gstatus` | Everyone | Check if bot is online |
| `/gmusic [query]` | Everyone | **Premium** Spotify music downloader |
| `/grules` | Everyone | View group rules |
| `/gapply` | Everyone | Join application form |
| `/groulette` | Everyone | Russian roulette 🎲 |
| `/gwarn` | Admin | Warn a member (3 = auto-mute 8h) |
| `/gmute [mins]` | Admin | Restrict a member |
| `/gkick` | Admin | Remove member temporarily |
| `/gban` | Owner | Permanent ban |
| `/gpromote` | Owner | Make someone admin |
| `/gdemote` | Owner | Remove admin permissions |
| `/gadmins` | Admin | List group admins |
| `/ginfo` | Admin | Member info & warnings |
| `/gstats` | Admin | Group statistics |
| `/gclearchat` | Admin | Bulk delete messages |
| `/gnotifyall [text]` | Admin | Mention all tracked members |
| `/gcleardata` | Admin | Clear stored group data |
| `/gsetwelcome` | Owner | Set custom welcome message |
| `/gsetrules` | Owner | Set group rules |
| `/garabic` | Owner | Change bot language |
| `/glinkfilter` | Owner | Toggle link filter |
| `/gspamfilter` | Owner | Toggle long message filter |
| `/grepeatfilter` | Owner | Toggle duplicate message filter |
| `/gcaptcha` | Owner | Toggle math captcha for new members |
| `/gtoggleapply` | Owner | Toggle application form requirement |
| `/gantibot` | Owner | Auto-remove bots when added |
| `/gcleanservice` | Owner | Hide join/leave messages |
| `/gsetlog` | Owner | Show log channel config info |

---

## Grace's Personality

Grace responds naturally to:
- **"who are you" / "what are you"** — Grace introduces herself
- **"grace"** (her name) — She responds to mentions with static persona phrases.

---

## Permission Levels

| Level | Who |
|---|---|
| **Master** | Hard-coded ID (developer) |
| **Owner** | OWNER_ID + SUDO_USERS in `.env` |
| **Admin** | Telegram group admins |
| **Member** | Everyone else |

---

## Built For
👑 Lasso (@n0amtell) & @M0t3ab 💙

*Private Build v1.1 — Grace Ashcroft Bot*

