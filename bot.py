"""
GSE Terminal — Telegram Bot
===========================
Ghana Stock Exchange live data, searchable via Telegram.

Commands:
  /start        — Welcome + menu
  /stock MTNGH  — Full stock profile
  /market       — Top movers + market summary
  /search abc   — Search by name or ticker
  /top          — Top 5 gainers & losers
  /dividends    — Upcoming dividends
  /news         — Latest Ghana market news
  /help         — All commands

Author : GSE Terminal (attah.godsway999@gmail.com)
Contact: +233 53 383 3623
"""

import os
import logging
import asyncio
import aiohttp
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("GSEBot")

# ── Config ─────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

GSE_LIVE_URL    = "https://dev.kwayisi.org/apis/gse/live"
GSE_EQUITY_URL  = "https://dev.kwayisi.org/apis/gse/equities/{ticker}"
RSS2JSON_URL    = "https://api.rss2json.com/v1/api.json?rss_url={url}&count=10"
NEWS_FEEDS = [
    ("https://thebftonline.com/feed/",                         "B&FT Online"),
    ("https://citibusinessnews.com/feed/",                     "Citi Business"),
    ("https://www.myjoyonline.com/feed/",                      "Joy Business"),
    ("https://feeds.bbci.co.uk/news/business/rss.xml",         "BBC Business"),
    ("https://www.cnbcafrica.com/feed/",                       "CNBC Africa"),
]

# ── Company Registry ───────────────────────────────────────────────────────────
COMPANIES = {
    "MTNGH":    "MTN Ghana",
    "GCB":      "GCB Bank",
    "SCB":      "Standard Chartered",
    "SCBPREF":  "SCB Preference",
    "EGH":      "Ecobank Ghana",
    "ETI":      "Ecobank Transnat.",
    "CAL":      "CAL Bank",
    "ACCESS":   "Access Bank Ghana",
    "ADB":      "Agric. Dev. Bank",
    "AGA":      "AngloGold Ashanti",
    "AADS":     "AngloGold ADS",
    "SOGEGH":   "Société Générale",
    "RBGH":     "Republic Bank GH",
    "EGL":      "Enterprise Group",
    "TOTAL":    "TotalEnergies GH",
    "GOIL":     "GOIL Company",
    "GGBL":     "Guinness Ghana",
    "UNIL":     "Unilever Ghana",
    "TLW":      "Tullow Oil",
    "GLD":      "NewGold ETF",
    "SIC":      "SIC Insurance",
    "FML":      "Fan Milk",
    "ZEN":      "ZEN Petroleum",
    "KASA":     "Kasapreko",
    "FAB":      "First Atlantic Bank",
    "BOPP":     "Benso Oil Palm",
    "CPC":      "Cocoa Processing",
    "MAC":      "Mega African Capital",
    "SAMBA":    "Samba Foods",
    "TBL":      "Trust Bank Ltd",
    "HORDS":    "Hords Ltd",
    "ALLGH":    "Atlantic Lithium",
    "ASG":      "Asante Gold",
    "IIL":      "Industrial Images",
    "CLYD":     "Clydestone Ghana",
    "CMLT":     "Camelot Ghana",
    "DASPHARMA":"Das Pharma",
    "DIGICUT":  "Digicut Ltd",
    "MMH":      "Meridian-Marshall",
}

