"""
mcp-server/server.py — MCP Server for Bitcoin Investment AI
Allows AI assistants to control and query the trading bot
"""
import asyncio
import json
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from loguru import logger

BACKEND_URL = "http://localhost:8000"

app = Server("bitcoin-investment-ai")


async def call_api(method: str, path: str, data: dict = None) -> dict:
    """Helper to call the backend API"""
    async with httpx.AsyncClient() as client:
        url = f"{BACKEND_URL}{path}"
        if method == "GET":
            resp = await client.get(url, timeout=10)
        elif method == "POST":
            resp = await client.post(url, json=data or {}, timeout=10)
        elif method == "PUT":
            resp = await client.put(url, json=data or {}, timeout=10)
        resp.raise_for_status()
        return resp.json()


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_bot_status",
            description="Dapatkan status bot (ON/OFF, next run time, version)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_price",
            description="Dapatkan harga Bitcoin/BTC semasa dalam Ringgit Malaysia (MYR)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_balance",
            description="Dapatkan baki akaun Luno (berapa RM dan BTC ada)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_portfolio",
            description="Dapatkan nilai portfolio semasa termasuk P&L (profit/loss)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_signal",
            description="Dapatkan signal pasaran semasa (BUY/SELL/HOLD) tanpa execute trade",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_trades",
            description="Dapatkan history semua trade (beli/jual)",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Berapa trade nak tengok (default: 10)",
                        "default": 10
                    }
                }
            }
        ),
        Tool(
            name="get_stats",
            description="Dapatkan statistik trading (total invest, P&L, win rate)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="get_settings",
            description="Dapatkan settings bot semasa (jumlah harian, threshold, dsb)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="update_settings",
            description="Update settings bot (tukar jumlah harian, threshold, dsb)",
            inputSchema={
                "type": "object",
                "properties": {
                    "daily_amount_myr": {
                        "type": "number",
                        "description": "Jumlah RM untuk invest setiap hari"
                    },
                    "buy_threshold_pct": {
                        "type": "number",
                        "description": "% penurunan harga sebelum beli (contoh: 1.5)"
                    },
                    "sell_threshold_pct": {
                        "type": "number",
                        "description": "% kenaikan harga sebelum jual (contoh: 2.0)"
                    },
                    "bot_enabled": {
                        "type": "boolean",
                        "description": "Aktifkan atau matikan bot"
                    }
                }
            }
        ),
        Tool(
            name="toggle_bot",
            description="Toggle bot ON atau OFF",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="trigger_trade_now",
            description="Jalankan trading job sekarang (tanpa tunggu jadual 8 pagi)",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "get_bot_status":
            data = await call_api("GET", "/api/status")
            status_emoji = "✅" if data.get("bot_enabled") else "❌"
            result = f"""
🤖 STATUS BOT INVESTMENT AI
{status_emoji} Status: {"AKTIF" if data.get("bot_enabled") else "DIMATIKAN"}
⏰ Run seterusnya: {data.get("next_run")}
🕐 Jadual: {data.get("schedule_time")} pagi setiap hari
            """.strip()

        elif name == "get_price":
            data = await call_api("GET", "/api/price")
            price = data.get("data", {})
            result = f"""
₿ HARGA BITCOIN SEMASA (LUNO)
💰 Harga: RM {price.get("last_trade", 0):,.2f}
📊 Bid: RM {price.get("bid", 0):,.2f}
📊 Ask: RM {price.get("ask", 0):,.2f}
            """.strip()

        elif name == "get_balance":
            data = await call_api("GET", "/api/balance")
            bal = data.get("data", {})
            result = f"""
💼 BAKI AKAUN LUNO
💵 Ringgit (MYR): RM {bal.get("MYR", 0):.2f}
₿  Bitcoin (BTC): {bal.get("XBT", 0):.8f} BTC
            """.strip()

        elif name == "get_portfolio":
            data = await call_api("GET", "/api/portfolio")
            pnl = data.get("total_pnl", 0)
            pnl_emoji = "📈" if pnl >= 0 else "📉"
            result = f"""
📦 PORTFOLIO SEMASA
₿  BTC: {data.get("btc_balance", 0):.8f} BTC
💵 Cash: RM {data.get("myr_balance", 0):.2f}
💰 Jumlah nilai: RM {data.get("total_value", 0):.2f}
{pnl_emoji} P&L: RM {pnl:+.2f} ({data.get("pnl_pct", 0):+.2f}%)
            """.strip()

        elif name == "get_signal":
            data = await call_api("GET", "/api/signal")
            action_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "💤"}.get(data.get("action"), "❓")
            result = f"""
🔍 SIGNAL PASARAN SEMASA
{action_emoji} Signal: {data.get("action")}
📊 Harga: RM {data.get("current_price", 0):,.2f}
📈 Perubahan: {data.get("price_change_pct", 0):+.2f}%
🔬 RSI: {data.get("rsi") or "N/A"}
💡 Sebab: {data.get("reason")}
🎯 Keyakinan: {data.get("confidence", 0) * 100:.0f}%
            """.strip()

        elif name == "get_trades":
            limit = arguments.get("limit", 10)
            trades = await call_api("GET", f"/api/trades?limit={limit}")
            if not trades:
                result = "Tiada trade lagi."
            else:
                lines = ["📝 HISTORY TRADE TERKINI\n"]
                for t in trades[:limit]:
                    emoji = "🟢" if t["type"] == "BUY" else "🔴"
                    lines.append(
                        f"{emoji} {t['type']} {t['amount_btc']:.6f} BTC @ RM{t['price_myr']:,.0f} "
                        f"({t['created_at'][:10]})"
                    )
                result = "\n".join(lines)

        elif name == "get_stats":
            data = await call_api("GET", "/api/trades/stats")
            result = f"""
📊 STATISTIK TRADING
Total Trade: {data.get("total_trades", 0)}
🟢 Beli: {data.get("total_buys", 0)} kali
🔴 Jual: {data.get("total_sells", 0)} kali
💰 Total Dilaburkan: RM {data.get("total_invested_myr", 0):.2f}
📈 Total Pulangan: RM {data.get("total_returned_myr", 0):.2f}
P&L: RM {data.get("total_pnl_myr", 0):+.2f}
🏆 Win Rate: {data.get("win_rate", 0):.1f}%
            """.strip()

        elif name == "get_settings":
            data = await call_api("GET", "/api/settings")
            result = f"""
⚙️ SETTINGS BOT SEMASA
💰 Jumlah harian: RM {data.get("daily_amount_myr", 5):.2f}
📉 Beli bila turun: {data.get("buy_threshold_pct", 1.5)}%
📈 Jual bila naik: {data.get("sell_threshold_pct", 2.0)}%
🔬 RSI beli: < {data.get("rsi_oversold", 30)}
🔬 RSI jual: > {data.get("rsi_overbought", 70)}
⏰ Jadual: {data.get("schedule_time")} pagi
💼 Modal max: RM {data.get("max_capital_myr", 100):.2f}
🤖 Bot aktif: {"Ya" if data.get("bot_enabled") else "Tidak"}
            """.strip()

        elif name == "update_settings":
            # Filter out None values
            update_data = {k: v for k, v in arguments.items() if v is not None}
            data = await call_api("PUT", "/api/settings", update_data)
            result = f"✅ Settings berjaya dikemaskini!\nPerubahan: {json.dumps(update_data, indent=2)}"

        elif name == "toggle_bot":
            data = await call_api("POST", "/api/bot/toggle")
            emoji = "✅" if data.get("bot_enabled") else "❌"
            result = f"{emoji} Bot sekarang: {data.get('status')}"

        elif name == "trigger_trade_now":
            data = await call_api("POST", "/api/bot/trigger")
            result = "🔥 Trading job sedang dijalankan! Semak log untuk hasilnya."

        else:
            result = f"❓ Tool '{name}' tidak dikenali"

        return [TextContent(type="text", text=result)]

    except Exception as e:
        logger.error(f"MCP tool error [{name}]: {e}")
        return [TextContent(type="text", text=f"❌ Error: {str(e)}\n\nPastikan backend server berjalan di port 8000")]


async def main():
    logger.info("🚀 Starting Bitcoin Investment AI MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
