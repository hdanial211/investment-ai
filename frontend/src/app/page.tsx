"use client";
import { useState, useEffect, useCallback } from "react";
import {
  TrendingUp, TrendingDown, Bitcoin, RefreshCw,
  Play, Pause, Zap, Activity, DollarSign,
  Clock, BarChart2, ArrowUpRight, ArrowDownRight, Settings
} from "lucide-react";
import Link from "next/link";

const API = "http://localhost:8000/api";

interface Portfolio {
  btc_balance: number;
  myr_balance: number;
  btc_price: number;
  total_value: number;
  total_pnl: number;
  pnl_pct: number;
  last_buy_price: number | null;
  last_buy_date: string | null;
  last_trade_type: string | null;
}

interface BotStatus {
  bot_enabled: boolean;
  next_run: string;
  schedule_time: string;
}

interface Signal {
  action: "BUY" | "SELL" | "HOLD";
  reason: string;
  confidence: number;
  current_price: number;
  price_change_pct: number;
  rsi: number | null;
  ema_20: number | null;
}

interface Trade {
  id: number;
  type: string;
  amount_myr: number;
  amount_btc: number;
  price_myr: number;
  pnl_myr: number;
  signal: string;
  created_at: string;
}

interface Stats {
  total_trades: number;
  total_buys: number;
  total_sells: number;
  total_invested_myr: number;
  total_pnl_myr: number;
  win_rate: number;
}

