"""Parse Luno MYR pairs and rank for grid trading suitability"""
import json

raw = '{"tickers":[{"pair":"AAVEMYR","timestamp":1776526598675,"bid":"446.65","ask":"448.41","last_trade":"447.61","rolling_24_hour_volume":"214.5342"},{"pair":"ADAMYR","timestamp":1776526598649,"bid":"0.9946","ask":"0.9947","last_trade":"0.9946","rolling_24_hour_volume":"586856.84"},{"pair":"ALGOMYR","timestamp":1776526597566,"bid":"0.4313","ask":"0.4385","last_trade":"0.4342","rolling_24_hour_volume":"1136330.52"},{"pair":"ARBMYR","timestamp":1776526595415,"bid":"0.5061","ask":"0.5118","last_trade":"0.5118","rolling_24_hour_volume":"49574.33"},{"pair":"ATOMMYR","timestamp":1776526584272,"bid":"7.10","ask":"7.11","last_trade":"7.11","rolling_24_hour_volume":"7713.2002"},{"pair":"AVAXMYR","timestamp":1776526598667,"bid":"37.30","ask":"37.31","last_trade":"37.33","rolling_24_hour_volume":"6357.2936"},{"pair":"BCHMYR","timestamp":1776526597939,"bid":"1767.00","ask":"1768.00","last_trade":"1768.00","rolling_24_hour_volume":"23.7155"},{"pair":"CRVMYR","timestamp":1776526598666,"bid":"0.9198","ask":"0.9199","last_trade":"0.92","rolling_24_hour_volume":"434871.60"},{"pair":"DOTMYR","timestamp":1776526598694,"bid":"5.11","ask":"5.12","last_trade":"5.12","rolling_24_hour_volume":"20929.57"},{"pair":"ETHMYR","timestamp":1776526598658,"bid":"9356.00","ask":"9357.00","last_trade":"9355.00","rolling_24_hour_volume":"246.6573"},{"pair":"GRTMYR","timestamp":1776526549096,"bid":"0.1006","ask":"0.1007","last_trade":"0.1007","rolling_24_hour_volume":"1422842.00"},{"pair":"HBARMYR","timestamp":1776526590949,"bid":"0.3577","ask":"0.3607","last_trade":"0.3614","rolling_24_hour_volume":"69133.27"},{"pair":"JUPMYR","timestamp":1776526570365,"bid":"0.7122","ask":"0.7259","last_trade":"0.7259","rolling_24_hour_volume":"6390.70"},{"pair":"LINKMYR","timestamp":1776526597473,"bid":"37.21","ask":"37.22","last_trade":"37.24","rolling_24_hour_volume":"1473.93"},{"pair":"LTCMYR","timestamp":1776526598282,"bid":"221.00","ask":"222.00","last_trade":"222.00","rolling_24_hour_volume":"157.8716"},{"pair":"NEARMYR","timestamp":1776526598601,"bid":"5.4118","ask":"5.4994","last_trade":"5.4135","rolling_24_hour_volume":"5291.40"},{"pair":"ONDOMYR","timestamp":1776526549388,"bid":"1.0299","ask":"1.042","last_trade":"1.042","rolling_24_hour_volume":"79191.11"},{"pair":"POLMYR","timestamp":1776526598689,"bid":"0.3563","ask":"0.3564","last_trade":"0.3565","rolling_24_hour_volume":"321047.21"},{"pair":"RENDERMYR","timestamp":1776526598552,"bid":"7.2218","ask":"7.4473","last_trade":"7.3012","rolling_24_hour_volume":"3390.44"},{"pair":"SKYMYR","timestamp":1776526594147,"bid":"0.305","ask":"0.3051","last_trade":"0.3045","rolling_24_hour_volume":"547401.00"},{"pair":"SNXMYR","timestamp":1776526598184,"bid":"1.20","ask":"1.21","last_trade":"1.21","rolling_24_hour_volume":"157821.71"},{"pair":"SOLMYR","timestamp":1776526598695,"bid":"343.59","ask":"343.60","last_trade":"343.52","rolling_24_hour_volume":"2962.0261"},{"pair":"SUIMYR","timestamp":1776526500675,"bid":"3.93","ask":"4.0555","last_trade":"4.0555","rolling_24_hour_volume":"18434.56"},{"pair":"TAOMYR","timestamp":1776526574149,"bid":"1005.00","ask":"1031.00","last_trade":"1031.00","rolling_24_hour_volume":"19.5742"},{"pair":"TONMYR","timestamp":1776526507346,"bid":"5.5001","ask":"5.6475","last_trade":"5.6475","rolling_24_hour_volume":"239.16"},{"pair":"TRXMYR","timestamp":1776526569655,"bid":"1.3001","ask":"1.3135","last_trade":"1.3135","rolling_24_hour_volume":"7888.64"},{"pair":"UNIMYR","timestamp":1776526568469,"bid":"13.41","ask":"13.42","last_trade":"13.44","rolling_24_hour_volume":"5522.74"},{"pair":"XBTMYR","timestamp":1776526582522,"bid":"301602.00","ask":"301603.00","last_trade":"301603.00","rolling_24_hour_volume":"18.628237"},{"pair":"XLMMYR","timestamp":1776526598507,"bid":"0.6714","ask":"0.6715","last_trade":"0.672","rolling_24_hour_volume":"135156.00"},{"pair":"XRPMYR","timestamp":1776526598698,"bid":"5.6913","ask":"5.6914","last_trade":"5.6914","rolling_24_hour_volume":"531113.00"}]}'

data = json.loads(raw)['tickers']

results = []
for t in data:
    bid = float(t['bid'])
    ask = float(t['ask'])
    price = float(t['last_trade'])
    vol = float(t['rolling_24_hour_volume'])
    if price == 0: continue
    
    # Spread % (lower = tighter = better for grid)
    spread_pct = (ask - bid) / price * 100 if price > 0 else 999
    
    # Volume in MYR
    vol_myr = vol * price
    
    results.append({
        'pair': t['pair'],
        'price': price,
        'spread_pct': spread_pct,
        'vol_myr': vol_myr,
        'vol_units': vol,
    })

# Score: tight spread (most important) + high volume
for r in results:
    # Normalized: lower spread = better, higher vol = better
    # Grid needs: tight spread (so 2-5% margin actually profits after spread cost)
    # and enough volume (orders fill quickly)
    spread_score = max(0, 10 - r['spread_pct'] * 100)  # < 0.1% spread = 10pts
    
    # Log scale volume (unit volume matters for altcoins)
    import math
    vol_score = min(10, math.log10(max(1, r['vol_myr'])) - 3)  # RM10k = 1pt, RM1M = 3pt
    
    r['score'] = spread_score + vol_score

results.sort(key=lambda x: x['score'], reverse=True)

print(f"{'Pair':<12} {'Price':>10} {'Spread%':>9} {'Vol MYR':>14} {'Score':>7}")
print("-"*58)
for r in results[:20]:
    print(f"{r['pair']:<12} {r['price']:>10.4f} {r['spread_pct']:>8.4f}% {r['vol_myr']:>14,.0f} {r['score']:>7.2f}")
