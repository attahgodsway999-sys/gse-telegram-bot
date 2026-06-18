"""
GSE Terminal — Telegram Bot  v3
=================================
Ghana Stock Exchange live data bot.
API fields: name, price, change, volume
pct formula: change / (price - change) * 100

Contact: attah.godsway999@gmail.com · +233 53 383 3623
"""

import os, json, logging, asyncio, aiohttp, ssl
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (Application, CommandHandler, MessageHandler,
                           CallbackQueryHandler, ContextTypes, filters)
from telegram.constants import ParseMode

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN  = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
GSE_LIVE   = "https://dev.kwayisi.org/apis/gse/live"
GSE_EQUITY = "https://dev.kwayisi.org/apis/gse/equities/{}"
RSS2JSON   = "https://api.rss2json.com/v1/api.json?rss_url={}&count=8"
NEWS_FEEDS = [
    "https://thebftonline.com/feed/",
    "https://citibusinessnews.com/feed/",
    "https://www.myjoyonline.com/feed/",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
]

# Multiple CORS proxies — tried in sequence until one works
PROXIES = [
    lambda u: f"https://api.allorigins.win/get?url={u}",
    lambda u: f"https://corsproxy.io/?{u}",
    lambda u: f"https://api.codetabs.com/v1/proxy?quest={u}",
]

TIMEOUT = aiohttp.ClientTimeout(total=15)

NAMES = {
    "MTNGH":"MTN Ghana","GCB":"GCB Bank","SCB":"Standard Chartered",
    "EGH":"Ecobank Ghana","ETI":"Ecobank Transnat.","CAL":"CAL Bank",
    "ACCESS":"Access Bank","ADB":"Agric Dev Bank","AGA":"AngloGold Ashanti",
    "SOGEGH":"Société Générale","ALLGH":"Atlantic Lithium","ASG":"Asante Gold",
    "RBGH":"Republic Bank","SIC":"SIC Insurance","EGL":"Enterprise Group",
    "TOTAL":"TotalEnergies GH","GOIL":"GOIL Company","GGBL":"Guinness Ghana",
    "BOPP":"Benso Oil Palm","TLW":"Tullow Oil","GLD":"NewGold ETF",
    "FML":"Fan Milk","ZEN":"ZEN Petroleum","UNIL":"Unilever Ghana",
    "KASA":"Kasapreko","FAB":"First Atlantic Bank","HORDS":"Hords Ltd",
    "CLYD":"Clydestone","CMLT":"Camelot Ghana","CPC":"Cocoa Processing",
    "DASPHARMA":"Das Pharma","DIGICUT":"Digicut Ltd","MAC":"Mega African Cap",
    "MMH":"Meridian-Marshall","SAMBA":"Samba Foods","SCBPREF":"SCB Preference",
    "TBL":"Trust Bank","AADS":"AngloGold ADS","IIL":"Industrial Images",
}

