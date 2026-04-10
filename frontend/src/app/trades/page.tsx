"use client";
import { useState, useEffect } from "react";
import { ArrowLeft, ArrowUpRight, ArrowDownRight, Download, Filter } from "lucide-react";
import Link from "next/link";

const API = "http://localhost:8000/api";

interface Trade {
  id: number;
  type: string;
  amount_myr: number;
  amount_btc: number;
  price_myr: number;
  pnl_myr: number;
  signal: string;
  status: string;
  order_id: string;
  created_at: string;
}

export default function TradesPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [filter, setFilter] = useState<"ALL" | "BUY" | "SELL">("ALL");
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      const [t, s] = await Promise.all([
        fetch(`${API}/trades?limit=100`).then(r => r.json()).catch(() => []),
        fetch(`${API}/trades/stats`).then(r => r.json()).catch(() => null),
      ]);
      setTrades(t);
      setStats(s);
      setLoading(false);
    };
    fetchData();
  }, []);

  const filtered = filter === "ALL" ? trades : trades.filter(t => t.type === filter);

  const exportCSV = () => {
    const headers = "ID,Jenis,RM,BTC,Harga,P&L,Tarikh\n";
    const rows = trades.map(t =>
      `${t.id},${t.type},${t.amount_myr},${t.amount_btc},${t.price_myr},${t.pnl_myr},${t.created_at}`
    ).join("\n");
    const blob = new Blob([headers + rows], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "bitcoin_trades.csv";
    a.click();
  };

  return (
    <div className="min-h-screen" style={{ background: "linear-gradient(135deg, #0a0e1a 0%, #0d1525 100%)" }}>
      <header className="border-b px-6 py-4 flex items-center justify-between" style={{ borderColor: "#1e293b", background: "rgba(10,14,26,0.9)" }}>
        <div className="flex items-center gap-3">
          <Link href="/" className="p-2 rounded-lg" style={{ background: "rgba(255,255,255,0.05)" }}>
            <ArrowLeft size={18} style={{ color: "#94a3b8" }} />
          </Link>
          <h1 className="font-bold text-lg" style={{ color: "#f1f5f9" }}>History Trade</h1>
        </div>
        <button onClick={exportCSV} className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm"
          style={{ background: "rgba(59,130,246,0.15)", color: "#3b82f6", border: "1px solid rgba(59,130,246,0.3)" }}>
          <Download size={14} /> Export CSV
        </button>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {/* Stats row */}
        {stats && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            {[
              { label: "Total Invest", value: `RM ${stats.total_invested_myr?.toFixed(2)}`, color: "#3b82f6" },
              { label: "Total P&L", value: `RM ${stats.total_pnl_myr?.toFixed(2)}`, color: stats.total_pnl_myr >= 0 ? "#00d4aa" : "#ff4757" },
              { label: "Win Rate", value: `${stats.win_rate?.toFixed(1)}%`, color: "#fbbf24" },
            ].map((s, i) => (
              <div key={i} className="glass-card p-4 text-center">
                <p className="text-xs mb-1" style={{ color: "#64748b" }}>{s.label}</p>
                <p className="text-xl font-bold" style={{ color: s.color }}>{s.value}</p>
              </div>
            ))}
          </div>
        )}

        {/* Filter */}
        <div className="flex items-center gap-3 mb-5">
          <Filter size={16} style={{ color: "#64748b" }} />
          {(["ALL", "BUY", "SELL"] as const).map(f => (
            <button key={f} onClick={() => setFilter(f)}
              className="px-4 py-1.5 rounded-full text-sm font-medium transition-all"
              style={{
                background: filter === f ? (f === "BUY" ? "rgba(0,212,170,0.2)" : f === "SELL" ? "rgba(255,71,87,0.2)" : "rgba(59,130,246,0.2)") : "rgba(255,255,255,0.05)",
                color: filter === f ? (f === "BUY" ? "#00d4aa" : f === "SELL" ? "#ff4757" : "#3b82f6") : "#64748b",
                border: filter === f ? `1px solid ${f === "BUY" ? "#00d4aa" : f === "SELL" ? "#ff4757" : "#3b82f6"}40` : "1px solid rgba(255,255,255,0.05)"
              }}>
              {f === "ALL" ? "Semua" : f === "BUY" ? "🟢 Beli" : "🔴 Jual"} ({f === "ALL" ? trades.length : trades.filter(t => t.type === f).length})
            </button>
          ))}
        </div>

        {/* Trade Table */}
        <div className="glass-card overflow-hidden">
          {loading ? (
            <div className="text-center py-16" style={{ color: "#64748b" }}>Memuat...</div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16" style={{ color: "#64748b" }}>Tiada trade lagi</div>
          ) : (
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: "1px solid #1e293b" }}>
                  {["Jenis", "Jumlah RM", "Jumlah BTC", "Harga BTC", "P&L", "Signal", "Tarikh"].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-medium" style={{ color: "#64748b" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((t, i) => (
                  <tr key={t.id} className="transition-colors"
                    style={{ borderBottom: "1px solid rgba(255,255,255,0.03)", background: i % 2 === 0 ? "transparent" : "rgba(255,255,255,0.01)" }}>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg flex items-center justify-center"
                          style={{ background: t.type === "BUY" ? "rgba(0,212,170,0.15)" : "rgba(255,71,87,0.15)" }}>
                          {t.type === "BUY" ? <ArrowDownRight size={13} style={{ color: "#00d4aa" }} /> : <ArrowUpRight size={13} style={{ color: "#ff4757" }} />}
                        </div>
                        <span className="text-sm font-medium" style={{ color: t.type === "BUY" ? "#00d4aa" : "#ff4757" }}>
                          {t.type === "BUY" ? "Beli" : "Jual"}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm" style={{ color: "#f1f5f9" }}>RM {t.amount_myr.toFixed(2)}</td>
                    <td className="px-4 py-3 text-sm font-mono" style={{ color: "#94a3b8" }}>{t.amount_btc.toFixed(8)}</td>
                    <td className="px-4 py-3 text-sm" style={{ color: "#94a3b8" }}>RM {t.price_myr.toLocaleString("ms-MY", { maximumFractionDigits: 0 })}</td>
                    <td className="px-4 py-3 text-sm font-medium" style={{ color: t.pnl_myr >= 0 ? "#00d4aa" : "#ff4757" }}>
                      {t.type === "SELL" ? `RM ${t.pnl_myr?.toFixed(2) ?? "0.00"}` : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-xs px-2 py-1 rounded-full" style={{ background: "rgba(255,255,255,0.05)", color: "#64748b", maxWidth: "150px", display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {t.signal || "—"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs" style={{ color: "#64748b" }}>
                      {new Date(t.created_at).toLocaleString("ms-MY")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  );
}
