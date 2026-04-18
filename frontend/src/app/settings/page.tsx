"use client";
import { useState, useEffect, useCallback } from "react";
import {
  ArrowLeft, Save, AlertTriangle, ToggleLeft, ToggleRight,
  Zap, TrendingUp, Shield, Settings2, Bitcoin, RefreshCw,
  CheckCircle2, ChevronDown, ChevronUp
} from "lucide-react";
import Link from "next/link";

const API = "http://localhost:8000/api";

const PAIR_META: Record<string, { icon: string; color: string; label: string; ticker: string }> = {
  XBTMYR: { icon: "₿",  color: "#f7931a", label: "Bitcoin",  ticker: "BTC" },
  ETHMYR: { icon: "Ξ",  color: "#627eea", label: "Ethereum", ticker: "ETH" },
  XRPMYR: { icon: "✕",  color: "#346aa9", label: "XRP",      ticker: "XRP" },
  SOLMYR: { icon: "◎",  color: "#9945ff", label: "Solana",   ticker: "SOL" },
};

type GridState = {
  pair: string;
  display_name: string;
  enabled: boolean;
  base_price_myr: number;
  rebalance_margin_pct: number;
  trade_size_myr: number;
  current_price?: number;
};

type BotSettings = {
  bot_enabled: boolean;
  max_capital_myr: number;
  daily_amount_myr: number;
};