# Exact snapshot from the GSE Terminal HTML (ALL39) — used when live fetch fails
# Fields match the real API: name, price, change, volume
SNAPSHOT = [
    {"name":"AADS",     "price":0.42,  "change":0,     "volume":841},
    {"name":"ACCESS",   "price":29.0,  "change":0,     "volume":1001},
    {"name":"ADB",      "price":5.3,   "change":0,     "volume":0},
    {"name":"AGA",      "price":37.0,  "change":0,     "volume":0},
    {"name":"ALLGH",    "price":8.46,  "change":0,     "volume":434},
    {"name":"ASG",      "price":8.89,  "change":0,     "volume":2},
    {"name":"BOPP",     "price":79.99, "change":0,     "volume":0},
    {"name":"CAL",      "price":0.77,  "change":0,     "volume":310013},
    {"name":"CLYD",     "price":2.5,   "change":0,     "volume":0},
    {"name":"CMLT",     "price":0.14,  "change":0,     "volume":0},
    {"name":"CPC",      "price":0.13,  "change":0,     "volume":0},
    {"name":"DASPHARMA","price":0.41,  "change":0,     "volume":0},
    {"name":"DIGICUT",  "price":0.09,  "change":0,     "volume":0},
    {"name":"EGH",      "price":41.0,  "change":0,     "volume":284},
    {"name":"EGL",      "price":10.05, "change":0,     "volume":9249},
    {"name":"ETI",      "price":2.29,  "change":0.04,  "volume":76977},
    {"name":"FAB",      "price":8.4,   "change":0.43,  "volume":8309},
    {"name":"FML",      "price":13.34, "change":0,     "volume":202},
    {"name":"GCB",      "price":36.0,  "change":0,     "volume":11494},
    {"name":"GGBL",     "price":12.99, "change":0,     "volume":416},
    {"name":"GLD",      "price":462.0, "change":-0.03, "volume":2},
    {"name":"GOIL",     "price":7.5,   "change":0,     "volume":2366},
    {"name":"HORDS",    "price":0.11,  "change":0,     "volume":103},
    {"name":"IIL",      "price":0.08,  "change":0,     "volume":5108},
    {"name":"KASA",     "price":1.45,  "change":0.13,  "volume":2455},
    {"name":"MAC",      "price":5.2,   "change":0,     "volume":0},
    {"name":"MMH",      "price":0.10,  "change":0,     "volume":0},
    {"name":"MTNGH",    "price":6.42,  "change":-0.03, "volume":488128},
    {"name":"RBGH",     "price":4.87,  "change":-0.13, "volume":7893},
    {"name":"SAMBA",    "price":0.55,  "change":0,     "volume":0},
    {"name":"SCB",      "price":71.38, "change":0,     "volume":2},
    {"name":"SCBPREF",  "price":0.9,   "change":0,     "volume":0},
    {"name":"SIC",      "price":5.18,  "change":0,     "volume":13084},
    {"name":"SOGEGH",   "price":6.85,  "change":0.05,  "volume":9476},
    {"name":"TBL",      "price":1.2,   "change":0,     "volume":0},
    {"name":"TLW",      "price":11.92, "change":0,     "volume":60},
    {"name":"TOTAL",    "price":36.3,  "change":0,     "volume":1456},
    {"name":"UNIL",     "price":29.5,  "change":0,     "volume":248},
    {"name":"ZEN",      "price":10.0,  "change":0,     "volume":40316},
]

watchlists: dict = {}
_cache = {"stocks": [], "ts": 0.0, "live": False}
TTL = 180  # seconds

# ── CORRECT percentage formula (matches the HTML app exactly) ─────────────────
def calc_pct(price: float, change: float) -> float:
    """
    Correct formula from the GSE Terminal HTML:
    a2p=(p,c)=>{ const v=p-c; return v ? (c/v*100) : 0 }
    i.e.  pct = change / prev_close * 100
    where prev_close = price - change
    """
    prev = price - change
    if prev == 0:
        return 0.0
    return round((change / prev) * 100, 2)

# ── Parse one raw API entry into a clean stock dict ───────────────────────────
def parse_one(raw: dict) -> dict | None:
    """
    API returns: {name, price, change, volume}
    'name' is the ticker symbol (e.g. "MTNGH")
    """
    try:
        ticker = str(raw.get("name") or raw.get("ticker") or raw.get("symbol") or "").upper().strip()
        price  = float(raw.get("price")  or 0)
        change = float(raw.get("change") or 0)
        volume = float(raw.get("volume") or 0)
        if not ticker or price <= 0:
            return None
        prev = round(price - change, 4)
        pct  = calc_pct(price, change)
        return {
            "t":    ticker,
            "name": NAMES.get(ticker, ticker),
            "p":    price,
            "c":    change,
            "pct":  pct,
            "v":    volume,
            "prev": prev,
        }
    except Exception:
        return None

# ── HTTP fetch with proxy fallback ────────────────────────────────────────────
async def fetch_url(session: aiohttp.ClientSession, url: str) -> dict | list | None:
    # 1. Try direct
    try:
        async with session.get(url, timeout=TIMEOUT) as r:
            if r.status == 200:
                data = await r.json(content_type=None)
                logger.info(f"Direct OK: {url[:55]}")
                return data
    except Exception as e:
        logger.warning(f"Direct failed ({url[:40]}): {e}")

    # 2. Try each proxy
    for i, proxy_fn in enumerate(PROXIES):
        try:
            proxy_url = proxy_fn(url)
            async with session.get(proxy_url, timeout=TIMEOUT) as r:
                if r.status != 200:
                    continue
                raw = await r.json(content_type=None)
                # allorigins wraps in {"contents": "...json string..."}
                if isinstance(raw, dict) and "contents" in raw:
                    contents = raw["contents"]
                    data = json.loads(contents) if isinstance(contents, str) else contents
                else:
                    data = raw
                logger.info(f"Proxy {i} OK: {url[:40]}")
                return data
        except Exception as e:
            logger.warning(f"Proxy {i} failed: {e}")

    logger.error(f"All fetches failed: {url}")
    return None