# Snapshot prices for offline fallback
FALLBACK = {
    "AADS":{"price":0.42,"change":0,"volume":841},
    "ACCESS":{"price":29,"change":0,"volume":1001},
    "ADB":{"price":5.3,"change":0,"volume":0},
    "AGA":{"price":37,"change":0,"volume":0},
    "ALLGH":{"price":8.46,"change":0,"volume":434},
    "ASG":{"price":8.89,"change":0,"volume":2},
    "BOPP":{"price":79.99,"change":0,"volume":0},
    "CAL":{"price":0.77,"change":0,"volume":310013},
    "CLYD":{"price":2.5,"change":0,"volume":0},
    "CMLT":{"price":0.14,"change":0,"volume":0},
    "CPC":{"price":0.13,"change":0,"volume":0},
    "DASPHARMA":{"price":0.41,"change":0,"volume":0},
    "DIGICUT":{"price":0.09,"change":0,"volume":0},
    "EGH":{"price":41,"change":0,"volume":284},
    "EGL":{"price":10.05,"change":0,"volume":9249},
    "ETI":{"price":2.29,"change":0.04,"volume":76977},
    "FAB":{"price":8.4,"change":0.43,"volume":8309},
    "FML":{"price":13.34,"change":0,"volume":202},
    "GCB":{"price":36,"change":0,"volume":11494},
    "GGBL":{"price":12.99,"change":0,"volume":416},
    "GLD":{"price":462,"change":-0.03,"volume":2},
    "GOIL":{"price":7.5,"change":0,"volume":2366},
    "HORDS":{"price":0.11,"change":0,"volume":103},
    "IIL":{"price":0.08,"change":0,"volume":5108},
    "KASA":{"price":1.45,"change":0.13,"volume":2455},
    "MAC":{"price":5.2,"change":0,"volume":0},
    "MMH":{"price":0.1,"change":0,"volume":0},
    "MTNGH":{"price":6.42,"change":-0.03,"volume":488128},
    "RBGH":{"price":4.87,"change":-0.13,"volume":7893},
    "SAMBA":{"price":0.55,"change":0,"volume":0},
    "SCB":{"price":71.38,"change":0,"volume":2},
    "SCBPREF":{"price":0.9,"change":0,"volume":0},
    "SIC":{"price":5.18,"change":0,"volume":13084},
    "SOGEGH":{"price":6.85,"change":0.05,"volume":9476},
    "TBL":{"price":1.2,"change":0,"volume":0},
    "TLW":{"price":11.92,"change":0,"volume":60},
    "TOTAL":{"price":36.3,"change":0,"volume":1456},
    "UNIL":{"price":29.5,"change":0,"volume":248},
    "ZEN":{"price":10,"change":0,"volume":40316},
}

# ── Simple in-memory cache ─────────────────────────────────────────────────────
_cache: dict = {}
CACHE_TTL = 300  # 5 minutes


def cache_get(key: str):
    entry = _cache.get(key)
    if entry and (datetime.now() - entry["ts"]).seconds < CACHE_TTL:
        return entry["data"]
    return None


def cache_set(key: str, data):
    _cache[key] = {"data": data, "ts": datetime.now()}


# ── HTTP helpers ───────────────────────────────────────────────────────────────
HEADERS = {"User-Agent": "GSETerminalBot/1.0"}
PROXIES = [
    lambda u: f"https://api.allorigins.win/get?url={u}",
    lambda u: f"https://corsproxy.io/?{u}",
]


