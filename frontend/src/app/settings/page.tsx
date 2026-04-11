"use client";
import { useState, useEffect } from "react";
import { ArrowLeft, Save, AlertTriangle, ToggleLeft, ToggleRight } from "lucide-react";
import Link from "next/link";

const API = "http://localhost:8000/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    daily_amount_myr: 5.0,
    buy_threshold_pct: 1.5,
    sell_threshold_pct: 2.0,
    rsi_oversold: 30,
    rsi_overbought: 70,
    schedule_time: "08:00",
    max_capital_myr: 100.0,
    bot_enabled: true,
    target_baseline_myr: 100.0,
    rebalance_margin_pct: 2.0,
    base_price_myr: 0.0,
    trade_size_myr: 30.0,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetch(`${API}/settings`)
      .then(r => r.json())
      .then(d => { setSettings(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const save = async () => {
    setSaving(true);
    await fetch(`${API}/settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settings),
    });
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const inputClass = "w-full px-4 py-2.5 rounded-xl text-sm outline-none transition-all focus:ring-2";
  const inputStyle = {
    background: "rgba(255,255,255,0.05)",
    border: "1px solid rgba(255,255,255,0.1)",
    color: "#f1f5f9",
    focusRingColor: "#3b82f6"
  };

  return (
    <div className="min-h-screen" style={{ background: "linear-gradient(135deg, #0a0e1a 0%, #0d1525 100%)" }}>
      <header className="border-b px-6 py-4 flex items-center justify-between" style={{ borderColor: "#1e293b", background: "rgba(10,14,26,0.9)" }}>
        <div className="flex items-center gap-3">
          <Link href="/" className="p-2 rounded-lg" style={{ background: "rgba(255,255,255,0.05)" }}>
            <ArrowLeft size={18} style={{ color: "#94a3b8" }} />
          </Link>
          <h1 className="font-bold text-lg" style={{ color: "#f1f5f9" }}>⚙️ Tetapan Bot</h1>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-8">
        {/* Warning */}
        <div className="flex items-start gap-3 p-4 rounded-xl mb-6" style={{ background: "rgba(251,191,36,0.1)", border: "1px solid rgba(251,191,36,0.2)" }}>
          <AlertTriangle size={18} style={{ color: "#fbbf24", flexShrink: 0, marginTop: 2 }} />
          <p className="text-sm" style={{ color: "#fbbf24" }}>
            Perubahan settings akan aktif pada run seterusnya. Pastikan anda faham risiko sebelum ubah threshold.
          </p>
        </div>

        {loading ? (
          <p className="text-center py-16" style={{ color: "#64748b" }}>Memuat...</p>
        ) : (
          <div className="space-y-5">

            {/* Bot Toggle */}
            <div className="glass-card p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold" style={{ color: "#f1f5f9" }}>Status Bot</p>
                  <p className="text-sm mt-0.5" style={{ color: "#64748b" }}>Aktifkan atau matikan auto-trading</p>
                </div>
                <button onClick={() => setSettings(s => ({ ...s, bot_enabled: !s.bot_enabled }))}
                  style={{ color: settings.bot_enabled ? "#00d4aa" : "#64748b" }}>
                  {settings.bot_enabled ? <ToggleRight size={40} /> : <ToggleLeft size={40} />}
                </button>
              </div>
            </div>

            {/* Daily Investment */}
            <div className="glass-card p-5">
              <h3 className="font-semibold mb-4" style={{ color: "#f1f5f9" }}>💰 Pelaburan Harian</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm mb-2" style={{ color: "#94a3b8" }}>Jumlah Invest Setiap Hari (RM)</label>
                  <input type="number" min="2" max="1000" step="1"
                    value={settings.daily_amount_myr}
                    onChange={e => setSettings(s => ({ ...s, daily_amount_myr: parseFloat(e.target.value) }))}
                    className={inputClass}
                    style={{ ...inputStyle, border: "1px solid rgba(0,212,170,0.3)" }} />
                  <p className="text-xs mt-1" style={{ color: "#64748b" }}>Min: RM 2 (syarat Luno)</p>
                </div>
                <div>
                  <label className="block text-sm mb-2" style={{ color: "#94a3b8" }}>Modal Maksimum (RM)</label>
                  <input type="number" min="10" step="10"
                    value={settings.max_capital_myr}
                    onChange={e => setSettings(s => ({ ...s, max_capital_myr: parseFloat(e.target.value) }))}
                    className={inputClass}
                    style={inputStyle} />
                </div>
              </div>
            </div>

            {/* Strategy Thresholds */}
            <div className="glass-card p-5">
              <h3 className="font-semibold mb-4" style={{ color: "#f1f5f9" }}>📊 Strategy Thresholds</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm mb-2" style={{ color: "#94a3b8" }}>
                    🟢 Beli Bila Harga Jatuh (%) — Semasa: {settings.buy_threshold_pct}%
                  </label>
                  <input type="range" min="0.5" max="10" step="0.5"
                    value={settings.buy_threshold_pct}
                    onChange={e => setSettings(s => ({ ...s, buy_threshold_pct: parseFloat(e.target.value) }))}
                    className="w-full" />
                  <div className="flex justify-between text-xs mt-1" style={{ color: "#64748b" }}>
                    <span>0.5% (Agresif)</span><span>5% (Sederhana)</span><span>10% (Konservatif)</span>
                  </div>
                </div>
                <div>
                  <label className="block text-sm mb-2" style={{ color: "#94a3b8" }}>
                    🔴 Jual Bila Harga Naik (%) — Semasa: {settings.sell_threshold_pct}%
                  </label>
                  <input type="range" min="0.5" max="15" step="0.5"
                    value={settings.sell_threshold_pct}
                    onChange={e => setSettings(s => ({ ...s, sell_threshold_pct: parseFloat(e.target.value) }))}
                    className="w-full" />
                  <div className="flex justify-between text-xs mt-1" style={{ color: "#64748b" }}>
                    <span>0.5% (Agresif)</span><span>7.5% (Sederhana)</span><span>15% (Konservatif)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Rebalance Settings (Price-Step Grid) */}
            <div className="glass-card p-5">
              <h3 className="font-semibold mb-4" style={{ color: "#f1f5f9" }}>⚡ Grid Trading (Check 3-Minit)</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm mb-2" style={{ color: "#94a3b8" }}>Harga Semasa Rujukan (Base Price) RM</label>
                  <input type="number" step="0.01"
                    value={settings.base_price_myr || 0}
                    onChange={e => setSettings(s => ({ ...s, base_price_myr: parseFloat(e.target.value) || 0 }))}
                    className={inputClass}
                    style={{ ...inputStyle, border: "1px solid rgba(168,85,247,0.3)" }} />
                  <p className="text-xs mt-1" style={{ color: "#64748b" }}>Biarkan '0' jika ingin bot auto-kunci (lock) harga pasaran secara terus.</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm mb-2" style={{ color: "#94a3b8" }}>Saiz Tembakan Trade (RM)</label>
                    <input type="number" min="30" step="5"
                      value={settings.trade_size_myr}
                      onChange={e => setSettings(s => ({ ...s, trade_size_myr: parseFloat(e.target.value) }))}
                      className={inputClass} style={inputStyle} />
                    <p className="text-xs mt-1" style={{ color: "#64748b" }}>Minima Luno: ~RM 30</p>
                  </div>
                  <div>
                    <label className="block text-sm mb-2" style={{ color: "#94a3b8" }}>Margin Naik/Turun (%)</label>
                    <input type="number" min="0.5" max="10" step="0.5"
                      value={settings.rebalance_margin_pct}
                      onChange={e => setSettings(s => ({ ...s, rebalance_margin_pct: parseFloat(e.target.value) }))}
                      className={inputClass} style={inputStyle} />
                    <p className="text-xs mt-1" style={{ color: "#64748b" }}>Contoh: 1.5 atau 2.0</p>
                  </div>
                </div>
                
                <p className="text-xs mt-2 p-3 rounded" style={{ background: "rgba(168,85,247,0.1)", color: "#c084fc", border: "1px solid rgba(168,85,247,0.2)" }}>
                  Info: Bot akan sentiasa melontar <strong>RM {settings.trade_size_myr}</strong> 
                  apabila harga pasaran BTC berubah sebanyak <strong>{settings.rebalance_margin_pct}%</strong> dari Harga Rujukan. Harga Rujukan akan berpindah ikut harga terbaru.
                </p>
              </div>
            </div>

            {/* RSI Settings */}
            <div className="glass-card p-5">
              <h3 className="font-semibold mb-4" style={{ color: "#f1f5f9" }}>🔬 RSI Settings</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm mb-2" style={{ color: "#94a3b8" }}>RSI Beli (Oversold)</label>
                  <input type="number" min="10" max="50"
                    value={settings.rsi_oversold}
                    onChange={e => setSettings(s => ({ ...s, rsi_oversold: parseInt(e.target.value) }))}
                    className={inputClass} style={inputStyle} />
                  <p className="text-xs mt-1" style={{ color: "#64748b" }}>Default: 30</p>
                </div>
                <div>
                  <label className="block text-sm mb-2" style={{ color: "#94a3b8" }}>RSI Jual (Overbought)</label>
                  <input type="number" min="50" max="90"
                    value={settings.rsi_overbought}
                    onChange={e => setSettings(s => ({ ...s, rsi_overbought: parseInt(e.target.value) }))}
                    className={inputClass} style={inputStyle} />
                  <p className="text-xs mt-1" style={{ color: "#64748b" }}>Default: 70</p>
                </div>
              </div>
            </div>

            {/* Schedule */}
            <div className="glass-card p-5">
              <h3 className="font-semibold mb-4" style={{ color: "#f1f5f9" }}>⏰ Jadual Auto-Run</h3>
              <div>
                <label className="block text-sm mb-2" style={{ color: "#94a3b8" }}>Masa Run (24-jam format)</label>
                <input type="time"
                  value={settings.schedule_time}
                  onChange={e => setSettings(s => ({ ...s, schedule_time: e.target.value }))}
                  className={inputClass} style={{ ...inputStyle, border: "1px solid rgba(251,191,36,0.3)" }} />
                <p className="text-xs mt-1" style={{ color: "#64748b" }}>Bot akan auto beli/jual pada masa ini setiap hari (Waktu Malaysia)</p>
              </div>
            </div>

            {/* Save Button */}
            <button onClick={save} disabled={saving}
              className="w-full py-3.5 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all"
              style={{
                background: saved ? "rgba(0,212,170,0.2)" : "linear-gradient(135deg, #3b82f6, #2563eb)",
                color: saved ? "#00d4aa" : "white",
                border: saved ? "1px solid rgba(0,212,170,0.4)" : "none"
              }}>
              <Save size={18} />
              {saving ? "Menyimpan..." : saved ? "✅ Disimpan!" : "Simpan Tetapan"}
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