# ── Load stocks ───────────────────────────────────────────────────────────────
async def load_stocks(session: aiohttp.ClientSession) -> list:
    now = datetime.now().timestamp()

    # Return cache if still fresh
    if _cache["stocks"] and now - _cache["ts"] < TTL:
        return _cache["stocks"]

    data = await fetch_url(session, GSE_LIVE)

    if data:
        # API returns a list directly or wraps in {"data": [...]}
        raw_list = data if isinstance(data, list) else data.get("data", [])
        if isinstance(raw_list, list):
            parsed = [parse_one(s) for s in raw_list]
            stocks = [s for s in parsed if s is not None]
            if stocks:
                _cache["stocks"] = stocks
                _cache["ts"]     = now
                _cache["live"]   = True
                logger.info(f"Live data: {len(stocks)} stocks")
                return stocks

    # Live fetch failed — use snapshot
    logger.warning("Using offline snapshot")
    _cache["live"] = False
    if _cache["stocks"]:
        return _cache["stocks"]   # stale cache better than nothing

    stocks = [s for s in [parse_one(r) for r in SNAPSHOT] if s]
    _cache["stocks"] = stocks
    return stocks

async def load_equity(session: aiohttp.ClientSession, ticker: str) -> dict | None:
    return await fetch_url(session, GSE_EQUITY.format(ticker.lower()))

async def load_news(session: aiohttp.ClientSession) -> list:
    articles = []
    for feed_url in NEWS_FEEDS:
        try:
            data = await fetch_url(session, RSS2JSON.format(feed_url))
            if data and data.get("status") == "ok":
                for item in (data.get("items") or [])[:4]:
                    title = (item.get("title") or "").strip()
                    if title and len(title) > 10:
                        articles.append({
                            "title": title,
                            "url":   item.get("link", ""),
                        })
        except Exception as e:
            logger.warning(f"News feed error: {e}")
    return articles[:12]

# ── Formatting helpers ────────────────────────────────────────────────────────
def circle(c: float) -> str:
    return "🟢" if c > 0 else ("🔴" if c < 0 else "⚪")

def fmt_price(p: float) -> str:
    return f"₵{p:,.2f}"

def fmt_vol(v: float) -> str:
    if v >= 1_000_000: return f"{v/1_000_000:.2f}M"
    if v >= 1_000:     return f"{v/1_000:.1f}K"
    return str(int(v))

def fmt_mktcap(shares: float, price: float) -> str:
    val = shares * price
    if val >= 1e9: return f"₵{val/1e9:.2f}B"
    if val >= 1e6: return f"₵{val/1e6:.2f}M"
    return f"₵{val:,.0f}"

def fmt_change(change: float, pct: float) -> str:
    """
    Shows change and percentage CLEARLY with correct +/- signs:
      ₵+0.04  (+1.78%)   ← gained
      ₵-0.03  (-0.47%)   ← lost
       ₵0.00  (0.00%)    ← flat
    """
    if change > 0:
        return f"₵+{change:.2f}  (+{pct:.2f}%)"
    elif change < 0:
        return f"₵{change:.2f}  ({pct:.2f}%)"
    else:
        return f"₵0.00  (0.00%)"

# ── Stock card message ────────────────────────────────────────────────────────
def build_card(s: dict, detail: dict | None = None) -> str:
    tag = "🟡 _Offline snapshot_" if not _cache["live"] else ""
    lines = [
        f"{circle(s['c'])} *{s['t']}*  —  {s['name']}",
        "",
        f"💰 *Price:*       {fmt_price(s['p'])}",
        f"📊 *Change:*      {fmt_change(s['c'], s['pct'])}",
        f"🔙 *Prev Close:*  {fmt_price(s['prev'])}",
        f"📦 *Volume:*      {fmt_vol(s['v'])}",
    ]

    if detail:
        shares  = float(detail.get("shares") or detail.get("sharesInIssue") or 0)
        eps     = detail.get("eps")
        dps     = detail.get("dps")
        pe      = detail.get("pe") or detail.get("peRatio")
        sector  = detail.get("sector",   "")
        industry= detail.get("industry", "")
        lines.append("")
        if shares  : lines.append(f"🏢 *Mkt Cap:*     {fmt_mktcap(shares, s['p'])}")
        if sector  : lines.append(f"🏭 *Sector:*      {sector}")
        if industry: lines.append(f"🔧 *Industry:*    {industry}")
        if eps     : lines.append(f"📈 *EPS:*         ₵{float(eps):.4f}")
        if dps     : lines.append(f"💵 *DPS:*         ₵{float(dps):.4f}")
        if pe      : lines.append(f"📐 *P/E Ratio:*   {float(pe):.2f}×")

    lines += [
        "",
        f"⏰ `{datetime.now().strftime('%H:%M GMT  ·  %d %b %Y')}`",
    ]
    if tag:
        lines.append(tag)
    return "\n".join(lines)

