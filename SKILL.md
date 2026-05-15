---
name: etoro-stock
description: "Fetch the user's live eToro portfolio status and deliver a combined briefing — portfolio up/down vs yesterday with per-position breakdown, news affecting held stocks, and growth opportunities in other stocks. Sends everything to WhatsApp and displays it in chat. Trigger this skill whenever the user asks about their eToro portfolio, asks 'how is my portfolio doing?', 'am I up or down today?', 'what's my eToro balance?', 'check my investments', 'portfolio update', 'how are my stocks doing?', 'what's my eToro status?', or any variation of wanting to know the current state of their eToro holdings, daily P&L, or investment performance. Use this skill proactively any time eToro, portfolio, or investment status is mentioned."
---

# eToro Portfolio Briefing

The user wants a full update on their eToro portfolio: current status, daily movement, news on their holdings, and growth opportunities elsewhere.

## Step 1 — Fetch portfolio data

Run the portfolio script:

```bash
python3 "$CLAUDE_PLUGIN_ROOT/scripts/etoro_portfolio.py"
```

Credentials are injected automatically via Claude Code's settings — no need to source `.bashrc`.

This outputs JSON with:
- `positions[]` — each holding: `ticker`, `name`, `current_value`, `daily_pnl`, `daily_pnl_pct`, `unrealized_pnl`
- `total_daily_pnl` — portfolio's total dollar change vs yesterday
- `total_daily_pnl_pct` — percentage change vs yesterday
- `total_portfolio_value` — current market value of all positions
- `total_unrealized_pnl` — total floating P&L from open prices
- `cash_balance` — uninvested cash
- `as_of` — timestamp

If `error` is set, explain the issue and stop (credentials not set, API down, etc.).

**Credentials setup** — if the script fails with a credentials error, tell the user:
> Set your eToro API keys in Claude Code's settings (`~/.claude/settings.json`) under the `env` key:
> ```json
> {
>   "env": {
>     "ETORO_API_KEY": "your_api_key_here",
>     "ETORO_USER_KEY": "your_user_key_here"
>   }
> }
> ```
> Get these from: eToro web → Settings → Trading → Create New Key (Real environment, Read permission)

## Step 2 — Research news (run in parallel)

Use WebSearch to find relevant news. Do **all searches simultaneously**:

1. **Holdings news**: For each ticker in `positions[]`, search: `"TICKER news today"` or `"TICKER stock news 2026"`. Focus on: earnings, analyst upgrades/downgrades, product launches, regulatory news, macro events that could move the stock. 2-3 sentences per holding.

2. **Growth opportunities**: Search for `"best stocks to buy this week 2026"` and `"stocks with strong momentum May 2026"`. Pick 3-4 that look compelling and summarize why in 1-2 sentences each. Prefer stocks with a concrete catalyst (earnings beat, new product, sector tailwind).

3. **Macro context**: Search for `"stock market today"` or `"market outlook 2026"` to get a 1-sentence read on overall market conditions.

## Step 3 — Compose the full briefing

Build a single message in this format (use WhatsApp-friendly markdown: `*bold*`, `_italic_`, line breaks):

```
📊 *eToro Portfolio — [as_of]*

[▲ or ▼] *Portfolio Today: [sign][total_daily_pnl_pct]% ([sign]$[total_daily_pnl])*
Total value: $[total_portfolio_value] | Cash: $[cash_balance]
Unrealized P&L (all time): [sign]$[total_unrealized_pnl]

━━━ *Your Holdings* ━━━
[For each position, sorted by biggest daily mover first:]
[▲/▼] *TICKER* — $[current_value]
   Today: [sign]$[daily_pnl] ([sign][daily_pnl_pct]%)
   📰 [1-2 sentences of news/context]

━━━ *Market Context* ━━━
[1-2 sentences on overall market conditions]

━━━ *Stocks to Watch* ━━━
[3-4 growth opportunities, each with ticker + 1-2 sentence rationale]

_Source: eToro API + Yahoo Finance | [as_of]_
```

Rules for the message:
- Use ▲ when the value is positive, ▼ when negative
- Include `+` sign for positive numbers
- Keep the whole message under 1,500 characters so it reads well on mobile
- If a position has no news, write "No major news today" instead of leaving it blank
- Keep news summaries tight — one strong sentence beats two weak ones

## Step 4 — Deliver via WhatsApp and chat

**Chat**: Display the formatted message in the conversation.

**WhatsApp**: Since the message can contain quotes and special chars, write it to a temp file first and read from stdin:

```bash
cat /tmp/etoro_msg.txt | python3 "$CLAUDE_PLUGIN_ROOT/scripts/send_etoro.py"
```

If WhatsApp env vars (`CALLMEBOT_PHONE`, `CALLMEBOT_KEY`) are not set, the script will print a setup message — tell the user to add them to `~/.claude/settings.json` under `env`:
> ```json
> {
>   "env": {
>     "CALLMEBOT_PHONE": "your_phone_number",
>     "CALLMEBOT_KEY": "your_callmebot_apikey"
>   }
> }
> ```
> Get your free CallMeBot API key by messaging `+34 644 63 67 97` on WhatsApp with: `I allow callmebot to send me messages`

If the WhatsApp send fails, tell the user briefly but don't treat it as a fatal error — the chat output is already there.

## Handling errors

- **No positions**: Tell the user their portfolio appears empty or their key may be for the wrong account (Demo vs Real).
- **HTTP 401**: API keys are invalid or expired — guide user to regenerate them.
- **HTTP 429**: Rate limit hit — wait 60 seconds and retry once.
- **Network error**: Fall back to telling the user the eToro API is unreachable and show any cached data if available.