async function fetchJSON(url: string) {
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return null;
  }
}

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [signal, setSignal] = useState<Signal | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [countdown, setCountdown] = useState(30);

  const fetchAll = useCallback(async () => {
    const [portfolioData, statusData, signalData, tradesData, statsData, settingsData] =
      await Promise.all([
        fetchJSON(`${API}/portfolio`),
        fetchJSON(`${API}/status`),
        fetchJSON(`${API}/signal`),
        fetchJSON(`${API}/trades?limit=5`),
        fetchJSON(`${API}/trades/stats`),
        fetchJSON(`${API}/settings`),
      ]);
    if (portfolioData) setPortfolio(portfolioData);
    if (statusData) setStatus(statusData);
    if (signalData) setSignal(signalData);
    if (tradesData) setTrades(tradesData);
    if (statsData) setStats(statsData);
    if (settingsData) setSettings(settingsData);
    setLastUpdate(new Date());
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchAll();
    const REFRESH_SEC = 30;
    const interval = setInterval(() => {
      fetchAll();
      setCountdown(REFRESH_SEC);
    }, REFRESH_SEC * 1000);
    // Countdown ticker every second
    const ticker = setInterval(() => {
      setCountdown(prev => (prev <= 1 ? REFRESH_SEC : prev - 1));
    }, 1000);
    return () => { clearInterval(interval); clearInterval(ticker); };
  }, [fetchAll]);


  const toggleBot = async () => {
    setToggling(true);
    await fetch(`${API}/bot/toggle`, { method: "POST" });
    await fetchAll();
    setToggling(false);
  };

  const triggerNow = async () => {
    setTriggering(true);
    await fetch(`${API}/bot/trigger`, { method: "POST" });
    setTimeout(() => { fetchAll(); setTriggering(false); }, 3000);
  };

  const pnlPositive = (portfolio?.total_pnl ?? 0) >= 0;

  return (
    <div className="min-h-screen" style={{ background: "linear-gradient(135deg, #0a0e1a 0%, #0d1525 50%, #0a0e1a 100%)" }}>
      {/* Header */}
      <header className="border-b" style={{ borderColor: "#1e293b", background: "rgba(10,14,26,0.9)", backdropFilter: "blur(20px)" }}>
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "linear-gradient(135deg, #f7931a, #ff6b35)" }}>
              <Bitcoin size={20} color="white" />
            </div>
            <div>
              <h1 className="font-bold text-lg" style={{ color: "#f1f5f9" }}>Bitcoin Investment AI</h1>
              <p className="text-xs" style={{ color: "#64748b" }}>Auto-Invest via Luno Malaysia</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Auto-refresh countdown */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full" style={{ background: "rgba(0,212,170,0.1)", border: "1px solid rgba(0,212,170,0.2)" }}>
              <div className="w-2 h-2 rounded-full pulse-dot" style={{ background: "#00d4aa" }} />
              <span className="text-xs font-medium" style={{ color: "#00d4aa" }}>
                Auto-refresh: {countdown}s
              </span>
            </div>


            <Link href="/settings" className="p-2 rounded-lg transition-colors" style={{ background: "rgba(255,255,255,0.05)" }}>
              <Settings size={18} style={{ color: "#94a3b8" }} />
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">

        {/* Top Row — Status + Price */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">

          {/* Bot Status Card */}
          <div className="glass-card p-5 slide-up" style={{ animationDelay: "0ms" }}>
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-medium" style={{ color: "#94a3b8" }}>Status Bot</span>
              <Activity size={16} style={{ color: "#94a3b8" }} />
            </div>
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-3 h-3 rounded-full pulse-dot`}
                style={{ background: status?.bot_enabled ? "#00d4aa" : "#ff4757" }} />
              <span className="text-xl font-bold" style={{ color: status?.bot_enabled ? "#00d4aa" : "#ff4757" }}>
                {status?.bot_enabled ? "AKTIF" : "BERHENTI"}
              </span>
            </div>
            <div className="flex flex-col gap-2 mb-4">
              <div className="flex items-center justify-between p-2 rounded-lg" style={{ background: "rgba(0,212,170,0.05)", border: "1px solid rgba(0,212,170,0.2)" }}>
                <div className="flex items-center gap-2">
                  <Zap size={14} style={{ color: "#00d4aa" }} />
                  <span className="text-xs font-medium" style={{ color: "#f1f5f9" }}>Enjin: Grid Sniper</span>
                </div>
                <span className="text-[10px]" style={{ color: "#00d4aa" }}>Setiap 3 Min</span>
              </div>
              <div className="flex items-center justify-between p-2 rounded-lg" style={{ background: "rgba(59,130,246,0.05)", border: "1px solid rgba(59,130,246,0.2)" }}>
                <div className="flex items-center gap-2">
                  <Clock size={14} style={{ color: "#3b82f6" }} />
                  <span className="text-xs font-medium" style={{ color: "#f1f5f9" }}>Enjin: Daily Flipper</span>
                </div>
                <span className="text-[10px]" style={{ color: "#3b82f6" }}>08:00 Pagi</span>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={toggleBot}
                disabled={toggling}
                className="flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all"
                style={{
                  background: status?.bot_enabled ? "rgba(255,71,87,0.15)" : "rgba(0,212,170,0.15)",
                  color: status?.bot_enabled ? "#ff4757" : "#00d4aa",
                  border: `1px solid ${status?.bot_enabled ? "rgba(255,71,87,0.3)" : "rgba(0,212,170,0.3)"}`
                }}>
                {toggling ? "..." : status?.bot_enabled ? <><Pause size={14} className="inline mr-1" />Pause</> : <><Play size={14} className="inline mr-1" />Aktif</>}
              </button>
              <button
                onClick={triggerNow}
                disabled={triggering}
                className="flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all"
                style={{ background: "rgba(59,130,246,0.15)", color: "#3b82f6", border: "1px solid rgba(59,130,246,0.3)" }}>
                {triggering ? "Running..." : <><Zap size={14} className="inline mr-1" />Run Sekarang</>}
              </button>
            </div>
          </div>

          {/* BTC Price Card — 3 maklumat penting sahaja */}
          <div className="glass-card p-5 slide-up glow-green" style={{ animationDelay: "100ms" }}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium" style={{ color: "#94a3b8" }}>Harga BTC/MYR</span>
              <Bitcoin size={16} style={{ color: "#f7931a" }} />
            </div>

            {/* Harga Sekarang */}
            <div className="mb-4">
              <p className="text-3xl font-bold number-glow" style={{ color: "#f1f5f9" }}>
                RM {signal?.current_price ? signal.current_price.toLocaleString("ms-MY", { maximumFractionDigits: 0 }) : "---"}
              </p>
              <div className="flex items-center gap-2 mt-1">
                {(signal?.price_change_pct ?? 0) >= 0
                  ? <ArrowUpRight size={14} style={{ color: "#00d4aa" }} />
                  : <ArrowDownRight size={14} style={{ color: "#ff4757" }} />}
                <span className="text-xs" style={{ color: (signal?.price_change_pct ?? 0) >= 0 ? "#00d4aa" : "#ff4757" }}>
                  {signal?.price_change_pct !== undefined ? `${signal.price_change_pct >= 0 ? "+" : ""}${signal.price_change_pct.toFixed(2)}%` : "---"} dari semalam
                </span>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              {/* Last Beli/Jual */}
              {portfolio?.last_buy_price && (() => {
                const pct = signal?.current_price
                  ? (((signal.current_price - portfolio.last_buy_price) / portfolio.last_buy_price) * 100)
                  : null;
                const isUp = pct !== null && pct >= 0;
                const isSell = portfolio.last_trade_type === "SELL";
                const tradeColor = isSell ? "#ff4757" : "#00d4aa";
                const tradeLabel = isSell ? "🔴 Last Jual" : "🟢 Last Beli";
                return (
                  <div className="p-3 rounded-lg" style={{ background: isSell ? "rgba(255,71,87,0.07)" : "rgba(0,212,170,0.08)", border: `1px solid ${isSell ? "rgba(255,71,87,0.2)" : "rgba(0,212,170,0.2)"}` }}>
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-[10px] font-medium" style={{ color: tradeColor }}>{tradeLabel}</p>
                      <p className="text-[10px]" style={{ color: "#475569" }}>
                        {portfolio.last_buy_date ? new Date(portfolio.last_buy_date).toLocaleString("ms-MY", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }) : ""}
                      </p>
                    </div>
                    <div className="flex items-center justify-between">
                      <p className="text-base font-bold" style={{ color: "#f1f5f9" }}>
                        RM {portfolio.last_buy_price.toLocaleString("ms-MY", { maximumFractionDigits: 0 })}
                      </p>
                      {pct !== null && (
                        <span className="text-sm font-bold px-2 py-0.5 rounded-full" style={{
                          background: isUp ? "rgba(0,212,170,0.15)" : "rgba(255,71,87,0.15)",
                          color: isUp ? "#00d4aa" : "#ff4757",
                          border: `1px solid ${isUp ? "rgba(0,212,170,0.3)" : "rgba(255,71,87,0.3)"}`
                        }}>
                          {isUp ? "▲" : "▼"} {Math.abs(pct).toFixed(2)}%
                        </span>
                      )}
                    </div>
                  </div>
                );
              })()}

              {/* Next Beli / Next Jual */}
              {settings && settings.base_price_myr > 0 && (
                <div className="flex gap-2">
                  <div className="flex-1 p-3 rounded-lg text-center" style={{ background: "rgba(59,130,246,0.08)", border: "1px solid rgba(59,130,246,0.2)" }}>
                    <p className="text-[10px] font-medium mb-1" style={{ color: "#3b82f6" }}>⬇ Next Beli</p>
                    <p className="text-sm font-bold" style={{ color: "#f1f5f9" }}>
                      RM {(settings.base_price_myr * (1 - settings.rebalance_margin_pct / 100)).toLocaleString("ms-MY", { maximumFractionDigits: 0 })}
                    </p>
                  </div>
                  <div className="flex-1 p-3 rounded-lg text-center" style={{ background: "rgba(0,212,170,0.08)", border: "1px solid rgba(0,212,170,0.2)" }}>
                    <p className="text-[10px] font-medium mb-1" style={{ color: "#00d4aa" }}>⬆ Next Jual</p>
                    <p className="text-sm font-bold" style={{ color: "#f1f5f9" }}>
                      RM {(settings.base_price_myr * (1 + settings.rebalance_margin_pct / 100)).toLocaleString("ms-MY", { maximumFractionDigits: 0 })}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

        </div>

        {/* Portfolio Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {[
            {
              label: "Jumlah Portfolio",
              value: `RM ${portfolio?.total_value?.toFixed(2) ?? "0.00"}`,
              sub: "Nilai semasa",
              icon: <DollarSign size={16} />,
              color: "#3b82f6"
            },
            {
              label: "Profit / Loss",
              value: `RM ${portfolio?.total_pnl?.toFixed(2) ?? "0.00"}`,
              sub: `${portfolio?.pnl_pct?.toFixed(2) ?? "0.00"}%`,
              icon: pnlPositive ? <TrendingUp size={16} /> : <TrendingDown size={16} />,
              color: pnlPositive ? "#00d4aa" : "#ff4757",
              highlight: true
            },
            {
              label: "BTC Dimiliki",
              value: `${portfolio?.btc_balance?.toFixed(6) ?? "0.000000"} BTC`,
              sub: `≈ RM ${((portfolio?.btc_balance ?? 0) * (signal?.current_price ?? 0)).toFixed(2)}`,
              icon: <Bitcoin size={16} />,
              color: "#f7931a"
            },
            {
              label: "Baki Cash",
              value: `RM ${portfolio?.myr_balance?.toFixed(2) ?? "0.00"}`,
              sub: "Tersedia untuk invest",
              icon: <DollarSign size={16} />,
              color: "#94a3b8"
            },
          ].map((card, i) => (
            <div key={i} className="glass-card p-4 slide-up" style={{ animationDelay: `${300 + i * 80}ms` }}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs" style={{ color: "#64748b" }}>{card.label}</span>
                <span style={{ color: card.color }}>{card.icon}</span>
              </div>
              <p className="text-xl font-bold mb-1" style={{ color: card.highlight ? card.color : "#f1f5f9" }}>
                {card.value}
              </p>
              <p className="text-xs" style={{ color: "#64748b" }}>{card.sub}</p>
            </div>
          ))}
        </div>

        {/* Stats + Recent Trades */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">

          {/* Stats */}
          <div className="glass-card p-5">
            <h3 className="font-semibold mb-4" style={{ color: "#f1f5f9" }}>📊 Statistik Trading</h3>
            <div className="grid grid-cols-2 gap-4">
              {[
                { label: "Total Trade", value: stats?.total_trades ?? 0 },
                { label: "Beli", value: stats?.total_buys ?? 0, prefix: "🟢 ", color: "#00d4aa" },
                { label: "Jual", value: stats?.total_sells ?? 0, prefix: "🔴 ", color: "#ff4757" },
                { label: "Win Rate", value: `${stats?.win_rate?.toFixed(1) ?? "0.0"}%`, color: "#fbbf24" },
                { label: "Total Invest", value: `RM ${stats?.total_invested_myr?.toFixed(2) ?? "0.00"}` },
                { label: "Total P&L", value: `RM ${stats?.total_pnl_myr?.toFixed(2) ?? "0.00"}`, color: (stats?.total_pnl_myr ?? 0) >= 0 ? "#00d4aa" : "#ff4757" },
              ].map((s, i) => (
                <div key={i} className="p-3 rounded-xl" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <p className="text-xs mb-1" style={{ color: "#64748b" }}>{s.label}</p>
                  <p className="font-bold" style={{ color: s.color ?? "#f1f5f9" }}>{s.prefix ?? ""}{s.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Trades */}
          <div className="glass-card p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold" style={{ color: "#f1f5f9" }}>🕒 Trade Terkini</h3>
              <Link href="/trades" className="text-xs" style={{ color: "#3b82f6" }}>Lihat semua →</Link>
            </div>
            {trades.length === 0 ? (
              <div className="text-center py-8" style={{ color: "#64748b" }}>
                <Bitcoin size={32} className="mx-auto mb-2 opacity-30" />
                <p className="text-sm">Belum ada trade lagi</p>
              </div>
            ) : (
              <div className="space-y-3">
                {trades.map((t) => (
                  <div key={t.id} className="flex items-center justify-between p-3 rounded-xl"
                    style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg flex items-center justify-center"
                        style={{ background: t.type === "BUY" ? "rgba(0,212,170,0.15)" : "rgba(255,71,87,0.15)" }}>
                        {t.type === "BUY" ? <ArrowDownRight size={16} style={{ color: "#00d4aa" }} /> : <ArrowUpRight size={16} style={{ color: "#ff4757" }} />}
                      </div>
                      <div>
                        <p className="text-sm font-medium" style={{ color: t.type === "BUY" ? "#00d4aa" : "#ff4757" }}>
                          {t.type === "BUY" ? "BELI" : "JUAL"}
                        </p>
                        <p className="text-xs" style={{ color: "#64748b" }}>
                          {new Date(t.created_at).toLocaleDateString("ms-MY")}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium" style={{ color: "#f1f5f9" }}>
                        RM {t.amount_myr.toFixed(2)}
                      </p>
                      <p className="text-xs" style={{ color: "#64748b" }}>
                        {t.amount_btc.toFixed(6)} BTC
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Navigation Links */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link href="/trades" className="glass-card p-5 flex items-center gap-4 transition-all hover:scale-[1.02]"
            style={{ border: "1px solid rgba(59,130,246,0.2)" }}>
            <div className="w-12 h-12 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(59,130,246,0.15)" }}>
              <BarChart2 size={22} style={{ color: "#3b82f6" }} />
            </div>
            <div>
              <p className="font-semibold" style={{ color: "#f1f5f9" }}>History Trade</p>
              <p className="text-sm" style={{ color: "#64748b" }}>Lihat semua transaksi beli & jual</p>
            </div>
          </Link>
          <Link href="/settings" className="glass-card p-5 flex items-center gap-4 transition-all hover:scale-[1.02]"
            style={{ border: "1px solid rgba(251,191,36,0.2)" }}>
            <div className="w-12 h-12 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(251,191,36,0.15)" }}>
              <Settings size={22} style={{ color: "#fbbf24" }} />
            </div>
            <div>
              <p className="font-semibold" style={{ color: "#f1f5f9" }}>Tetapan Bot</p>
              <p className="text-sm" style={{ color: "#64748b" }}>Tukar jumlah, threshold, dan jadual</p>
            </div>
          </Link>
        </div>
      </main>
    </div>
  );
}