def build_market(stocks: list) -> str:
    if not stocks:
        return "⚠️ No market data available right now. Try again shortly."

    gainers = [s for s in stocks if s["c"] > 0]
    losers  = [s for s in stocks if s["c"] < 0]
    flat    = [s for s in stocks if s["c"] == 0]
    tot_vol = sum(s["v"] for s in stocks)
    live_tag = "🟢 Live" if _cache["live"] else "🟡 Snapshot"

    top_g = sorted(gainers, key=lambda x: x["pct"], reverse=True)[:3]
    top_l = sorted(losers,  key=lambda x: x["pct"])[:3]

    lines = [
        "📊 *GSE Market Summary*",
        f"`{datetime.now().strftime('%a %d %b %Y  ·  %H:%M GMT')}`  {live_tag}",
        "",
        f"🟢 Advancing: *{len(gainers)}*   "
        f"🔴 Declining: *{len(losers)}*   "
        f"⚪ Flat: *{len(flat)}*",
        f"📦 Total Volume: *{fmt_vol(tot_vol)}*",
        f"📋 Equities listed: *{len(stocks)}*",
    ]

    if top_g:
        lines += ["", "🚀 *Top Gainers*"]
        for s in top_g:
            lines.append(
                f"  {circle(1)} `{s['t']:<10}` "
                f"{fmt_price(s['p'])}   *{fmt_change(s['c'], s['pct'])}*"
            )
    if top_l:
        lines += ["", "📉 *Top Losers*"]
        for s in top_l:
            lines.append(
                f"  {circle(-1)} `{s['t']:<10}` "
                f"{fmt_price(s['p'])}   *{fmt_change(s['c'], s['pct'])}*"
            )

    lines += ["", "💡 Type a ticker e.g. `MTNGH` for full details"]
    return "\n".join(lines)

# ── Keyboards ─────────────────────────────────────────────────────────────────
def kb_stock(t: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Full Profile",   callback_data=f"profile:{t}"),
         InlineKeyboardButton("⭐ Watchlist",      callback_data=f"watch:{t}")],
        [InlineKeyboardButton("🔄 Refresh",        callback_data=f"refresh:{t}"),
         InlineKeyboardButton("📊 Market",         callback_data="market")],
    ])

def kb_market() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏆 Top Movers",  callback_data="top"),
         InlineKeyboardButton("📰 News",        callback_data="news")],
        [InlineKeyboardButton("🔄 Refresh",     callback_data="market"),
         InlineKeyboardButton("⭐ Watchlist",   callback_data="watchlist")],
    ])

def kb_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Market Board",  callback_data="market"),
         InlineKeyboardButton("🏆 Top Movers",    callback_data="top")],
        [InlineKeyboardButton("📰 News",          callback_data="news"),
         InlineKeyboardButton("⭐ Watchlist",     callback_data="watchlist")],
    ])

# ── Core lookup helper ────────────────────────────────────────────────────────
async def do_lookup(update: Update, ticker: str, full: bool = False):
    msg = await update.message.reply_text(
        f"🔍 Looking up *{ticker}*…", parse_mode=ParseMode.MARKDOWN
    )
    async with aiohttp.ClientSession() as sess:
        stocks = await load_stocks(sess)
        stock  = next((s for s in stocks if s["t"] == ticker), None)
        if not stock:
            # Try partial match
            stock = next((s for s in stocks if ticker in s["t"]), None)
        detail = await load_equity(sess, ticker) if (full and stock) else None

    if not stock:
        near = [s["t"] for s in stocks if ticker[:3] in s["t"]]
        hint = "  ".join(f"`{t}`" for t in near[:5])
        txt  = f"❌ *{ticker}* not found on the GSE.\n\n"
        txt += f"Did you mean: {hint}" if hint else "Use /market to see all equities."
        await msg.edit_text(txt, parse_mode=ParseMode.MARKDOWN)
        return

    await msg.edit_text(
        build_card(stock, detail),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_stock(ticker)
    )

