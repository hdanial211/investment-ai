import os
import re

files = [
    'backtesting result BTC',
    'backtesting result SOL',
    'backtesting result XRP',
    'backtesting result LTC',
    'backtesting result ETH'
]

markdown_content = "# Keputusan Keuntungan Bersih Mengikut Koin\n\n"
markdown_content += "Berikut adalah hasil analisis prestasi strategi yang diasingkan untuk setiap koin. Hanya memaparkan Top 5 Strategi dengan **Keuntungan Bersih Paling Tinggi** bagi setiap pasaran.\n\n"

for f in files:
    if not os.path.exists(f): continue
    coin = f.split()[-1]
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        
    experiments = re.split(r'## \d+\. Eksperimen: ', content)
    coin_results = []
    
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
                    
        coin_results.append({'name': name, 'pnl': pnl, 'wr': wr, 'dd': dd})

    # Sort by PnL
    coin_results = sorted(coin_results, key=lambda x: x['pnl'], reverse=True)
    
    markdown_content += f"## 🪙 {coin} (Modal: RM 1,000)\n"
    markdown_content += "| Kedudukan | Nama Strategi | Untung Bersih | Win Rate | Max Drawdown |\n"
    markdown_content += "| :--- | :--- | :--- | :--- | :--- |\n"
    
    for i, data in enumerate(coin_results[:5]):
        markdown_content += f"| #{i+1} | {data['name']} | **RM {data['pnl']:.2f}** | {data['wr']}% | {data['dd']}% |\n"
        
    markdown_content += "\n---\n\n"

# Add the final summary question
markdown_content += "## 🎯 Pilihan Awak\n"
markdown_content += "Awak boleh pilih satu strategi yang konsisten di semua koin, atau kita boleh buat sistem yang menggunakan strategi berbeza untuk koin yang berbeza (dinamik).\n\n"
markdown_content += "> [!IMPORTANT]\n"
markdown_content += "> Maklumkan pada saya jika awak sudah bersedia untuk pilih, kemudian kita akan siapkan `live_engine.py` dan push **v5.1.0** ke GitHub!"

# Write directly to the artifact file
artifact_path = r'C:\Users\User\.gemini\antigravity-ide\brain\43c2cc59-3dc4-46e4-9600-31f1a07b1a02\implementation_plan.md'
with open(artifact_path, 'w', encoding='utf-8') as f:
    f.write(markdown_content)