export default function SettingsPage() {
  const [botSettings, setBotSettings]   = useState<BotSettings>({ bot_enabled: true, max_capital_myr: 200, daily_amount_myr: 5 });
  const [grids, setGrids]               = useState<GridState[]>([]);
  const [loading, setLoading]           = useState(true);
  const [saving, setSaving]             = useState(false);
  const [saved, setSaved]               = useState<string | null>(null);
  const [expanded, setExpanded]         = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      const [s, g] = await Promise.all([
        fetch(`${API}/settings`).then(r => r.json()),
        fetch(`${API}/grid-states`).then(r => r.json()),
      ]);
      setBotSettings({ bot_enabled: s.bot_enabled, max_capital_myr: s.max_capital_myr, daily_amount_myr: s.daily_amount_myr });
      setGrids(g);
    } catch (_) {}
    setLoading(false);
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const saveBotSettings = async () => {
    setSaving(true);
    await fetch(`${API}/settings`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(botSettings),
    });
    setSaving(false);
    setSaved("global");
    setTimeout(() => setSaved(null), 2500);
  };

  const saveGrid = async (gs: GridState) => {
    setSaving(true);
    try {
      await fetch(`${API}/grid-states/${gs.pair}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          base_price_myr:      gs.base_price_myr,
          rebalance_margin_pct: gs.rebalance_margin_pct,
          trade_size_myr:      gs.trade_size_myr,
        }),
      });
      // Toggle enabled separately
      await fetch(`${API}/grid-states/${gs.pair}/${gs.enabled ? "enable" : "disable"}`, { method: "POST" });
      setSaved(gs.pair);
      setTimeout(() => setSaved(null), 2500);
    } catch (_) {}
    setSaving(false);
  };

  const updateGrid = (pair: string, key: keyof GridState, val: any) => {
    setGrids(prev => prev.map(g => g.pair === pair ? { ...g, [key]: val } : g));
  };

  // ── Helpers ──────────────────────────────────────────────────────────
  const SliderRow = ({ label, value, min, max, step, onChange, unit = "", hint = "" }: any) => (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs" style={{ color: "#94a3b8" }}>{label}</span>
        <span className="text-xs font-bold px-2 py-0.5 rounded-md" style={{ background: "rgba(0,212,170,0.1)", color: "#00d4aa" }}>
          {value}{unit}
        </span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
        style={{ accentColor: "#00d4aa" }} />
      {hint && <p className="text-[11px] mt-1" style={{ color: "#475569" }}>{hint}</p>}
    </div>
  );

  const NumberInput = ({ label, value, min, step, onChange, unit = "RM", hint = "" }: any) => (
    <div>
      <label className="block text-xs mb-1.5" style={{ color: "#94a3b8" }}>{label}</label>
      <div className="flex items-center gap-2 px-3 py-2 rounded-xl" style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.1)" }}>
        <span className="text-xs" style={{ color: "#64748b" }}>{unit}</span>
        <input type="number" min={min} step={step} value={value}
          onChange={e => onChange(parseFloat(e.target.value) || 0)}
          className="flex-1 bg-transparent outline-none text-sm"
          style={{ color: "#f1f5f9" }} />
      </div>
      {hint && <p className="text-[11px] mt-1" style={{ color: "#475569" }}>{hint}</p>}
    </div>
  );

  return (
    <div className="min-h-screen" style={{ background: "linear-gradient(135deg, #0a0e1a 0%, #0d1525 100%)" }}>
      {/* Header */}
      <header className="sticky top-0 z-10 border-b px-5 py-4 flex items-center justify-between backdrop-blur-md"
        style={{ borderColor: "#1e293b", background: "rgba(10,14,26,0.92)" }}>
        <div className="flex items-center gap-3">
          <Link href="/" className="p-2 rounded-xl transition-all hover:bg-white/10"
            style={{ background: "rgba(255,255,255,0.05)" }}>
            <ArrowLeft size={16} style={{ color: "#94a3b8" }} />
          </Link>
          <div>
            <h1 className="font-bold" style={{ color: "#f1f5f9" }}>Tetapan Bot</h1>
            <p className="text-[11px]" style={{ color: "#475569" }}>Grid Trading Configuration</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchAll} className="p-2 rounded-xl transition-all hover:bg-white/10"
            style={{ background: "rgba(255,255,255,0.05)" }}>
            <RefreshCw size={14} style={{ color: "#64748b" }} />
          </button>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-6 space-y-4">

        {/* Notice */}
        <div className="flex items-start gap-3 px-4 py-3 rounded-xl"
          style={{ background: "rgba(251,191,36,0.08)", border: "1px solid rgba(251,191,36,0.15)" }}>
          <AlertTriangle size={14} style={{ color: "#fbbf24", flexShrink: 0, marginTop: 2 }} />
          <p className="text-xs" style={{ color: "#fbbf24" }}>
            Perubahan aktif pada run seterusnya (max 3 minit). Jangan ubah <strong>Margin %</strong> terlalu rendah — boleh jadi too many trades.
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: "#00d4aa", borderTopColor: "transparent" }} />
          </div>
        ) : (
          <>
            {/* ── Bot Global Settings ─────────────────────────────── */}
            <div className="rounded-2xl overflow-hidden" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <div className="px-5 py-4 flex items-center gap-3 border-b" style={{ borderColor: "rgba(255,255,255,0.07)" }}>
                <div className="p-2 rounded-xl" style={{ background: "rgba(0,212,170,0.1)" }}>
                  <Settings2 size={16} style={{ color: "#00d4aa" }} />
                </div>
                <div>
                  <p className="text-sm font-semibold" style={{ color: "#f1f5f9" }}>Tetapan Global</p>
                  <p className="text-[11px]" style={{ color: "#475569" }}>Kawalan utama bot</p>
                </div>
              </div>
              <div className="p-5 space-y-4">
                {/* Bot Toggle */}
                <div className="flex items-center justify-between p-3 rounded-xl" style={{ background: "rgba(255,255,255,0.03)" }}>
                  <div>
                    <p className="text-sm font-medium" style={{ color: "#f1f5f9" }}>Auto-Trading</p>
                    <p className="text-[11px]" style={{ color: "#64748b" }}>Bot aktif beli/jual secara automatik</p>
                  </div>
                  <button onClick={() => setBotSettings(s => ({ ...s, bot_enabled: !s.bot_enabled }))}
                    style={{ color: botSettings.bot_enabled ? "#00d4aa" : "#475569", transition: "color 0.2s" }}>
                    {botSettings.bot_enabled ? <ToggleRight size={44} /> : <ToggleLeft size={44} />}
                  </button>
                </div>

                <NumberInput
                  label="Modal Maksimum Portfolio (RM)"
                  value={botSettings.max_capital_myr}
                  min={50} step={10}
                  onChange={(v: number) => setBotSettings(s => ({ ...s, max_capital_myr: v }))}
                  hint="Had maksimum dana yang bot boleh guna merata semua pair" />

                <button onClick={saveBotSettings} disabled={saving}
                  className="w-full py-2.5 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-all"
                  style={{
                    background: saved === "global" ? "rgba(0,212,170,0.15)" : "linear-gradient(135deg, #3b82f6, #2563eb)",
                    color: saved === "global" ? "#00d4aa" : "white",
                    border: saved === "global" ? "1px solid rgba(0,212,170,0.3)" : "none"
                  }}>
                  {saved === "global" ? <><CheckCircle2 size={15} /> Disimpan!</> : <><Save size={15} /> Simpan Tetapan Global</>}
                </button>
              </div>
            </div>

            {/* ── Per-Pair Grid Settings ──────────────────────────── */}
            <div>
              <p className="text-xs font-semibold mb-3 flex items-center gap-2" style={{ color: "#64748b" }}>
                <Zap size={12} style={{ color: "#00d4aa" }} />
                GRID CONFIG PER PAIR
              </p>
              <div className="space-y-3">
                {grids.map(gs => {
                  const meta  = PAIR_META[gs.pair] ?? { icon: "●", color: "#94a3b8", label: gs.pair, ticker: gs.pair.slice(0,3) };
                  const isExp = expanded === gs.pair;
                  const nextBuy  = gs.base_price_myr > 0 ? gs.base_price_myr * (1 - gs.rebalance_margin_pct / 100) : null;
                  const nextSell = gs.base_price_myr > 0 ? gs.base_price_myr * (1 + gs.rebalance_margin_pct / 100) : null;

                  return (
                    <div key={gs.pair} className="rounded-2xl overflow-hidden transition-all"
                      style={{ background: "rgba(255,255,255,0.03)", border: `1px solid ${isExp ? meta.color + "30" : "rgba(255,255,255,0.08)"}` }}>

                      {/* Header Row */}
                      <button className="w-full px-5 py-4 flex items-center gap-3"
                        onClick={() => setExpanded(isExp ? null : gs.pair)}>
                        <div className="w-9 h-9 rounded-xl flex items-center justify-center text-base font-bold flex-shrink-0"
                          style={{ background: meta.color + "18", color: meta.color }}>
                          {meta.icon}
                        </div>
                        <div className="flex-1 text-left">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold" style={{ color: "#f1f5f9" }}>{meta.label}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded-md font-mono"
                              style={{ background: meta.color + "15", color: meta.color }}>{meta.ticker}/MYR</span>
                          </div>
                          <div className="flex items-center gap-3 mt-0.5">
                            <span className="text-[11px]" style={{ color: "#475569" }}>
                              RM {gs.trade_size_myr} · {gs.rebalance_margin_pct}% margin
                            </span>
                            {gs.current_price && (
                              <span className="text-[11px]" style={{ color: "#64748b" }}>
                                RM {gs.current_price.toLocaleString("ms-MY", { maximumFractionDigits: 0 })}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {/* Enable/Disable toggle inline */}
                          <div onClick={e => { e.stopPropagation(); updateGrid(gs.pair, "enabled", !gs.enabled); }}
                            style={{ color: gs.enabled ? "#00d4aa" : "#475569", transition: "color 0.2s" }}>
                            {gs.enabled ? <ToggleRight size={30} /> : <ToggleLeft size={30} />}
                          </div>
                          {isExp ? <ChevronUp size={14} style={{ color: "#64748b" }} /> : <ChevronDown size={14} style={{ color: "#64748b" }} />}
                        </div>
                      </button>

                      {/* Expanded Content */}
                      {isExp && (
                        <div className="px-5 pb-5 space-y-4 border-t" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
                          <div className="pt-4 space-y-4">

                            {/* Grid info boxes */}
                            {nextBuy && nextSell && (
                              <div className="grid grid-cols-3 gap-2">
                                <div className="p-2 rounded-xl text-center" style={{ background: "rgba(0,212,170,0.07)", border: "1px solid rgba(0,212,170,0.15)" }}>
                                  <p className="text-[10px]" style={{ color: "#64748b" }}>Next Beli</p>
                                  <p className="text-xs font-bold" style={{ color: "#00d4aa" }}>RM {Math.round(nextBuy).toLocaleString()}</p>
                                </div>
                                <div className="p-2 rounded-xl text-center" style={{ background: "rgba(255,255,255,0.04)" }}>
                                  <p className="text-[10px]" style={{ color: "#64748b" }}>Base</p>
                                  <p className="text-xs font-bold" style={{ color: "#f1f5f9" }}>RM {Math.round(gs.base_price_myr).toLocaleString()}</p>
                                </div>
                                <div className="p-2 rounded-xl text-center" style={{ background: "rgba(255,71,87,0.07)", border: "1px solid rgba(255,71,87,0.15)" }}>
                                  <p className="text-[10px]" style={{ color: "#64748b" }}>Next Jual</p>
                                  <p className="text-xs font-bold" style={{ color: "#ff4757" }}>RM {Math.round(nextSell).toLocaleString()}</p>
                                </div>
                              </div>
                            )}

                            <NumberInput
                              label="Saiz Trade per Transaksi (RM)"
                              value={gs.trade_size_myr}
                              min={30} step={5}
                              onChange={(v: number) => updateGrid(gs.pair, "trade_size_myr", v)}
                              hint="Minimum RM30 (syarat Luno)" />

                            <SliderRow
                              label="Margin Naik/Turun untuk Trigger"
                              value={gs.rebalance_margin_pct}
                              min={0.5} max={10} step={0.5}
                              unit="%"
                              onChange={(v: number) => updateGrid(gs.pair, "rebalance_margin_pct", v)}
                              hint={`Beli bila turun ${gs.rebalance_margin_pct}% · Jual bila naik ${gs.rebalance_margin_pct}%`} />

                            <NumberInput
                              label="Harga Rujukan (Base Price) — 0 = Auto"
                              value={gs.base_price_myr}
                              min={0} step={100}
                              onChange={(v: number) => updateGrid(gs.pair, "base_price_myr", v)}
                              unit="RM"
                              hint="Set '0' supaya bot auto-lock ke harga semasa trade terakhir" />

                            <button onClick={() => saveGrid(gs)} disabled={saving}
                              className="w-full py-2.5 rounded-xl text-sm font-semibold flex items-center justify-center gap-2 transition-all"
                              style={{
                                background: saved === gs.pair ? `${meta.color}20` : `linear-gradient(135deg, ${meta.color}cc, ${meta.color}88)`,
                                color: saved === gs.pair ? meta.color : "white",
                                border: saved === gs.pair ? `1px solid ${meta.color}40` : "none"
                              }}>
                              {saved === gs.pair ? <><CheckCircle2 size={15} /> Disimpan!</> : <><Save size={15} /> Simpan {meta.ticker}</>}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* ── Info ──────────────────────────────────────────────── */}
            <div className="p-4 rounded-xl space-y-2" style={{ background: "rgba(0,212,170,0.04)", border: "1px solid rgba(0,212,170,0.1)" }}>
              <p className="text-xs font-semibold" style={{ color: "#00d4aa" }}>💡 Cara Grid Trading Berfungsi</p>
              <p className="text-xs leading-relaxed" style={{ color: "#64748b" }}>
                Bot check harga setiap <strong style={{ color: "#94a3b8" }}>3 minit</strong>.
                Kalau harga jatuh lebih dari <strong style={{ color: "#94a3b8" }}>Margin %</strong> dari Base Price → <strong style={{ color: "#00d4aa" }}>BELI</strong>.
                Kalau naik lebih dari Margin % → <strong style={{ color: "#ff4757" }}>JUAL</strong>.
                Base Price auto-update pada harga trade terbaru.
              </p>
            </div>

          </>
        )}
      </main>
    </div>
  );
}