async def fetch_json(url: str, timeout: int = 10) -> dict | list | None:
    """Fetch JSON with fallback proxies."""
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        # Try direct first
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                if r.status == 200:
                    return await r.json(content_type=None)
        except Exception:
            pass
        # Try proxies
        for proxy_fn in PROXIES:
            try:
                proxy_url = proxy_fn(url)
                async with session.get(proxy_url, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                    if r.status != 200:
                        continue
                    raw = await r.json(content_type=None)
                    # allorigins wraps in {contents}
                    if isinstance(raw, dict) and "contents" in raw:
                        import json
                        return json.loads(raw["contents"])
                    return raw
            except Exception:
                continue
    return None


# ── Data fetchers ──────────────────────────────────────────────────────────────
async def get_all_stocks() -> list[dict]:
    cached = cache_get("all_stocks")
    if cached:
        return cached

    data = await fetch_json(GSE_LIVE_URL)
    if data:
        stocks = []
        raw_list = data if isinstance(data, list) else data.get("data", [])
        for s in raw_list:
            ticker = (s.get("name") or s.get("ticker") or "").upper()
            price  = float(s.get("price", 0))
            change = float(s.get("change", 0))
            vol    = float(s.get("volume", 0))
            stocks.append({
                "ticker": ticker,
                "name":   COMPANIES.get(ticker, ticker),
                "price":  price,
                "change": change,
                "pct":    round((change / (price - change) * 100), 2) if (price - change) > 0 else 0,
                "volume": vol,
                "prev":   round(price - change, 2),
            })
        if stocks:
            cache_set("all_stocks", stocks)
            return stocks

    # Fallback to snapshot
    stocks = []
    for ticker, info in FALLBACK.items():
        price  = info["price"]
        change = info["change"]
        stocks.append({
            "ticker": ticker,
            "name":   COMPANIES.get(ticker, ticker),
            "price":  price,
            "change": change,
            "pct":    round((change / (price - change) * 100), 2) if (price - change) > 0 else 0,
            "volume": info["volume"],
            "prev":   round(price - change, 2),
        })
    return stocks


async def get_equity(ticker: str) -> dict | None:
    key = f"equity_{ticker}"
    cached = cache_get(key)
    if cached:
        return cached
    data = await fetch_json(GSE_EQUITY_URL.format(ticker=ticker.lower()))
    if data:
        cache_set(key, data)
    return data


async def get_news() -> list[dict]:
    cached = cache_get("news")
    if cached:
        return cached

    articles = []
    for feed_url, source in NEWS_FEEDS[:3]:  # fetch 3 in parallel
        try:
            api_url = RSS2JSON_URL.format(url=feed_url)
            data = await fetch_json(api_url, timeout=12)
            if data and data.get("status") == "ok":
                for item in (data.get("items") or [])[:4]:
                    title = (item.get("title") or "").strip()
                    link  = item.get("link") or ""
                    if title and len(title) > 10:
                        articles.append({"title": title, "url": link, "src": source})
        except Exception:
            continue

    if articles:
        cache_set("news", articles)
    return articles[:12]


# ── Formatters ─────────────────────────────────────────────────────────────────
def arrow(change: float) -> str:
    return "🟢 ▲" if change > 0 else ("🔴 ▼" if change < 0 else "⚪ ─")


def fmt_price(p: float) -> str:
    return f"₵{p:,.2f}"


def fmt_vol(v: float) -> str:
    if v >= 1_000_000:
        return f"{v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"{v/1_000:.1f}K"
    return str(int(v))


def stock_card(s: dict, equity: dict | None = None) -> str:
    change  = s["change"]
    pct     = s["pct"]
    ar      = arrow(change)
    sign    = "+" if change > 0 else ""
    name    = s.get("name", s["ticker"])
    lines   = [
        f"📈 *{s['ticker']}* — {name}",
        f"",
        f"💰 *Price:*    {fmt_price(s['price'])}",
        f"{ar} *Change:*   {sign}{fmt_price(change)}  ({sign}{pct:.2f}%)",
        f"📉 *Prev Close:* {fmt_price(s['prev'])}",
        f"📦 *Volume:*   {fmt_vol(s['volume'])}",
    ]

    if equity:
        mkt_cap  = equity.get("marketCap") or equity.get("market_cap")
        shares   = equity.get("shares") or equity.get("sharesInIssue")
        eps      = equity.get("eps")
        dps      = equity.get("dps")
        pe       = equity.get("pe") or equity.get("peRatio")
        sector   = equity.get("sector")
        industry = equity.get("industry")
        lines.append("")
        if mkt_cap:
            lines.append(f"🏦 *Market Cap:*  ₵{float(mkt_cap)/1e6:.2f}M")
        if shares:
            lines.append(f"📊 *Shares:*      {fmt_vol(float(shares))}")
        if eps:
            lines.append(f"💵 *EPS:*         ₵{float(eps):.4f}")
        if dps:
            lines.append(f"🎁 *DPS:*         ₵{float(dps):.4f}")
        if pe:
            lines.append(f"📐 *P/E Ratio:*   {float(pe):.2f}x")
        if sector:
            lines.append(f"🏭 *Sector:*      {sector}")
        if industry:
            lines.append(f"🔧 *Industry:*    {industry}")

    lines += [
        "",
        f"🕐 _Updated: {datetime.now().strftime('%H:%M · %d %b %Y')}_",
        f"📡 _Source: GSE Terminal_",
    ]
    return "\n".join(lines)


def market_summary(stocks: list[dict]) -> str:
    gainers  = [s for s in stocks if s["change"] > 0]
    losers   = [s for s in stocks if s["change"] < 0]
    flat     = [s for s in stocks if s["change"] == 0]
    total_vol = sum(s["volume"] for s in stocks)

    top_g = sorted(gainers, key=lambda x: x["pct"], reverse=True)[:5]
    top_l = sorted(losers,  key=lambda x: x["pct"])[:5]

    lines = [
        "📊 *GSE Market Summary*",
        f"_{datetime.now().strftime('%A, %d %b %Y · %H:%M')}_",
        "",
        f"🟢 Advancing: *{len(gainers)}*   🔴 Declining: *{len(losers)}*   ⚪ Flat: *{len(flat)}*",
        f"📦 Total Volume: *{fmt_vol(total_vol)}*",
        f"📋 Equities: *{len(stocks)}*",
        "",
        "🏆 *Top Gainers*",
    ]
    for s in top_g:
        lines.append(f"  🟢 `{s['ticker']:<10}` {fmt_price(s['price'])}  +{s['pct']:.2f}%")
    if not top_g:
        lines.append("  _No gainers today_")

    lines += ["", "📉 *Top Losers*"]
    for s in top_l:
        lines.append(f"  🔴 `{s['ticker']:<10}` {fmt_price(s['price'])}  {s['pct']:.2f}%")
    if not top_l:
        lines.append("  _No losers today_")

    lines += ["", "📡 _Data: GSE Terminal · dev.kwayisi.org_"]
    return "\n".join(lines)


# ── Keyboards ──────────────────────────────────────────────────────────────────
def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Market Board",  callback_data="cmd_market"),
            InlineKeyboardButton("🏆 Top Movers",    callback_data="cmd_top"),
        ],
        [
            InlineKeyboardButton("📰 Latest News",   callback_data="cmd_news"),
            InlineKeyboardButton("💰 Dividends",     callback_data="cmd_dividends"),
        ],
        [
            InlineKeyboardButton("🔍 Search Stock",  callback_data="cmd_search_prompt"),
            InlineKeyboardButton("❓ Help",           callback_data="cmd_help"),
        ],
    ])


