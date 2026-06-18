# 📈 GSE Terminal — Telegram Bot

Ghana Stock Exchange live data, searchable directly from Telegram.

---

## What the bot does

| Command | What happens |
|---|---|
| `/start` | Welcome menu with buttons |
| `/stock MTNGH` | Full stock profile — price, change, volume, EPS, P/E |
| `/market` | All 39 equities + top movers summary |
| `/top` | Top 5 gainers, losers, most traded |
| `/search MTN` | Search by name or ticker |
| `/news` | Latest Ghana & Africa business news |
| `/dividends` | Upcoming dividend calendar |
| Type `GCB` | Instantly shows stock profile |

---

## Step 1 — Create your Telegram bot (free, 2 minutes)

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. When asked for a name, type: `GSE Terminal`
4. When asked for a username, type: `GSETerminalBot` (or any unique name ending in `bot`)
5. BotFather gives you a token like:
   ```
   7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
6. **Copy and save this token** — you need it in Step 3

---

## Step 2 — Host it FREE on Railway (recommended)

Railway gives you free hosting that runs 24/7.

### 2a. Create a GitHub account
Go to **github.com** → Sign up (free)

### 2b. Create a new GitHub repository
1. Click **+** → **New repository**
2. Name it: `gse-telegram-bot`
3. Set to **Public**
4. Click **Create repository**

### 2c. Upload the bot files
Upload these 4 files to the repository:
- `bot.py`
- `requirements.txt`
- `Procfile`
- `runtime.txt`

_(From the repository page → "uploading an existing file")_

### 2d. Deploy to Railway
1. Go to **railway.app** → Sign up with GitHub (free)
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your `gse-telegram-bot` repository
4. Click **Deploy**

### 2e. Add your Bot Token
1. In Railway, click your project → **Variables** tab
2. Click **New Variable**
3. Name: `BOT_TOKEN`
4. Value: your token from Step 1
5. Click **Add** → Railway redeploys automatically

Your bot is now live 24/7! ✅

---

## Step 3 — Test your bot

1. Open Telegram
2. Search for your bot username (e.g. `@GSETerminalBot`)
3. Send `/start`
4. You should see the welcome menu

---

## Alternative: Run locally on your computer

If you have Python installed:

```bash
# Install dependencies
pip install -r requirements.txt

# Set your token (Mac/Linux)
export BOT_TOKEN="your_token_here"

# Set your token (Windows)
set BOT_TOKEN=your_token_here

# Run
python bot.py
```

---

## Alternative free hosts

| Platform | Free tier | Notes |
|---|---|---|
| **Railway** | $5 credit/month free | Easiest, recommended |
| **Render** | 750 hrs/month free | Good alternative |
| **Fly.io** | 3 VMs free | More technical |
| **Koyeb** | Free tier | Simple deployment |

---

## Customise the bot

### Change the contact info
Edit `bot.py` line 42:
```python
"📧 attah.godsway999@gmail.com\n"
"📱 +233 53 383 3623"
```

### Add more dividend data
Find `DIVS = [` in `bot.py` and add more entries.

### Change cache duration
```python
CACHE_TTL = 300  # seconds (5 minutes default)
```
Set higher (e.g. 600) if you want less API calls.

---

## Contact

📧 attah.godsway999@gmail.com
📱 +233 53 383 3623
💬 WhatsApp: wa.me/233533833623
