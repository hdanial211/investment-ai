import { useState, useEffect } from 'react'
import axios from 'axios'
import { Activity, Power, ShieldAlert, Zap, Layers, BarChart2, Radio, Wallet, TrendingUp, AlertTriangle } from 'lucide-react'
import './App.css'
import BacktestSimulator from './BacktestSimulator'

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

  // Resolve current coin details safely
  const coinData = state.coins[selectedCoin] || {
    current_price: 0.0,
    last_signal: 0.0,
    confidence: 0.0,
    layers: [],
    total_pnl: 0.0,
    trade_amount_myr: 250.0,
    risk_level: 1,
    tp_pct: 0.005
  }

  const tradeAmount = coinData.trade_amount_myr || 250.0;
  const tpPct = coinData.tp_pct || 0.005;
  const maxLayers = coinData.risk_level === 3 ? "2-3 Lapis" : coinData.risk_level === 2 ? "5 Lapis" : "6 Lapis";
  
  const getStrategyName = (coin, level) => {
    if (level === 3) {
      if (coin === 'ETH' || coin === 'SOL') return "The Whale Imitator (Gap 5%)";
      return "Heavy Scalping (Gap 1%)";
    }
    if (level === 2) return "Scalp & Run + Trailing (Gap 0.5%)";
    return "DCA Asas / Deep Value (Gap 2%-5%)";
  };

  // Calculate overall PnL across all coins
  const totalPnL = Object.values(state.coins).reduce((sum, c) => sum + (c.total_pnl || 0), 0)

  // Calculate consolidated sell info for current coin
  const holdingLayers = (coinData.layers || []).filter(l => l.status === 'HOLDING')
  const consolidatedSellId = coinData.consolidated_sell_order_id
  let consolidatedInfo = null
  if (holdingLayers.length > 0) {
    const totalCost = holdingLayers.reduce((sum, l) => sum + (l.actual_cost_myr || l.amount_myr || 0), 0)
    const totalQty = holdingLayers.reduce((sum, l) => sum + (l.net_qty || l.quantity || 0), 0)
    const avgEntry = totalQty > 0 ? totalCost / totalQty : 0
    const sellPrice = holdingLayers[0]?.consolidated_sell_price || (avgEntry * (1 + tpPct + 0.004))
    consolidatedInfo = { totalCost, totalQty, avgEntry, sellPrice }
  }

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
                    {c.layers && c.layers.length > 0 && (
                      <span className="layers-count">{c.layers.length} L</span>
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
                <h2><Layers size={20} /> Posisi Layering (DCA) Aktif: {selectedCoin}</h2>
                <div style={{ marginTop: '1.5rem' }}>
                  {!coinData.layers || coinData.layers.length === 0 ? (
                    <div className="empty-state">
                      <AlertTriangle className="empty-state-icon" size={36} />
                      <p>Tiada posisi terbuka pada masa ini untuk {selectedCoin}.</p>
                    </div>
                  ) : (
                    <div className="table-wrapper">
                      <table className="layer-table">
                        <thead>
                          <tr>
                            <th>Layer</th>
                            <th>Harga Entry (RM)</th>
                            <th>Saiz (RM)</th>
                            <th>Qty (Hata)</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {coinData.layers.map(l => {
                            const entryPriceMYR = l.entry_price || 0
                            const netQty = l.net_qty || l.quantity || 0
                            const actualCost = l.actual_cost_myr || l.amount_myr || 0
                            return (
                              <tr key={l.id}>
                                <td>#{l.id}</td>
                                <td>RM {entryPriceMYR > 0 ? entryPriceMYR.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}</td>
                                <td>RM {actualCost ? actualCost.toFixed(2) : '0.00'}</td>
                                <td>{netQty > 0 ? netQty.toFixed(6) : '-'}</td>
                                <td><span className={`status-badge ${l.status === 'HOLDING' ? 'holding' : l.status === 'PENDING_BUY' ? 'pending' : 'open'}`}>{l.status || 'TERBUKA'}</span></td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>

                      {/* Consolidated Sell Summary */}
                      {consolidatedInfo && (
                        <div style={{ 
                          marginTop: '1rem', 
                          background: 'rgba(0, 229, 255, 0.08)', 
                          border: '1px solid rgba(0, 229, 255, 0.3)', 
                          borderRadius: '8px', 
                          padding: '12px 16px' 
                        }}>
                          <h4 style={{ color: '#00e5ff', margin: '0 0 10px 0', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <TrendingUp size={16} /> Gabungan Sell Order
                            {consolidatedSellId && <span style={{ fontSize: '0.75rem', color: '#888', marginLeft: '8px' }}>#{consolidatedSellId}</span>}
                          </h4>
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.85rem' }}>
                            <div>
                              <span style={{ color: '#888' }}>Avg Entry: </span>
                              <span style={{ color: '#fff' }}>RM {consolidatedInfo.avgEntry.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}</span>
                            </div>
                            <div>
                              <span style={{ color: '#888' }}>Total Qty: </span>
                              <span style={{ color: '#fff' }}>{consolidatedInfo.totalQty.toFixed(6)}</span>
                            </div>
                            <div>
                              <span style={{ color: '#888' }}>Total Kos: </span>
                              <span style={{ color: '#fff' }}>RM {consolidatedInfo.totalCost.toFixed(2)}</span>
                            </div>
                            <div>
                              <span style={{ color: '#888' }}>Sell Price (TP {(tpPct * 100).toFixed(1)}%): </span>
                              <span style={{ color: '#00e676', fontWeight: 'bold' }}>RM {consolidatedInfo.sellPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })}</span>
                            </div>
                          </div>
                          <p style={{ margin: '8px 0 0 0', fontSize: '0.75rem', color: '#666' }}>
                            *Satu sell order gabungan untuk semua {holdingLayers.length} layer. Cancel & replace automatik bila layer baru masuk.
                          </p>
                        </div>
                      )}
                    </div>
                  )}
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
                    <h3>Untung Bersih (Semua) <span style={{ fontSize: '0.65rem', color: '#888' }}>via Hata</span></h3>
                    <p className={`value ${totalPnL >= 0 ? 'profit' : 'loss'}`}>
                      RM {totalPnL >= 0 ? '+' : ''}{totalPnL.toFixed(2)}
                    </p>
                  </div>
                </div>
                <div className="stats-row">
                  <div className="stat-box" style={{ gridColumn: 'span 2' }}>
                    <h3>Untung Bersih ({selectedCoin}) <span style={{ fontSize: '0.65rem', color: '#888' }}>via Hata</span></h3>
                    <p className={`value ${coinData.total_pnl >= 0 ? 'profit' : 'loss'}`} style={{ fontSize: '1.4rem' }}>
                      RM {coinData.total_pnl >= 0 ? '+' : ''}{coinData.total_pnl ? coinData.total_pnl.toFixed(2) : '0.00'}
                    </p>
                  </div>
                </div>
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

                  <label>Take Profit (%) — per coin</label>
                  <div className="amount-controls" style={{ marginBottom: '1rem' }}>
                    <input 
                      type="number" 
                      className="amount-input"
                      value={tpPct ? (tpPct * 100).toFixed(1) : ''} 
                      onChange={(e) => {
                        const val = parseFloat(e.target.value)
                        if (!isNaN(val)) setTP(val / 100)
                      }}
                      min="0.1"
                      max="50"
                      step="0.1"
                      placeholder="Cth: 0.5 = 0.5%"
                      style={{ width: '100%', fontSize: '1.2rem', padding: '10px' }}
                    />
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.75rem', color: '#888' }}>
                      *TP {(tpPct * 100).toFixed(1)}% + ~0.4% fee buffer = Sell pada +{((tpPct + 0.004) * 100).toFixed(1)}% dari avg entry
                    </p>
                  </div>

                  <label>Tahap Risiko (Pilihan Strategi Pasif)</label>
                  <div className="amount-controls" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
                    <button 
                      className={`amount-btn ${coinData.risk_level === 1 ? 'active' : ''}`} 
                      onClick={() => setRiskLevel(1)}
                      style={{ fontSize: '1rem', padding: '10px' }}
                    >
                      Tahap 1<br/><small>(Konservatif / 5%)</small>
                    </button>
                    <button 
                      className={`amount-btn ${coinData.risk_level === 2 ? 'active' : ''}`} 
                      onClick={() => setRiskLevel(2)}
                      style={{ fontSize: '1rem', padding: '10px' }}
                    >
                      Tahap 2<br/><small>(Seimbang / 10%)</small>
                    </button>
                    <button 
                      className={`amount-btn ${coinData.risk_level === 3 ? 'active' : ''}`} 
                      onClick={() => setRiskLevel(3)}
                      style={{ fontSize: '1rem', padding: '10px' }}
                    >
                      Tahap 3<br/><small>(Agresif / 25%)</small>
                    </button>
                  </div>
                  
                  <div style={{ marginTop: '1.5rem', background: '#111', padding: '15px', borderRadius: '8px', border: '1px solid #333' }}>
                    <h4 style={{ color: '#00e5ff', marginBottom: '10px' }}>Tetapan Individu Aktif ({selectedCoin})</h4>
                    <p style={{ margin: '5px 0', fontSize: '0.9rem' }}>
                      <strong style={{ color: '#aaa' }}>Strategi:</strong> {getStrategyName(selectedCoin, coinData.risk_level)}
                    </p>
                    <p style={{ margin: '5px 0', fontSize: '0.9rem' }}>
                      <strong style={{ color: '#aaa' }}>Kapasiti Maksimum:</strong> {maxLayers}
                    </p>
                    <p style={{ margin: '5px 0', fontSize: '0.9rem' }}>
                      <strong style={{ color: '#aaa' }}>Take Profit:</strong> <span style={{ color: '#00e676' }}>{(tpPct * 100).toFixed(1)}%</span> (+ ~0.4% sell fee)
                    </p>
                    <p style={{ margin: '15px 0 5px 0', fontSize: '0.95rem' }}>
                      <strong style={{ color: '#fff' }}>Saiz Trade Ditetapkan: <span style={{ color: '#00e5ff' }}>RM {tradeAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span></strong>
                    </p>
                    <p style={{ margin: '0', fontSize: '0.8rem', color: '#666' }}>
                      *Bot akan masuk posisi sebanyak RM {tradeAmount} pada setiap layer (maksimum {maxLayers}). Semua layer digabung dalam 1 sell order.
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
      ) : (
        <BacktestSimulator />
      )}
    </div>
  )
}

export default App