def stock_keyboard(ticker: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh",       callback_data=f"refresh_{ticker}"),
            InlineKeyboardButton("📊 Full Profile",  callback_data=f"full_{ticker}"),
        ],
        [
            InlineKeyboardButton("⬅ Back to Market", callback_data="cmd_market"),
            InlineKeyboardButton("🏠 Main Menu",      callback_data="cmd_start"),
        ],
    ])


# ── Command Handlers ────────────────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"👋 Welcome, *{user.first_name}*!\n\n"
        "📈 *GSE Terminal Bot*\n"
        "Ghana Stock Exchange — live prices, news & analysis\n\n"
        "What would you like to do?"
    )
    msg = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
        await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())
    else:
        await msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *GSE Terminal — Commands*\n\n"
        "🔍 `/stock MTNGH` — Full stock profile\n"
        "📊 `/market` — Market summary + top movers\n"
        "🔎 `/search MTN` — Search by name or ticker\n"
        "🏆 `/top` — Top 5 gainers & losers\n"
        "📰 `/news` — Latest Ghana market news\n"
        "💰 `/dividends` — Upcoming dividends\n"
        "❓ `/help` — This message\n\n"
        "💡 *Tip:* Just type a ticker like `GCB` and I'll look it up!\n\n"
        "📧 attah.godsway999@gmail.com\n"
        "📱 +233 53 383 3623"
    )
    msg = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()
        await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())
    else:
        await msg.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())


async def cmd_stock(update: Update, ctx: ContextTypes.DEFAULT_TYPE, ticker: str = None):
    msg = update.message or update.callback_query.message

    # Resolve ticker from args or parameter
    if not ticker:
        if ctx.args:
            ticker = ctx.args[0].upper().strip()
        else:
            await msg.reply_text(
                "❓ Usage: `/stock MTNGH`\n\nOr just type a ticker like `GCB`",
                parse_mode=ParseMode.MARKDOWN
            )
            return

    loading = await msg.reply_text(f"⏳ Fetching *{ticker}*…", parse_mode=ParseMode.MARKDOWN)

    stocks = await get_all_stocks()
    stock  = next((s for s in stocks if s["ticker"] == ticker), None)

    if not stock:
        # Try partial match
        matches = [s for s in stocks if ticker in s["ticker"] or ticker in s["name"].upper()]
        if matches:
            stock = matches[0]
        else:
            await loading.edit_text(
                f"❌ Ticker *{ticker}* not found on GSE.\n\nTry `/search {ticker}` to find it.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_menu_keyboard()
            )
            return

    equity = await get_equity(stock["ticker"])
    text   = stock_card(stock, equity)
    await loading.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=stock_keyboard(stock["ticker"]))


