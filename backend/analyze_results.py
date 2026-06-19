import os
import re

files = [
    'backtesting result BTC',
    'backtesting result SOL',
    'backtesting result XRP',
    'backtesting result LTC',
    'backtesting result ETH'
]

results = {}

for f in files:
    if not os.path.exists(f): continue
    coin = f.split()[-1]
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        
    experiments = re.split(r'## \d+\. Eksperimen: ', content)
    for exp in experiments[1:]: # Skip the first part
        lines = exp.strip().split('\n')
        name = lines[0].strip()
        
        pnl = 0
        wr = ""
        dd = ""
        
        for line in lines:
            if "Untung Bersih:" in line:
                match = re.search(r'RM\s*(-?[\d\.]+)', line)
                if match:
                    pnl = float(match.group(1))
            if "Win Rate:" in line:
                match = re.search(r'([\d\.]+)%', line)
                if match:
                    wr = float(match.group(1))
            if "Max Drawdown:" in line:
                match = re.search(r'([\d\.]+)%', line)
                if match:
                    dd = float(match.group(1))
                    
        if name not in results:
            results[name] = {'pnl': 0, 'coins': [], 'wr_avg': [], 'dd_avg': []}
            
        results[name]['pnl'] += pnl
        results[name]['coins'].append(coin)
        if isinstance(wr, float): results[name]['wr_avg'].append(wr)
        if isinstance(dd, float): results[name]['dd_avg'].append(dd)

# Calculate averages and sort by total PnL
sorted_results = sorted(results.items(), key=lambda x: x[1]['pnl'], reverse=True)

print("TOP STRATEGIES OVERALL PNL (Across All Coins):")
for name, data in sorted_results[:10]:
    avg_wr = sum(data['wr_avg'])/len(data['wr_avg']) if data['wr_avg'] else 0
    avg_dd = sum(data['dd_avg'])/len(data['dd_avg']) if data['dd_avg'] else 0
    print(f"- {name}")
    print(f"  Total PnL: RM {data['pnl']:.2f}")
    print(f"  Avg Win Rate: {avg_wr:.2f}% | Avg Drawdown: {avg_dd:.2f}%")
    print(f"  Passed Coins: {len(data['coins'])}/5")
    print()
