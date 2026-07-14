import { useState, useEffect } from 'react'
import axios from 'axios'
import { Activity, Power, ShieldAlert, Zap, Layers, BarChart2, Radio, Wallet, TrendingUp, AlertTriangle, Brain } from 'lucide-react'
import './App.css'
import BacktestSimulator from './BacktestSimulator'
import AILearning from './AILearning'

// ★ Minimum notional (MYR) per coin — selaras dengan Hata exchange (minimum RM10 untuk semua pairs)
const MIN_NOTIONAL = {
  BTC: 10.0,
  ETH: 10.0,
  SOL: 10.0,
  LTC: 10.0,
  XRP: 10.0,
}

function App() {
  const [activeTab, setActiveTab] = useState('live') // 'live' or 'simulator'
  const [selectedCoin, setSelectedCoin] = useState('ETH')
  const [state, setState] = useState({
    global: {
      balance_myr: 10000.0,
      is_auto: false,
      usdt_myr_rate: 4.70,
      frozen_myr: 0.0,
      guardian_status: {
        status: "safe",
        analysis: "Memulakan Enjin Penjaga AI...",
        recommendation: "Tiada tindakan diperlukan."
      },
      guardian_last_update: "Never"
    },
    coins: {
      ETH: { current_price: 0.0, last_signal: 0.0, confidence: 0.0, layers: [], total_pnl: 0.0, risk_level: 1, tp_pct: 0.005 },
      BTC: { current_price: 0.0, last_signal: 0.0, confidence: 0.0, layers: [], total_pnl: 0.0, risk_level: 1, tp_pct: 0.005 },
      SOL: { current_price: 0.0, last_signal: 0.0, confidence: 0.0, layers: [], total_pnl: 0.0, risk_level: 1, tp_pct: 0.005 },
      XRP: { current_price: 0.0, last_signal: 0.0, confidence: 0.0, layers: [], total_pnl: 0.0, risk_level: 1, tp_pct: 0.005 },
      LTC: { current_price: 0.0, last_signal: 0.0, confidence: 0.0, layers: [], total_pnl: 0.0, risk_level: 1, tp_pct: 0.005 }
    }
  })

  useEffect(() => {
    const fetchState = async () => {
      try {
        const res = await axios.get('http://localhost:8000/api/state')
        if (res.data && res.data.global && res.data.coins) {
          setState(res.data)
        }
      } catch (err) {
        console.error("Failed to fetch state from backend:", err)
      }
    }
    const interval = setInterval(fetchState, 1000)
    return () => clearInterval(interval)
  }, [])

  const toggleAuto = async () => {
    try {
      await axios.post('http://localhost:8000/api/toggle-auto', { 
        coin: selectedCoin,
        is_auto: !(coinData.is_auto || false)
      })
    } catch (err) {
      console.error(err)
    }
  }

  const manualBuy = async () => {
    try {
      await axios.post('http://localhost:8000/api/manual-buy', { coin: selectedCoin })
    } catch (err) {
      console.error(err)
    }
  }

  const panicSell = async () => {
    if (window.confirm(`Adakah anda pasti ingin menjual / mengosongkan semua posisi ${selectedCoin}?`)) {
      try {
        await axios.post('http://localhost:8000/api/panic-sell', { coin: selectedCoin })
      } catch (err) {
        console.error(err)
      }
    }
  }

  const setAmount = async (amount) => {
    try {
      await axios.post('http://localhost:8000/api/set-amount', {
        coin: selectedCoin,
        amount: parseFloat(amount)
      })
    } catch (err) {
      console.error(err)
    }
  }

  const setRiskLevel = async (level) => {
    try {
      await axios.post('http://localhost:8000/api/set-risk-level', {
        coin: selectedCoin,
        risk_level: parseInt(level)
      })
    } catch (err) {
      console.error(err)
    }
  }

  const setTP = async (tp_pct) => {
    if (isNaN(tp_pct) || tp_pct < 0.001 || tp_pct > 0.5) return
    try {
      await axios.post('http://localhost:8000/api/set-tp', {
        coin: selectedCoin,
        tp_pct: tp_pct
      })
    } catch (err) {
      console.error(err)
    }
  }

  const setGridGap = async (gap_pct) => {
    if (isNaN(gap_pct) || gap_pct < 0.001 || gap_pct > 0.10) return
    try {
      await axios.post('http://localhost:8000/api/set-grid-gap', {
        coin: selectedCoin,
        grid_gap_pct: gap_pct
      })
    } catch (err) {
      console.error(err)
    }
  }

  const setMaxLayers = async (n) => {
    const val = parseInt(n)
    if (isNaN(val) || val < 0 || val > 99) return
    try {
      await axios.post('http://localhost:8000/api/set-max-layers', {
        coin: selectedCoin,
        max_layers: val
      })
    } catch (err) {
      console.error(err)
    }
  }

  const setMaxGroups = async (n) => {
    const val = parseInt(n)
    if (isNaN(val) || val < 1 || val > 99) return
    try {
      await axios.post('http://localhost:8000/api/set-max-groups', {
        coin: selectedCoin,
        max_groups: val
      })
    } catch (err) {
      console.error(err)
    }
  }

  const setNewGroupGap = async (gap_pct) => {
    if (isNaN(gap_pct) || gap_pct < 0.001 || gap_pct > 0.10) return
    try {
      await axios.post('http://localhost:8000/api/set-new-group-gap', {
        coin: selectedCoin,
        gap_pct: gap_pct
      })
    } catch (err) {
      console.error(err)
    }
  }

  const [syncing, setSyncing] = useState(false)
  const syncHistory = async () => {
    setSyncing(true)
    try {
      await axios.post('http://localhost:8000/api/sync-history')
    } catch (err) {
      console.error(err)
    }
    setSyncing(false)
  }

  // Resolve current coin details safely
  const coinData = state.coins[selectedCoin] || {
    current_price: 0.0,
    last_signal: 0.0,
    confidence: 0.0,
    groups: [],
    total_pnl: 0.0,
    trade_amount_myr: 250.0,
    max_groups: 3,
    new_group_gap_pct: 0.02,
    max_layers: 5,
    grid_gap_pct: 0.01,
  }

  const tradeAmount = coinData.trade_amount_myr || 250.0;
  const gridGapPct = coinData.grid_gap_pct || 0.01;
  const maxGroups = coinData.max_groups || 3;
  const newGroupGapPct = coinData.new_group_gap_pct || 0.02;
  const maxLayers = coinData.max_layers || 5;

  // P&L dari Hata API sync (sell - buy - fees) — simple & tepat
  const totalPnL = Object.values(state.coins).reduce((sum, c) => sum + (c.total_pnl || 0), 0)

  const activeGroups = coinData.groups || [];
  const lastCycleEntry = coinData.last_cycle_entry || 0
  
  let minNewEntry = 0;
  if (activeGroups.length > 0) {
    const allEntries = activeGroups.flatMap(g => g.layers || []).map(l => l.entry_price || 0);
    if (allEntries.length > 0) {
      minNewEntry = Math.min(...allEntries) * (1 - newGroupGapPct);
    }
  } else if (lastCycleEntry > 0) {
    minNewEntry = lastCycleEntry * (1 - newGroupGapPct);
  }

  const currentPrice = coinData.current_price || 0
  const canNewEntry = activeGroups.length < maxGroups && (minNewEntry === 0 || currentPrice <= minNewEntry)



  return (
    <div className="dashboard">
      <header className="header">
        <div className="logo-section">
          <Zap className="neon-icon" size={32} />
          <h1>INVESTMENT AI <span className="badge">LIVE</span></h1>
        </div>
        
        <div className="tab-navigation">
          <button 
            className={`tab-btn ${activeTab === 'live' ? 'active' : ''}`}
            onClick={() => setActiveTab('live')}
          >
            <Radio size={16} /> LIVE TRADE
          </button>
          <button 
            className={`tab-btn ${activeTab === 'ai-learning' ? 'active' : ''}`}
            onClick={() => setActiveTab('ai-learning')}
          >
            <Brain size={16} /> AI LEARNING
          </button>
          <button 
            className={`tab-btn ${activeTab === 'simulator' ? 'active' : ''}`}
            onClick={() => setActiveTab('simulator')}
          >
            <BarChart2 size={16} /> SIMULATOR
          </button>
        </div>

        <div className={`status-indicator ${coinData.is_auto ? 'auto' : 'manual'}`}>
          <div className={`led ${coinData.is_auto ? 'on' : 'off'}`}></div>
          <span>{coinData.is_auto ? `AUTO TRADING (${selectedCoin})` : `MANUAL MODE (${selectedCoin})`}</span>
        </div>
      </header>

      {activeTab === 'live' ? (
        <>
          {/* Coin Selector horizontal bar */}
          <div className="coin-selector-bar">
            {Object.keys(state.coins).map((coin) => {
              const c = state.coins[coin]
              const isActive = selectedCoin === coin
              const hasSignal = c.last_signal === 1
              const myrPrice = c.current_price || 0
              return (
                <div 
                  key={coin} 
                  className={`coin-card ${isActive ? 'active' : ''}`}
                  onClick={() => setSelectedCoin(coin)}
                >
                  <div className="coin-card-header">
                    <span className="coin-name">{coin}/MYR</span>
                    {hasSignal && <span className="coin-badge signal-buy">BUY</span>}
                  </div>
                  <div className="coin-price">
                    RM {myrPrice > 0 ? myrPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}
                  </div>
                  <div className="coin-card-footer">
                    <div className="coin-confidence">
                      <div className={`confidence-dot ${c.confidence > 60 ? 'golden' : ''}`}></div>
                      <span>{c.confidence ? c.confidence.toFixed(1) : '0.0'}%</span>
                    </div>
                    {c.groups && c.groups.length > 0 && (
                      <span className="layers-count">{c.groups.length} G</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          <div className="grid-container">
            {/* Left Side: Price Detail & Active Layers */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <section className="panel">
                <div className="panel-header-row">
                  <h2><Activity size={20} /> Paparan Pasaran: {selectedCoin}/MYR</h2>
                </div>
                
                <div className="detail-price-ai">
                  <div className="detail-price-row">
                    <span className="currency">RM</span>
                    <span className="price">
                      {coinData.current_price > 0 ? coinData.current_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}
                    </span>
                  </div>
                  
                  <div className="ai-meter">
                    <div className="meter-header">
                      <span>AI Golden Entry Confidence ({selectedCoin})</span>
                      <span className={`percent ${coinData.confidence > 60 ? 'golden' : ''}`}>
                        {coinData.confidence ? coinData.confidence.toFixed(1) : '0.0'}%
                      </span>
                    </div>
                    <div className="progress-bar">
                      <div 
                        className={`progress-fill ${coinData.confidence > 60 ? 'golden' : ''}`} 
                        style={{width: `${Math.min(coinData.confidence || 0, 100)}%`}}
                      ></div>
                    </div>
                  </div>
                </div>
              </section>

              <section className="panel layer-panel" style={{ flexGrow: 1 }}>
                <h2><Layers size={20} /> Multi-Group Grid: {selectedCoin}</h2>
                <div style={{ marginTop: '1.5rem' }}>
                  {activeGroups.length === 0 ? (
                    <div className="empty-state">
                      <AlertTriangle className="empty-state-icon" size={36} />
                      <p>Tiada posisi terbuka pada masa ini untuk {selectedCoin}. Menunggu setup ML...</p>
                    </div>
                  ) : (
                    <div className="groups-wrapper" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      {activeGroups.map(group => {
                        const layers = group.layers || [];
                        const standbyId = group.standby_buy_order_id;
                        const standbyPrice = group.standby_buy_price || 0;
                        
                        return (
                          <div key={group.id} className="group-card" style={{ 
                            background: 'rgba(0, 229, 255, 0.05)', 
                            border: '1px solid rgba(0, 229, 255, 0.2)', 
                            borderRadius: '10px', 
                            padding: '16px' 
                          }}>
                            <div className="group-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                              <h3 style={{ margin: 0, color: '#00e5ff', fontSize: '1.1rem' }}>Group #{group.id}</h3>
                              <span style={{ fontSize: '0.8rem', background: 'rgba(0,230,118,0.15)', color: '#00e676', padding: '4px 10px', borderRadius: '12px' }}>
                                {layers.length} Layers
                              </span>
                            </div>
                            
                            <table className="layer-table" style={{ marginBottom: '12px' }}>
                              <thead>
                                <tr>
                                  <th>Layer</th>
                                  <th>Entry (RM)</th>
                                  <th>Net Qty</th>
                                  <th>Fees (RM)</th>
                                  <th>Sell Target (RM)</th>
                                  <th>Status</th>
                                </tr>
                              </thead>
                              <tbody>
                                {layers.map(l => (
                                  <tr key={l.id}>
                                    <td>#{l.id}</td>
                                    <td>{(l.entry_price||0).toFixed(2)}</td>
                                    <td>{(l.net_qty||l.quantity||0).toFixed(6)}</td>
                                    <td>
                                      {l.fee_myr !== undefined ? (
                                        <span style={{ color: '#ffb300', fontSize: '0.85rem' }}>
                                          {(l.fee_myr||0).toFixed(4)} <br/>
                                          <span style={{ fontSize: '0.7rem', color: '#888' }}>({l.fee_role||'maker'})</span>
                                        </span>
                                      ) : '-'}
                                    </td>
                                    <td>
                                      {l.status === 'HOLDING' ? (
                                        <span style={{ color: l.sell_order_id ? '#00e676' : '#888', fontWeight: l.sell_order_id ? 'bold' : 'normal' }}>
                                          {l.sell_order_id ? (l.sell_target_price||0).toFixed(2) : 'placing...'}
                                        </span>
                                      ) : '-'}
                                    </td>
                                    <td><span className={`status-badge ${l.status === 'HOLDING' ? 'holding' : 'pending'}`}>{l.status}</span></td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                            
                            {standbyId && (
                              <div style={{ padding: '10px 12px', background: 'rgba(255,179,0,0.08)', border: '1px solid rgba(255,179,0,0.2)', borderRadius: '6px', fontSize: '0.85rem' }}>
                                <span style={{ color: '#ffb300', fontWeight: 'bold' }}>📡 Standby BUY Layer {layers.length + 1}: </span>
                                <span style={{ color: '#fff' }}>RM {(standbyPrice||0).toFixed(2)}</span>
                                <span style={{ color: '#888', fontSize: '0.75rem', marginLeft: '10px' }}>ID: {standbyId}</span>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}

                  {/* New Group Entry Status */}
                  <div style={{ 
                    marginTop: '1.5rem', 
                    background: canNewEntry ? 'rgba(0, 230, 118, 0.08)' : 'rgba(255, 179, 0, 0.08)', 
                    border: `1px solid ${canNewEntry ? 'rgba(0, 230, 118, 0.3)' : 'rgba(255, 179, 0, 0.3)'}`, 
                    borderRadius: '8px', 
                    padding: '12px 16px',
                    fontSize: '0.85rem'
                  }}>
                    <span style={{ color: canNewEntry ? '#00e676' : '#ffb300', fontWeight: 'bold' }}>
                      {canNewEntry ? '✅ Boleh buka Group Baharu (Jika ada ML Signal)' : '🔒 Buka Group Baharu disekat'}
                    </span>
                    <p style={{ margin: '6px 0 0 0', color: '#888', fontSize: '0.8rem', lineHeight: '1.5' }}>
                      Harga sekarang: RM {currentPrice.toFixed(4)}<br/>
                      Syarat Mula Group Baharu: Mesti kurang dari RM {minNewEntry.toFixed(4)} (Gap {newGroupGapPct*100}% bawah dari entry terendah) <br/>
                      Max Groups Dibuka: {activeGroups.length} / {maxGroups}
                    </p>
                  </div>
                </div>
              </section>
            </div>

            {/* Right Side: Account Balance & Action Controls */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <section className="panel">
                <h2><Wallet size={20} /> Status Akaun & PnL</h2>
                <div style={{ marginTop: '1.5rem' }} className="stats-row">
                  <div className="stat-box">
                    <h3>Baki Hata Wallet</h3>
                    <p className="value">RM {state.global.balance_myr ? state.global.balance_myr.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}</p>
                    {state.global.frozen_myr > 0 && (
                      <span className="frozen-label" style={{ fontSize: '0.85rem', color: '#ffb300', display: 'block', marginTop: '4px' }}>
                        (Terkunci: RM {state.global.frozen_myr.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })})
                      </span>
                    )}
                  </div>
                  <div className="stat-box">
                    <h3>P&L (Semua) <span style={{ fontSize: '0.65rem', color: '#888' }}>sell - buy - fees</span></h3>
                    <p className={`value ${totalPnL >= 0 ? 'profit' : 'loss'}`}>
                      RM {totalPnL >= 0 ? '+' : ''}{totalPnL.toFixed(2)}
                    </p>
                  </div>
                </div>
                <div className="stats-row">
                  <div className="stat-box" style={{ gridColumn: 'span 2' }}>
                    <h3>P&L ({selectedCoin}) <span style={{ fontSize: '0.65rem', color: '#888' }}>dari Hata API (2 July →)</span></h3>
                    <p className={`value ${(coinData.total_pnl || 0) >= 0 ? 'profit' : 'loss'}`} style={{ fontSize: '1.4rem' }}>
                      RM {(coinData.total_pnl || 0) >= 0 ? '+' : ''}{(coinData.total_pnl || 0).toFixed(2)}
                    </p>
                  </div>
                </div>

                {/* Trade History from Hata API */}
                {coinData.trade_history && (
                  <div style={{ 
                    marginTop: '1rem', 
                    background: 'rgba(0, 229, 255, 0.06)', 
                    border: '1px solid rgba(0, 229, 255, 0.15)', 
                    borderRadius: '8px', 
                    padding: '12px 16px' 
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <h4 style={{ color: '#00e5ff', margin: 0, fontSize: '0.9rem' }}>📊 Sejarah Trade ({selectedCoin}) — Hata API</h4>
                      <span style={{ fontSize: '0.7rem', color: '#666' }}>
                        Sync: {coinData.trade_history.last_sync || 'Never'}
                      </span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px', fontSize: '0.8rem' }}>
                      <div>
                        <span style={{ color: '#888' }}>Total Trades: </span>
                        <span style={{ color: '#fff', fontWeight: 'bold' }}>{coinData.trade_history.total_trades || 0}</span>
                      </div>
                      <div>
                        <span style={{ color: '#888' }}>Buys: </span>
                        <span style={{ color: '#ffb300' }}>{coinData.trade_history.buy_count || 0} (RM{(coinData.trade_history.total_buy_cost || 0).toFixed(2)})</span>
                      </div>
                      <div>
                        <span style={{ color: '#888' }}>Sells: </span>
                        <span style={{ color: '#00e676' }}>{coinData.trade_history.sell_count || 0} (RM{(coinData.trade_history.total_sell_revenue || 0).toFixed(2)})</span>
                      </div>
                      <div>
                        <span style={{ color: '#888' }}>Total Fees: </span>
                        <span style={{ color: (coinData.trade_history.total_fees || 0) > 0 ? '#ffb300' : '#00e676' }}>
                          RM{(coinData.trade_history.total_fees || 0).toFixed(4)}
                        </span>
                      </div>
                      <div style={{ gridColumn: 'span 2' }}>
                        <span style={{ color: '#888' }}>Range: </span>
                        <span style={{ color: '#aaa', fontSize: '0.7rem' }}>
                          {coinData.trade_history.oldest_trade ? new Date(coinData.trade_history.oldest_trade * 1000).toLocaleDateString() : '?'} → {coinData.trade_history.newest_trade ? new Date(coinData.trade_history.newest_trade * 1000).toLocaleDateString() : '?'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                <button 
                  onClick={syncHistory}
                  disabled={syncing}
                  style={{ 
                    marginTop: '1rem', 
                    width: '100%', 
                    padding: '10px', 
                    background: syncing ? 'rgba(255,255,255,0.05)' : 'rgba(0, 229, 255, 0.1)', 
                    border: '1px solid rgba(0, 229, 255, 0.3)', 
                    borderRadius: '8px', 
                    color: '#00e5ff', 
                    cursor: syncing ? 'wait' : 'pointer',
                    fontSize: '0.85rem',
                    fontWeight: 'bold'
                  }}
                >
                  {syncing ? '⏳ Syncing dari Hata API...' : '🔄 Sync Sejarah Trade (Hata API)'}
                </button>
              </section>

              <section className="panel guardian-panel" style={{ background: 'rgba(10, 25, 41, 0.7)', border: '1px solid #1e4976' }}>
                <div className="panel-header-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h2 style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                    ⚙️ Status Sistem Bot <span style={{ fontSize: '0.75rem', color: '#888' }}>(Autonomi)</span>
                  </h2>
                  <span style={{ fontSize: '0.8rem', color: '#888' }}>
                    Kemas kini: {state.global.guardian_last_update || "Never"}
                  </span>
                </div>
                
                <div style={{ marginTop: '1.2rem', display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div className={`status-dot ${state.global.guardian_status?.status || "safe"}`} style={{
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      background: state.global.guardian_status?.status === "safe" ? "#00e676" : state.global.guardian_status?.status === "warning" ? "#ffb300" : "#ff1744",
                      boxShadow: state.global.guardian_status?.status === "safe" ? "0 0 10px #00e676" : state.global.guardian_status?.status === "warning" ? "0 0 10px #ffb300" : "0 0 10px #ff1744"
                    }}></div>
                    <span style={{
                      fontWeight: 'bold',
                      fontSize: '1rem',
                      color: state.global.guardian_status?.status === "safe" ? "#00e676" : state.global.guardian_status?.status === "warning" ? "#ffb300" : "#ff1744"
                    }}>
                      {state.global.guardian_status?.status === "safe" ? "STATUS: SELAMAT" : state.global.guardian_status?.status === "warning" ? "STATUS: AMARAN" : "STATUS: TINDAKAN DIPERLUKAN"}
                    </span>
                  </div>

                  <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '6px', border: '1px solid #222' }}>
                    <h4 style={{ color: '#aaa', margin: '0 0 6px 0', fontSize: '0.85rem' }}>Analisis AI:</h4>
                    <p style={{ margin: 0, fontSize: '0.9rem', lineHeight: '1.4', color: '#eee' }}>
                      {state.global.guardian_status?.analysis || "Sedang menganalisis keadaan akaun dan pasaran..."}
                    </p>
                  </div>

                  <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '6px', border: '1px solid #222' }}>
                    <h4 style={{ color: '#aaa', margin: '0 0 6px 0', fontSize: '0.85rem' }}>Syor AI:</h4>
                    <p style={{ margin: 0, fontSize: '0.9rem', lineHeight: '1.4', color: '#eee' }}>
                      {state.global.guardian_status?.recommendation || "Tiada tindakan diperlukan."}
                    </p>
                  </div>
                </div>
              </section>

              <section className="panel control-panel">
                <h2>Kawalan Eksekusi Hata ({selectedCoin})</h2>
                
                <div className="amount-setting" style={{ marginBottom: '1.5rem' }}>
                  <label>Saiz Setiap Trade / Lapis (RM)</label>
                  <div className="amount-controls" style={{ marginBottom: '1rem' }}>
                    <input 
                      type="number" 
                      className="amount-input"
                      value={coinData.trade_amount_myr || ''} 
                      onChange={(e) => setAmount(e.target.value)}
                      min="10"
                      step="10"
                      placeholder="Masukkan Saiz per Lapis (Cth: 250)"
                      style={{ width: '100%', fontSize: '1.2rem', padding: '10px' }}
                    />
                  </div>

                  {/* ★ Min Notional Badge */}
                  {(() => {
                    const minVal = MIN_NOTIONAL[selectedCoin] ?? 10
                    const currentVal = parseFloat(coinData.trade_amount_myr) || 0
                    const isBelowMin = currentVal > 0 && currentVal < minVal
                    const isOk = currentVal >= minVal
                    return (
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '10px 14px',
                        borderRadius: '10px',
                        background: isBelowMin
                          ? 'rgba(255,59,59,0.12)'
                          : 'rgba(0,229,255,0.07)',
                        border: `1.5px solid ${isBelowMin ? '#ff3b3b' : isOk ? '#00e5ff' : '#444'}`,
                        marginBottom: '0.5rem',
                        fontSize: '0.85rem',
                        transition: 'all 0.3s',
                      }}>
                        <span style={{ fontSize: '1.1rem' }}>
                          {isBelowMin ? '⚠️' : isOk ? '✅' : 'ℹ️'}
                        </span>
                        <div style={{ flex: 1 }}>
                          <div style={{
                            fontWeight: 700,
                            color: isBelowMin ? '#ff6b6b' : '#00e5ff',
                            marginBottom: '2px',
                            fontSize: '0.82rem',
                            letterSpacing: '0.5px',
                            textTransform: 'uppercase'
                          }}>
                            Minimum Order {selectedCoin}/MYR
                          </div>
                          <div style={{ color: '#ccc', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                            {Object.entries(MIN_NOTIONAL).map(([coin, min]) => (
                              <span key={coin} style={{
                                padding: '2px 8px',
                                borderRadius: '20px',
                                fontSize: '0.78rem',
                                fontWeight: coin === selectedCoin ? 700 : 400,
                                background: coin === selectedCoin
                                  ? (isBelowMin ? 'rgba(255,59,59,0.3)' : 'rgba(0,229,255,0.2)')
                                  : 'rgba(255,255,255,0.06)',
                                color: coin === selectedCoin
                                  ? (isBelowMin ? '#ff8080' : '#00e5ff')
                                  : '#888',
                                border: coin === selectedCoin
                                  ? `1px solid ${isBelowMin ? '#ff3b3b' : '#00e5ff'}`
                                  : '1px solid #333',
                              }}>
                                {coin} ≥ RM{min.toFixed(0)}
                              </span>
                            ))}
                          </div>
                          {isBelowMin && (
                            <div style={{
                              color: '#ff6b6b',
                              fontWeight: 600,
                              marginTop: '5px',
                              fontSize: '0.8rem'
                            }}>
                              ❌ RM{currentVal.toFixed(2)} terlalu rendah! Naikkan ke sekurang-kurangnya RM{minVal.toFixed(0)} untuk {selectedCoin}.
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })()}


                  <label>Max Groups (Kumpulan Grid) — per coin</label>
                  <div className="amount-controls" style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <input 
                        type="number" 
                        className="amount-input"
                        value={maxGroups || ''} 
                        onChange={(e) => {
                          const val = parseInt(e.target.value)
                          if (!isNaN(val)) setMaxGroups(val)
                        }}
                        min="1"
                        max="99"
                        step="1"
                        placeholder="Cth: 3"
                        style={{ flex: 1, fontSize: '1.2rem', padding: '10px' }}
                      />
                      <span style={{ color: '#aaa', fontSize: '0.85rem', whiteSpace: 'nowrap' }}>groups</span>
                    </div>
                  </div>


                  {/* Grid Gap % Setting */}
                  <label>Grid Gap (%) — Jarak antara Buy/Sell per layer</label>
                  <div className="amount-controls" style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <input 
                        type="number" 
                        className="amount-input"
                        value={gridGapPct ? (gridGapPct * 100).toFixed(2) : ''} 
                        onChange={(e) => {
                          const val = parseFloat(e.target.value)
                          if (!isNaN(val)) setGridGap(val / 100)
                        }}
                        min="0.1"
                        max="10"
                        step="0.1"
                        placeholder="Cth: 1.0 = 1%"
                        style={{ flex: 1, fontSize: '1.2rem', padding: '10px' }}
                      />
                      <span style={{ color: '#00e676', fontWeight: 'bold', fontSize: '1rem', whiteSpace: 'nowrap' }}>%</span>
                    </div>
                  </div>

                  {/* Max Layers Setting */}
                  <label>Max Layers / Group</label>
                  <div className="amount-controls" style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <input 
                        type="number" 
                        className="amount-input"
                        value={maxLayers || ''}
                        onChange={(e) => setMaxLayers(e.target.value)}
                        min="1"
                        max="99"
                        step="1"
                        placeholder="Cth: 5"
                        style={{ flex: 1, fontSize: '1.2rem', padding: '10px' }}
                      />
                      <span style={{ color: '#aaa', fontSize: '0.85rem', whiteSpace: 'nowrap' }}>layers</span>
                    </div>
                  </div>


                  <label>Gap Untuk Group Baharu (%) — Jarak Harga Dari Entry Terendah</label>
                  <div className="amount-controls" style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <input 
                        type="number" 
                        className="amount-input"
                        value={newGroupGapPct ? (newGroupGapPct * 100).toFixed(2) : ''} 
                        onChange={(e) => {
                          const val = parseFloat(e.target.value)
                          if (!isNaN(val)) setNewGroupGap(val / 100)
                        }}
                        min="0.1"
                        max="10"
                        step="0.1"
                        placeholder="Cth: 2.0 = 2%"
                        style={{ flex: 1, fontSize: '1.2rem', padding: '10px' }}
                      />
                      <span style={{ color: '#00e676', fontWeight: 'bold', fontSize: '1rem', whiteSpace: 'nowrap' }}>%</span>
                    </div>
                  </div>

                  <div style={{ marginTop: '1.5rem', background: '#111', padding: '15px', borderRadius: '8px', border: '1px solid #333' }}>
                    <h4 style={{ color: '#00e5ff', marginBottom: '10px' }}>Tetapan Grid Semasa ({selectedCoin})</h4>
                    <p style={{ margin: '5px 0', fontSize: '0.9rem' }}>
                      <strong style={{ color: '#aaa' }}>Max Groups:</strong> <span style={{ color: '#00e676' }}>{maxGroups} Groups</span>
                    </p>
                    <p style={{ margin: '5px 0', fontSize: '0.9rem' }}>
                      <strong style={{ color: '#aaa' }}>Max Layers / Group:</strong> <span style={{ color: '#00e676' }}>{maxLayers} Layers</span>
                    </p>
                    <p style={{ margin: '5px 0', fontSize: '0.9rem' }}>
                      <strong style={{ color: '#aaa' }}>Gap Dalam Group:</strong> <span style={{ color: '#00e676' }}>{(gridGapPct * 100).toFixed(2)}%</span> (Layer Drop & Sell Target)
                    </p>
                    <p style={{ margin: '5px 0', fontSize: '0.9rem' }}>
                      <strong style={{ color: '#aaa' }}>Gap Group Baharu:</strong> <span style={{ color: '#00e676' }}>{(newGroupGapPct * 100).toFixed(2)}%</span> (Jarak mula Group Baru)
                    </p>
                    <p style={{ margin: '15px 0 5px 0', fontSize: '0.95rem' }}>
                      <strong style={{ color: '#fff' }}>Saiz Trade: <span style={{ color: '#00e5ff' }}>RM {tradeAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span> / Lapis</strong>
                    </p>
                    <p style={{ margin: '0', fontSize: '0.8rem', color: '#666' }}>
                      *Setiap layer diurus berasingan dan fee auto-dikira dari Hata API (Maker 0%).
                    </p>
                  </div>
                </div>

                <div className="button-group">
                  <button 
                    className={`btn-action btn-auto-toggle ${coinData.is_auto ? 'active' : ''}`} 
                    onClick={toggleAuto}
                  >
                    <Power size={18} /> {coinData.is_auto ? `HENTIKAN AUTO (${selectedCoin})` : `AKTIFKAN AUTO (${selectedCoin})`}
                  </button>
                  <button className="btn-action btn-manual-buy" onClick={manualBuy}>
                    TEMBAK RM {tradeAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ({selectedCoin}) SEKARANG
                  </button>
                  <button className="btn-action btn-panic-sell" onClick={panicSell}>
                    <ShieldAlert size={18} /> PANIC SELL SEMUA {selectedCoin}!
                  </button>
                </div>
              </section>
            </div>
          </div>
        </>
      ) : activeTab === 'ai-learning' ? (
        <AILearning />
      ) : (
        <BacktestSimulator />
      )}
    </div>
  )
}

export default App