# ── Command Handlers ──────────────────────────────────────────────────────────
async def h_start(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = u.effective_user.first_name or "Investor"
    await u.message.reply_text(
        f"👋 Welcome, *{name}*!\n\n"
        "📈 *GSE Terminal Bot*\n"
        "Ghana Stock Exchange — live prices, news & portfolio\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🔍 *Just type any ticker to get live data:*\n"
        "`MTNGH`  `GCB`  `EGH`  `GOIL`  `SCB`\n\n"
        "📋 *Commands:*\n"
        "/market — Full market board\n"
        "/top — Top gainers & losers\n"
        "/news — Ghana business news\n"
        "/watchlist — Your saved stocks\n"
        "/help — All commands\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📧 attah.godsway999@gmail.com\n"
        "📞 +233 53 383 3623",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_main()
    )

async def h_help(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await u.message.reply_text(
        "📖 *GSE Terminal — All Commands*\n\n"
        "*/start* — Welcome screen\n"
        "*/market* — Full market summary\n"
        "*/top* — Top 5 gainers & losers\n"
        "*/search TICKER* — Quick price\n"
        "*/ticker TICKER* — Full profile (EPS, DPS, P/E)\n"
        "*/news* — Ghana business headlines\n"
        "*/watchlist* — Your saved stocks\n"
        "*/watch TICKER* — Add to watchlist\n"
        "*/unwatch TICKER* — Remove from watchlist\n"
        "*/help* — This message\n\n"
        "💡 *Tip:* Just type a ticker directly:\n"
        "`MTNGH` `GCB` `GOIL` `EGH` `CAL` `SIC`\n\n"
        "📞 +233 53 383 3623\n"
        "📧 attah.godsway999@gmail.com",
        parse_mode=ParseMode.MARKDOWN
    )

async def h_market(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = await u.message.reply_text("⏳ Fetching live GSE data…")
    async with aiohttp.ClientSession() as sess:
        stocks = await load_stocks(sess)
    await msg.edit_text(
        build_market(stocks),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_market()
    )

async def h_top(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = await u.message.reply_text("⏳ Loading top movers…")
    async with aiohttp.ClientSession() as sess:
        stocks = await load_stocks(sess)

    gainers = sorted([s for s in stocks if s["c"] > 0], key=lambda x: x["pct"], reverse=True)[:5]
    losers  = sorted([s for s in stocks if s["c"] < 0], key=lambda x: x["pct"])[:5]
    by_vol  = sorted(stocks, key=lambda x: x["v"], reverse=True)[:5]

    lines = [
        "🏆 *GSE Top Movers*",
        f"`{datetime.now().strftime('%d %b %Y  ·  %H:%M GMT')}`",
        "",
    ]
    if gainers:
        lines.append("🚀 *Top Gainers*")
        for i, s in enumerate(gainers, 1):
            lines.append(
                f"  {i}. `{s['t']:<10}` {fmt_price(s['p'])}   "
                f"*{fmt_change(s['c'], s['pct'])}*"
            )
    if losers:
        lines += ["", "📉 *Top Losers*"]
        for i, s in enumerate(losers, 1):
            lines.append(
                f"  {i}. `{s['t']:<10}` {fmt_price(s['p'])}   "
                f"*{fmt_change(s['c'], s['pct'])}*"
            )
    if not gainers and not losers:
        lines.append("⚪ No movers today — market is flat.")

    lines += ["", "📦 *Most Traded*"]
    for i, s in enumerate(by_vol, 1):
        lines.append(f"  {i}. `{s['t']:<10}` {fmt_vol(s['v'])} shares")

    lines.append("\n💡 Type any ticker for the full profile.")
    await msg.edit_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb_market()
    )

async def h_search(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await u.message.reply_text("Usage: `/search MTNGH`", parse_mode=ParseMode.MARKDOWN)
        return
    await do_lookup(u, ctx.args[0].upper(), full=False)

async def h_ticker(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await u.message.reply_text("Usage: `/ticker GCB`", parse_mode=ParseMode.MARKDOWN)
        return
    await do_lookup(u, ctx.args[0].upper(), full=True)

async def h_news(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = await u.message.reply_text("📰 Fetching Ghana business news…")
    async with aiohttp.ClientSession() as sess:
        articles = await load_news(sess)

    if not articles:
        await msg.edit_text(
            "⚠️ Could not fetch news right now.\n\n"
            "Try directly:\n"
            "• t.me/BFTOnline\n"
            "• thebftonline.com"
        )
        return

    lines = [
        "📰 *Ghana Business News*",
        f"`{datetime.now().strftime('%d %b %Y  ·  %H:%M')}`",
        "",
    ]
    for i, a in enumerate(articles[:10], 1):
        title = a["title"][:90] + ("…" if len(a["title"]) > 90 else "")
        url   = a.get("url", "")
        lines.append(f"{i}. [{title}]({url})" if url else f"{i}. {title}")

    await msg.edit_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

async def h_watchlist(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = u.effective_user.id
    wl  = watchlists.get(uid, set())
    if not wl:
        await u.message.reply_text(
            "⭐ Your watchlist is empty.\n\nAdd stocks: `/watch MTNGH`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    msg = await u.message.reply_text("⏳ Loading watchlist…")
    async with aiohttp.ClientSession() as sess:
        stocks = await load_stocks(sess)
    by_t  = {s["t"]: s for s in stocks}
    lines = [f"⭐ *Your Watchlist*  ({len(wl)} stocks)", ""]
    for t in sorted(wl):
        s = by_t.get(t)
        if s:
            lines.append(
                f"{circle(s['c'])} `{t:<10}` "
                f"{fmt_price(s['p'])}   `{fmt_change(s['c'], s['pct'])}`"
            )
        else:
            lines.append(f"⚪ `{t}` — not found")
    lines += ["", "💡 `/watch TICKER`  add   ·   `/unwatch TICKER`  remove"]
    await msg.edit_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

async def h_watch(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await u.message.reply_text("Usage: `/watch MTNGH`", parse_mode=ParseMode.MARKDOWN)
        return
    uid = u.effective_user.id
    t   = ctx.args[0].upper()
    watchlists.setdefault(uid, set()).add(t)
    await u.message.reply_text(
        f"⭐ *{t}* added to watchlist!\nView: /watchlist",
        parse_mode=ParseMode.MARKDOWN
    )

async def h_unwatch(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await u.message.reply_text("Usage: `/unwatch MTNGH`", parse_mode=ParseMode.MARKDOWN)
        return
    uid = u.effective_user.id
    t   = ctx.args[0].upper()
    watchlists.get(uid, set()).discard(t)
    await u.message.reply_text(
        f"✅ *{t}* removed from watchlist.",
        parse_mode=ParseMode.MARKDOWN
    )

async def h_text(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (u.message.text or "").strip().upper().split()[0]
    if 2 <= len(text) <= 12 and text.replace(".", "").isalnum():
        await do_lookup(u, text, full=False)
    else:
        await u.message.reply_text(
            "💬 Type a GSE ticker to get live data.\n"
            "Examples: `MTNGH`  `GCB`  `GOIL`  `SIC`\n\n"
            "Or /help for all commands.",
            parse_mode=ParseMode.MARKDOWN
        )

async def h_callback(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q   = u.callback_query
    await q.answer()
    d   = q.data
    uid = q.from_user.id

    async with aiohttp.ClientSession() as sess:

        if d == "market":
            stocks = await load_stocks(sess)
            await q.edit_message_text(
                build_market(stocks),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb_market()
            )

        elif d == "top":
            stocks  = await load_stocks(sess)
            gainers = sorted([s for s in stocks if s["c"] > 0], key=lambda x: x["pct"], reverse=True)[:5]
            losers  = sorted([s for s in stocks if s["c"] < 0], key=lambda x: x["pct"])[:5]
            lines   = ["🏆 *Top Movers*", ""]
            if gainers:
                lines.append("🚀 *Gainers*")
                for i, s in enumerate(gainers, 1):
                    lines.append(f"  {i}. `{s['t']:<10}` {fmt_price(s['p'])}   *{fmt_change(s['c'], s['pct'])}*")
            if losers:
                lines += ["", "📉 *Losers*"]
                for i, s in enumerate(losers, 1):
                    lines.append(f"  {i}. `{s['t']:<10}` {fmt_price(s['p'])}   *{fmt_change(s['c'], s['pct'])}*")
            if not gainers and not losers:
                lines.append("⚪ No movers today.")
            await q.edit_message_text(
                "\n".join(lines),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb_market()
            )

        elif d == "news":
            await q.edit_message_text("📰 Fetching…")
            articles = await load_news(sess)
            lines    = ["📰 *Ghana Business News*", ""]
            for i, a in enumerate(articles[:10], 1):
                title = a["title"][:90]
                url   = a.get("url", "")
                lines.append(f"{i}. [{title}]({url})" if url else f"{i}. {title}")
            await q.edit_message_text(
                "\n".join(lines),
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )

        elif d == "watchlist":
            wl = watchlists.get(uid, set())
            if not wl:
                await q.edit_message_text(
                    "⭐ Watchlist empty.\nAdd: `/watch MTNGH`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            stocks = await load_stocks(sess)
            by_t   = {s["t"]: s for s in stocks}
            lines  = [f"⭐ *Watchlist*  ({len(wl)} stocks)", ""]
            for t in sorted(wl):
                s = by_t.get(t)
                if s:
                    lines.append(f"{circle(s['c'])} `{t:<10}` {fmt_price(s['p'])}   `{fmt_change(s['c'], s['pct'])}`")
                else:
                    lines.append(f"⚪ `{t}` — not found")
            await q.edit_message_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

        elif d.startswith("profile:"):
            t = d.split(":", 1)[1]
            await q.edit_message_text(f"⏳ Loading *{t}*…", parse_mode=ParseMode.MARKDOWN)
            stocks = await load_stocks(sess)
            stock  = next((s for s in stocks if s["t"] == t), None)
            detail = await load_equity(sess, t) if stock else None
            if stock:
                await q.edit_message_text(
                    build_card(stock, detail),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=kb_stock(t)
                )

        elif d.startswith("refresh:"):
            t = d.split(":", 1)[1]
            _cache["ts"] = 0  # force fresh fetch
            stocks = await load_stocks(sess)
            stock  = next((s for s in stocks if s["t"] == t), None)
            if stock:
                await q.edit_message_text(
                    build_card(stock),
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=kb_stock(t)
                )

        elif d.startswith("watch:"):
            t = d.split(":", 1)[1]
            watchlists.setdefault(uid, set()).add(t)
            await q.answer(f"⭐ {t} added to watchlist!", show_alert=True)

async def h_error(u: Update, ctx: ContextTypes.DEFAULT_TYPE):
    logger.error("Error: %s", ctx.error, exc_info=ctx.error)

async def post_init(app: Application):
    await app.bot.set_my_commands([
        BotCommand("start",     "Welcome & guide"),
        BotCommand("market",    "Full GSE market board"),
        BotCommand("top",       "Top gainers & losers"),
        BotCommand("search",    "Quick price: /search MTNGH"),
        BotCommand("ticker",    "Full profile: /ticker GCB"),
        BotCommand("news",      "Ghana business news"),
        BotCommand("watchlist", "Your saved stocks"),
        BotCommand("watch",     "Add to watchlist"),
        BotCommand("unwatch",   "Remove from watchlist"),
        BotCommand("help",      "All commands"),
    ])
    logger.info("✅ Commands registered")

def main():
    if "YOUR_BOT_TOKEN" in BOT_TOKEN:
        print("❌ Set your BOT_TOKEN environment variable first.")
        print("   Get a token from @BotFather on Telegram.")
        return

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start",     h_start))
    app.add_handler(CommandHandler("help",      h_help))
    app.add_handler(CommandHandler("market",    h_market))
    app.add_handler(CommandHandler("top",       h_top))
    app.add_handler(CommandHandler("search",    h_search))
    app.add_handler(CommandHandler("ticker",    h_ticker))
    app.add_handler(CommandHandler("news",      h_news))
    app.add_handler(CommandHandler("watchlist", h_watchlist))
    app.add_handler(CommandHandler("watch",     h_watch))
    app.add_handler(CommandHandler("unwatch",   h_unwatch))
    app.add_handler(CallbackQueryHandler(h_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, h_text))
    app.add_error_handler(h_error)

    logger.info("🚀 GSE Terminal Bot running…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