async def cmd_market(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()

    loading = await msg.reply_text("⏳ Fetching live market data…")
    stocks  = await get_all_stocks()
    text    = market_summary(stocks)

    # Build a quick paginated list of all stocks (first 20)
    stock_lines = ["", "─" * 30, "📋 *All Equities*  _(tap to search)_", ""]
    for s in sorted(stocks, key=lambda x: x["ticker"])[:20]:
        ar   = "🟢" if s["change"] > 0 else ("🔴" if s["change"] < 0 else "⚪")
        sign = "+" if s["change"] > 0 else ""
        stock_lines.append(
            f"{ar} `{s['ticker']:<10}` {fmt_price(s['price'])}  {sign}{s['pct']:.2f}%"
        )
    stock_lines.append(f"\n_...and {max(0,len(stocks)-20)} more. Use /stock TICKER_")

    full_text = text + "\n" + "\n".join(stock_lines)

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh",       callback_data="cmd_market"),
            InlineKeyboardButton("🏆 Top Movers",    callback_data="cmd_top"),
        ],
        [InlineKeyboardButton("🏠 Main Menu",         callback_data="cmd_start")],
    ])
    await loading.edit_text(full_text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


async def cmd_top(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()

    loading = await msg.reply_text("⏳ Loading top movers…")
    stocks  = await get_all_stocks()
    gainers = sorted([s for s in stocks if s["change"] > 0], key=lambda x: x["pct"], reverse=True)[:5]
    losers  = sorted([s for s in stocks if s["change"] < 0], key=lambda x: x["pct"])[:5]
    volume  = sorted(stocks, key=lambda x: x["volume"], reverse=True)[:5]

    lines = [
        "🏆 *GSE Top Movers*",
        f"_{datetime.now().strftime('%d %b %Y · %H:%M')}_",
        "",
        "🟢 *Top Gainers*",
    ]
    for i, s in enumerate(gainers, 1):
        lines.append(f"  {i}. `{s['ticker']:<10}` {fmt_price(s['price'])}  +{s['pct']:.2f}%")
    if not gainers:
        lines.append("  _No gainers today_")

    lines += ["", "🔴 *Top Losers*"]
    for i, s in enumerate(losers, 1):
        lines.append(f"  {i}. `{s['ticker']:<10}` {fmt_price(s['price'])}  {s['pct']:.2f}%")
    if not losers:
        lines.append("  _No losers today_")

    lines += ["", "📦 *Most Traded (Volume)*"]
    for i, s in enumerate(volume, 1):
        lines.append(f"  {i}. `{s['ticker']:<10}` {fmt_vol(s['volume'])} shares")

    lines.append("\n_Use /stock TICKER for full profile_")

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh", callback_data="cmd_top"),
         InlineKeyboardButton("📊 Market",  callback_data="cmd_market")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="cmd_start")],
    ])
    await loading.edit_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = " ".join(ctx.args).upper().strip() if ctx.args else ""
    if not query:
        await update.message.reply_text(
            "🔍 Usage: `/search MTN`  or  `/search Ghana`",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    stocks = await get_all_stocks()
    matches = [
        s for s in stocks
        if query in s["ticker"] or query in s["name"].upper()
    ]

    if not matches:
        await update.message.reply_text(
            f"❌ No stocks found for *{query}*\n\nTry the ticker symbol (e.g. `MTNGH`, `GCB`)",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_keyboard()
        )
        return

    if len(matches) == 1:
        # Directly show the stock
        equity = await get_equity(matches[0]["ticker"])
        text   = stock_card(matches[0], equity)
        await update.message.reply_text(
            text, parse_mode=ParseMode.MARKDOWN,
            reply_markup=stock_keyboard(matches[0]["ticker"])
        )
        return

    # Multiple matches — show a selection keyboard
    lines = [f"🔍 *Results for \"{query}\"*  ({len(matches)} found)\n"]
    buttons = []
    for s in matches[:8]:
        ar = "🟢" if s["change"] > 0 else ("🔴" if s["change"] < 0 else "⚪")
        lines.append(f"{ar} `{s['ticker']:<10}` {s['name'][:24]}  {fmt_price(s['price'])}")
        buttons.append([InlineKeyboardButton(
            f"{s['ticker']} — {s['name'][:22]}",
            callback_data=f"stock_{s['ticker']}"
        )])
    if len(matches) > 8:
        lines.append(f"\n_...{len(matches)-8} more. Refine your search._")
    buttons.append([InlineKeyboardButton("🏠 Main Menu", callback_data="cmd_start")])

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def cmd_news(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()

    loading = await msg.reply_text("⏳ Fetching latest news…")
    articles = await get_news()

    if not articles:
        await loading.edit_text(
            "⚠️ Could not fetch news right now. Try again in a moment.",
            reply_markup=main_menu_keyboard()
        )
        return

    lines = [
        "📰 *Ghana Market News*",
        f"_{datetime.now().strftime('%d %b %Y · %H:%M')}_\n",
    ]
    for i, a in enumerate(articles[:8], 1):
        title = a["title"][:80] + ("…" if len(a["title"]) > 80 else "")
        src   = a["src"]
        url   = a.get("url", "")
        if url:
            lines.append(f"{i}. [{title}]({url})\n   _— {src}_\n")
        else:
            lines.append(f"{i}. *{title}*\n   _— {src}_\n")

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Refresh News", callback_data="cmd_news"),
         InlineKeyboardButton("📊 Market",       callback_data="cmd_market")],
        [InlineKeyboardButton("🏠 Main Menu",     callback_data="cmd_start")],
    ])
    await loading.edit_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN,
                            reply_markup=kb, disable_web_page_preview=True)


