"""
Kira P&L sebenar dengan breakdown lengkap per pair
Formula: P&L = (MYR dapat dari jual) + (nilai crypto yang masih dipegang) - (MYR keluar beli) - fees
"""
import sys; sys.path.insert(0, '.')
from database.models import SessionLocal, Trade
from exchange.luno_client import luno_client

db = SessionLocal()
pairs = ["XBTMYR", "ETHMYR", "XRPMYR", "SOLMYR"]
prices = luno_client.get_all_prices(pairs)

grand_cost = grand_sell = grand_fees = grand_pnl = 0.0

print("=" * 65)
print(f"{'PAIR':<10} {'Keluar (Beli)':>14} {'Masuk (Jual)':>13} {'Nilai Tgn':>12} {'Fees':>8} {'P&L':>10}")
print("=" * 65)

for pair in pairs:
    p_data = prices.get(pair)
    live_price = p_data["last_trade"] if p_data else 0.0

    buys  = db.query(Trade).filter(Trade.pair == pair, Trade.trade_type == "BUY",  Trade.status == "COMPLETED").all()
    sells = db.query(Trade).filter(Trade.pair == pair, Trade.trade_type == "SELL", Trade.status == "COMPLETED").all()

    cost       = sum(t.amount_myr for t in buys)
    sold_myr   = sum(t.amount_myr for t in sells)
    fees       = sum(getattr(t, "fee_myr", 0.0) or 0.0 for t in buys + sells)
    vol_bought = sum(t.amount_btc for t in buys)
    vol_sold   = sum(t.amount_btc for t in sells)
    remaining  = max(0.0, vol_bought - vol_sold)
    curr_val   = remaining * live_price

    # P&L = Wang dapat dari jual + Nilai crypto dipegang sekarang - Wang keluar beli - Fees
    pnl = sold_myr + curr_val - cost - fees

    grand_cost += cost
    grand_sell += sold_myr
    grand_fees += fees
    grand_pnl  += pnl

    unit = pair[:3] if pair != "XBTMYR" else "BTC"
    print(f"{pair:<10} {'RM '+f'{cost:.2f}':>14} {'RM '+f'{sold_myr:.2f}':>13} {'RM '+f'{curr_val:.2f}':>12} {'RM '+f'{fees:.4f}':>8} {'RM '+f'{pnl:.2f}':>10}")

    # Detail breakdown
    for t in buys:
        print(f"  {'BUY':>5}: {t.amount_btc:.6f} {unit} @ RM{t.price_myr:,.4f} = RM{t.amount_myr:.2f}")
    for t in sells:
        print(f"  {'SELL':>5}: {t.amount_btc:.6f} {unit} @ RM{t.price_myr:,.4f} = RM{t.amount_myr:.2f} (P&L: RM{t.pnl_myr:.2f})")
    if remaining > 0:
        print(f"  {'HOLD':>5}: {remaining:.6f} {unit} @ RM{live_price:,.4f} = RM{curr_val:.2f} (unrealised)")

print("=" * 65)
pct = (grand_pnl / grand_cost * 100) if grand_cost > 0 else 0
print(f"{'TOTAL':<10} {'RM '+f'{grand_cost:.2f}':>14} {'RM '+f'{grand_sell:.2f}':>13} {'':>12} {'RM '+f'{grand_fees:.4f}':>8} {'RM '+f'{grand_pnl:.2f}':>10}")
print(f"\nPeratus Untung: {pct:.2f}%")
print(f"\nFormula: P&L = Jual ({grand_sell:.2f}) + Nilai Tgn - Beli ({grand_cost:.2f}) - Fees ({grand_fees:.4f})")

db.close()
