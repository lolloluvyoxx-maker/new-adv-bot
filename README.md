# SALVATION Discord Bot — Railway Deployment

This repo is set up to deploy straight from GitHub to [Railway](https://railway.app).

## What was changed in this pass (rebrand, theme, and bug fixes)

- **Rebranded** from "Zyrox X" (and two other leftover names, "STACY" and "CodeX Development",
  from earlier resellers of this template) to **SALVATION** everywhere it's visible: embeds,
  footers, the help menu, presence text, the role Antinuke creates, the console banner, etc.
- **Removed hardcoded backdoor access**: several files had specific Discord user IDs
  (the original template author's accounts) hardcoded to bypass "server owner only" checks,
  get DM-broadcast permissions, and be publicly credited as the bot's "Main Owner" regardless
  of who actually runs the bot. All of that has been removed; ownership now comes only from
  `OWNER_IDS` in `utils/config.py`.
- **Removed covert telemetry**: every command run in every server was being reported (user,
  server, channel, avatar) to a webhook controlled by the original developer, with their own
  account explicitly excluded from the log. This has been deleted.
- **Fixed the help menu being essentially empty**: the category list relied on a `help_custom()`
  method that no longer existed on any loaded cog (it only existed in an unused, now-deleted
  `cogs/zyrox/` folder), so every category page beyond "Home" silently showed nothing. Categories
  are now generated automatically from each cog's name.
- **Fixed commands failing silently**: `cogs/events/Errors.py` was swallowing real bugs inside
  commands (`CommandInvokeError`) with no message and no log. Errors are now logged to the
  console and the user gets a clear "something went wrong" reply instead of nothing.
- **Fixed the AI chat commands being completely broken**: `MODEL_ID` was set to
  `mixtral-8x7b-32768`, which Groq decommissioned back in late 2024. Updated to a current
  supported model (`openai/gpt-oss-20b`).
- **White theme + no emoji**: every embed color is now white (`0xFFFFFF`), and decorative emoji
  (both custom `<:name:id>` Discord emoji tied to the old bot's application, and standard unicode
  emoji) were stripped from embeds, buttons, and select menus. Buttons that only had an emoji and
  no visible label (so they rendered blank) now have real text labels. Emoji that are actually
  *used* as reaction-based game input (Wordle, Connect Four, Blackjack, RPS, etc.) were left alone,
  since those aren't cosmetic - removing them would break the games.
- **Other bugs fixed along the way**: moderation embeds were hotlinking the old bot's avatar via a
  hardcoded CDN URL (18+ places) instead of showing the current bot's own avatar; invite buttons
  pointed at the old bot's Discord application ID; a music "now playing" link pointed at a Discord
  invite instead of the actual track; a "Vote" button linked to a malformed top.gg URL.
- **Secrets**: the Spotify API credentials and MapQuest key that were hardcoded in source now read
  from `SPOTIFY_CLIENT_ID`/`SPOTIFY_CLIENT_SECRET`/`MAPQUEST_API_KEY` env vars (falling back to the
  original values if unset, so nothing breaks if you don't set your own).
- **Support server links**: every `discord.gg/codexdev` link (the old developer's server) was
  replaced with a placeholder (`discord.gg/your-server-here`) — search the repo for that string
  and swap in your own invite if you want those buttons to go somewhere.
- One feature — free "no-prefix" for boosting a specific external Discord server (`cogs/commands/np.py`)
  — is built entirely around the original developer's own server and role IDs. It's left in place
  and safely does nothing (it was already guarded against the server/role not being found), but it
  won't do anything useful for you unless you rebuild it around your own server.

## What was changed to make this deployable (earlier pass)

- **`requirements.txt`** cleaned up — removed stdlib fakes (`asyncio`, `typing`, `pathlib`, `datetime`,
  `collection`) and the conflicting `discord` package that clashes with `discord.py`, plus unused
  heavy/broken deps (`Quart`, `pymongo`, `motor`, `tasksio`, `Augmentor`, `pyttsx3`).
- **Secrets moved to environment variables**: the Pexels and Giphy API keys were hardcoded in
  `cogs/commands/image.py` and `cogs/commands/fun.py` — they now read from `PEXELS_API_KEY` /
  `GIPHY_API_KEY`. The Discord bot token and Groq AI key already used env vars (`TOKEN`,
  `GROQ_API_KEY`); see `.env.example`.
- **Keep-alive server** now binds to Railway's `PORT` env var instead of a hardcoded port, so
  Railway's health checks work.
- **SQLite files consolidated** under `db/` (two stray files, `rr.db` and `j2c_data.db`, were at the
  project root — moved so a single Volume mount covers everything). The `db/` folder is created
  automatically on startup.
- Added `Procfile`, `railway.json`, `.python-version`, and `.gitignore`.

## 1. Push this to GitHub

```bash
cd ZyroX
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

`.env` and all `*.db` files are gitignored on purpose — never commit real secrets or local bot data.

## 2. Create the Railway project

1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**.
2. Select this repository. Railway will detect Python via Nixpacks automatically and pick up
   `railway.json` / `Procfile` for the start command (`python CodeX.py`).

## 3. Set environment variables

In the Railway service → **Variables**, add:

| Variable | Required | Notes |
|---|---|---|
| `TOKEN` | ✅ | Discord bot token — Developer Portal → Bot → Reset Token |
| `GROQ_API_KEY` | optional | Needed for the AI chat commands |
| `PEXELS_API_KEY` | optional | Needed for image search commands |
| `GIPHY_API_KEY` | optional | Needed for GIF commands |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` | optional | Your own Spotify app credentials for music lookups; falls back to a shared default if unset |
| `MAPQUEST_API_KEY` | optional | Your own key for the `/map` command; falls back to a shared default if unset |
| `LOG_CHANNEL_ID` | optional | Channel ID for guild-join/leave logs |
| `SERVER_COUNT_CHANNEL_ID` / `USER_COUNT_CHANNEL_ID` | optional | Voice/text channel IDs whose *names* get updated with live server/user counts |

> The bot token that was in the uploaded `.env` was already a placeholder (masked with `x`s), but
> as a general rule: if a real token is ever exposed anywhere (git history, screenshots, chat), treat
> it as compromised and regenerate it in the Discord Developer Portal immediately.

## 4. Add a persistent Volume (important)

This bot stores all its data in local SQLite files under `db/`. **Railway's filesystem is ephemeral** —
without a Volume, every redeploy wipes levels, warns, tickets, giveaways, etc.

1. In the Railway service → **Settings → Volumes** → **New Volume**.
2. Mount path: `/app/db`
3. Redeploy. From then on, everything in `db/` persists across deploys.

## 5. Deploy

Railway deploys automatically on push to `main`. Watch the **Deployments** tab for build/runtime logs.
Once running, you should see the SALVATION startup banner in the logs and the bot come online in Discord.

## Notes

- The bot also starts a tiny Flask server (used for Railway's health check / uptime ping) on the
  `PORT` Railway provides — no action needed, it's automatic.
- `config.yml` holds non-secret bot behavior settings (AI model, presence messages, word filters,
  etc.) — edit and commit it directly rather than using env vars.