async def cmd_dividends(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message or update.callback_query.message
    if update.callback_query:
        await update.callback_query.answer()

    DIVS = [
        {"t":"MTNGH","co":"MTN Ghana",             "type":"INTERIM","dps":0.052,"yield":3.88,"ex":"2026-07-10","pay":"2026-08-01","upcoming":True,"days":24},
        {"t":"GCB",  "co":"Ghana Commercial Bank", "type":"FINAL",  "dps":0.42, "yield":6.77,"ex":"2026-06-01","pay":"2026-06-30","upcoming":False},
        {"t":"SCB",  "co":"Standard Chartered GH", "type":"INTERIM","dps":1.80, "yield":8.00,"ex":"2026-08-15","pay":"2026-09-05","upcoming":True,"days":60},
        {"t":"EGH",  "co":"Ecobank Ghana",          "type":"FINAL",  "dps":0.38, "yield":4.15,"ex":"2026-05-20","pay":"2026-06-15","upcoming":False},
        {"t":"CAL",  "co":"CAL Bank",               "type":"INTERIM","dps":0.045,"yield":5.23,"ex":"2026-09-01","pay":"2026-09-20","upcoming":True,"days":77},
        {"t":"TOTAL","co":"TotalEnergies GH",       "type":"FINAL",  "dps":0.28, "yield":8.19,"ex":"2026-04-10","pay":"2026-05-01","upcoming":False},
    ]

    lines = ["💰 *GSE Dividends*\n"]
    lines.append("⏳ *Upcoming*")
    for d in [x for x in DIVS if x["upcoming"]]:
        lines.append(
            f"  🎁 `{d['t']}`  ₵{d['dps']:.4f}/share  ({d['yield']:.2f}% yield)\n"
            f"      Ex-date: {d['ex']}  |  Pay: {d['pay']}\n"
            f"      _{d['type']} · In {d.get('days','')} days_\n"
        )
    lines.append("✅ *Recently Paid*")
    for d in [x for x in DIVS if not x["upcoming"]]:
        lines.append(
            f"  ✔ `{d['t']}`  ₵{d['dps']:.4f}/share  ({d['yield']:.2f}% yield)\n"
            f"      Ex: {d['ex']}  |  Paid: {d['pay']}\n"
        )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Market",   callback_data="cmd_market"),
         InlineKeyboardButton("🏠 Main Menu", callback_data="cmd_start")],
    ])
    await msg.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN, reply_markup=kb)


# ── Free-text message handler (type a ticker directly) ─────────────────────────
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip().upper()

    # If it looks like a ticker (2-10 uppercase chars / digits)
    if text and len(text) <= 10 and text.replace(" ", "").isalnum():
        stocks = await get_all_stocks()
        # Exact match
        stock = next((s for s in stocks if s["ticker"] == text), None)
        if stock:
            loading = await update.message.reply_text(f"⏳ Fetching *{text}*…", parse_mode=ParseMode.MARKDOWN)
            equity  = await get_equity(text)
            card    = stock_card(stock, equity)
            await loading.edit_text(card, parse_mode=ParseMode.MARKDOWN, reply_markup=stock_keyboard(text))
            return
        # Partial match
        matches = [s for s in stocks if text in s["ticker"] or text in s["name"].upper()]
        if matches:
            ctx.args = [text]
            await cmd_search(update, ctx)
            return

    # Default: show menu
    await update.message.reply_text(
        "💬 I didn't recognise that. Try:\n"
        "• Type a ticker: `MTNGH`, `GCB`, `SCB`\n"
        "• Use /stock MTNGH\n"
        "• Use /search MTN\n"
        "• Use /market for the full board",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard()
    )


# ── Callback Query Handler ─────────────────────────────────────────────────────
async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data  = query.data

    if data == "cmd_start":
        await cmd_start(update, ctx)
    elif data == "cmd_market":
        await cmd_market(update, ctx)
    elif data == "cmd_top":
        await cmd_top(update, ctx)
    elif data == "cmd_news":
        await cmd_news(update, ctx)
    elif data == "cmd_dividends":
        await cmd_dividends(update, ctx)
    elif data == "cmd_help":
        await cmd_help(update, ctx)
    elif data == "cmd_search_prompt":
        await query.answer()
        await query.message.reply_text(
            "🔍 Type: `/search MTN` or just type `GCB` directly",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data.startswith("stock_"):
        ticker = data.split("_", 1)[1]
        await query.answer()
        await cmd_stock(update, ctx, ticker=ticker)
    elif data.startswith("refresh_"):
        ticker = data.split("_", 1)[1]
        # Clear cache so it re-fetches
        _cache.pop("all_stocks", None)
        _cache.pop(f"equity_{ticker}", None)
        await query.answer("🔄 Refreshing…")
        await cmd_stock(update, ctx, ticker=ticker)
    elif data.startswith("full_"):
        ticker = data.split("_", 1)[1]
        await query.answer()
        await cmd_stock(update, ctx, ticker=ticker)
    else:
        await query.answer("Unknown action")


# ── Main ───────────────────────────────────────────────────────────────────────
async def post_init(app: Application):
    """Set bot commands menu."""
    await app.bot.set_my_commands([
        BotCommand("start",     "Welcome & main menu"),
        BotCommand("stock",     "Stock profile — /stock MTNGH"),
        BotCommand("market",    "Full market board"),
        BotCommand("search",    "Search stocks — /search MTN"),
        BotCommand("top",       "Top gainers & losers"),
        BotCommand("news",      "Latest Ghana market news"),
        BotCommand("dividends", "Upcoming dividends"),
        BotCommand("help",      "All commands"),
    ])
    logger.info("Bot commands registered ✓")


def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        raise ValueError(
            "Set your bot token!\n"
            "  export BOT_TOKEN='123456:ABC-your-token'\n"
            "  python bot.py"
        )

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Register handlers
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("stock",     cmd_stock))
    app.add_handler(CommandHandler("market",    cmd_market))
    app.add_handler(CommandHandler("top",       cmd_top))
    app.add_handler(CommandHandler("search",    cmd_search))
    app.add_handler(CommandHandler("news",      cmd_news))
    app.add_handler(CommandHandler("dividends", cmd_dividends))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 GSE Terminal Bot starting…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
