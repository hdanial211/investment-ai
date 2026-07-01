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
    if (isNaN(val) || val < 0 || val > 10) return
    try {
      await axios.post('http://localhost:8000/api/set-max-layers', {
        coin: selectedCoin,
        max_layers: val
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
    layers: [],
    total_pnl: 0.0,
    trade_amount_myr: 250.0,
    risk_level: 1,
    tp_pct: 0.005
  }

  const tradeAmount = coinData.trade_amount_myr || 250.0;
  const tpPct = coinData.tp_pct || 0.005;
  const gridGapPct = coinData.grid_gap_pct || 0.01;
  const standbyBuyId = coinData.standby_buy_order_id || null;
  const standbyBuyPrice = coinData.standby_buy_price || 0;
  const systemMode = coinData.system_mode || 'grid';
  const maxLayersCustom = coinData.max_layers || 0;  // 0 = ikut risk_level
  const riskDefaultMax = coinData.risk_level === 3 ? 3 : coinData.risk_level === 2 ? 5 : 6;
  const effectiveMaxLayers = maxLayersCustom > 0 ? maxLayersCustom : riskDefaultMax;
  const maxLayers = `${effectiveMaxLayers} Lapis${maxLayersCustom > 0 ? ' (Custom)' : ' (Auto)'}`;
  
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
    const sellPrice = holdingLayers[0]?.consolidated_sell_price || (avgEntry * (1 + tpPct))
    consolidatedInfo = { totalCost, totalQty, avgEntry, sellPrice }
  }

  // Cascade & cycle info
  const pendingBuyLayers = (coinData.layers || []).filter(l => l.status === 'PENDING_BUY')
  const lastCycleEntry = coinData.last_cycle_entry || 0
  const minNewEntry = lastCycleEntry > 0 ? lastCycleEntry * 0.98 : 0
  const currentPrice = coinData.current_price || 0
  const canNewEntry = lastCycleEntry <= 0 || currentPrice <= minNewEntry

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
                            <th>#</th>
                            <th>Entry (RM)</th>
                            <th>Saiz (RM)</th>
                            <th>Qty</th>
                            <th>Fee</th>
                            <th>Sell Target</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {coinData.layers.map(l => {
                            const entryPriceMYR = l.entry_price || 0
                            const netQty = l.net_qty || l.quantity || 0
                            const actualCost = l.actual_cost_myr || l.amount_myr || 0
                            const feeMyr = l.fee_myr || 0
                            const feeRole = l.fee_role || ''
                            const isMaker = feeRole === 'maker'
                            const sellTarget = l.sell_target_price || 0
                            const hasSell = !!l.sell_order_id
                            return (
                              <tr key={l.id}>
                                <td>#{l.id}</td>
                                <td>RM {entryPriceMYR > 0 ? entryPriceMYR.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}</td>
                                <td>RM {actualCost ? actualCost.toFixed(2) : '0.00'}</td>
                                <td>{netQty > 0 ? netQty.toFixed(6) : '-'}</td>
                                <td>
                                  {l.status === 'HOLDING' ? (
                                    <span style={{ 
                                      fontSize: '0.7rem', 
                                      padding: '2px 6px', 
                                      borderRadius: '4px',
                                      background: isMaker ? 'rgba(0,230,118,0.15)' : 'rgba(255,179,0,0.15)',
                                      color: isMaker ? '#00e676' : '#ffb300',
                                      fontWeight: 'bold'
                                    }}>
                                      {isMaker ? 'Maker 0%' : feeMyr > 0 ? `Taker RM${feeMyr.toFixed(4)}` : '-'}
                                    </span>
                                  ) : '-'}
                                </td>
                                <td>
                                  {l.status === 'HOLDING' ? (
                                    <span style={{ fontSize: '0.75rem', color: hasSell ? '#00e676' : '#888', fontWeight: hasSell ? 'bold' : 'normal' }}>
                                      {hasSell ? `RM ${sellTarget.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2})}` : '⏳ placing...'}
                                    </span>
                                  ) : '-'}
                                </td>
                                <td><span className={`status-badge ${l.status === 'HOLDING' ? 'holding' : l.status === 'PENDING_BUY' ? 'pending' : 'open'}`}>{l.status || 'TERBUKA'}</span></td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>

                      {/* Grid Paired Orders Summary */}
                      {holdingLayers.length > 0 && (
                        <div style={{ 
                          marginTop: '1rem', 
                          background: 'rgba(0, 229, 255, 0.06)', 
                          border: '1px solid rgba(0, 229, 255, 0.25)', 
                          borderRadius: '8px', 
                          padding: '12px 16px' 
                        }}>
                          <h4 style={{ color: '#00e5ff', margin: '0 0 10px 0', fontSize: '0.95rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <TrendingUp size={16} /> Grid Paired Orders
                            <span style={{ fontSize: '0.72rem', background: 'rgba(0,230,118,0.15)', color: '#00e676', padding: '2px 8px', borderRadius: '12px', marginLeft: '6px' }}>MAKER 0% FEE</span>
                          </h4>
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.83rem' }}>
                            {holdingLayers.map(l => (
                              <div key={l.id} style={{ background: 'rgba(255,255,255,0.04)', borderRadius: '6px', padding: '8px 10px' }}>
                                <div style={{ color: '#888', fontSize: '0.72rem', marginBottom: '3px' }}>Layer #{l.id}</div>
                                <div style={{ color: '#fff' }}>Buy @ RM{(l.entry_price||0).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}</div>
                                <div style={{ color: l.sell_order_id ? '#00e676' : '#888', fontWeight: 'bold' }}>
                                  {l.sell_order_id 
                                    ? `✅ Sell @ RM${(l.sell_target_price||0).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}`
                                    : '⏳ Placing sell...'}
                                </div>
                              </div>
                            ))}
                          </div>
                          {standbyBuyId && (
                            <div style={{ marginTop: '10px', padding: '8px 10px', background: 'rgba(255,179,0,0.08)', border: '1px solid rgba(255,179,0,0.25)', borderRadius: '6px', fontSize: '0.82rem' }}>
                              <span style={{ color: '#ffb300', fontWeight: 'bold' }}>📡 Standby BUY: </span>
                              <span style={{ color: '#fff' }}>RM {standbyBuyPrice > 0 ? standbyBuyPrice.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2}) : '...'}</span>
                              <span style={{ color: '#888', fontSize: '0.72rem', marginLeft: '8px' }}>#{standbyBuyId}</span>
                            </div>
                          )}
                          <p style={{ margin: '8px 0 0 0', fontSize: '0.72rem', color: '#666' }}>
                            *Setiap layer ada sell sendiri. Standby BUY sentiasa aktif di bawah. Fee auto-dikira dari Hata API.
                          </p>
                          {pendingBuyLayers.length > 0 && (
                            <p style={{ margin: '6px 0 0 0', fontSize: '0.8rem', color: '#ffb300' }}>
                              ⏳ Cascade: {pendingBuyLayers.length} pending BUY menunggu (Layer {pendingBuyLayers[0]?.id} @ RM {pendingBuyLayers[0]?.entry_price?.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 4})})
                            </p>
                          )}
                        </div>
                      )}

                      {/* 2% Gap Status — shown when no layers active */}
                      {(!coinData.layers || coinData.layers.length === 0) && lastCycleEntry > 0 && (
                        <div style={{ 
                          marginTop: '1rem', 
                          background: canNewEntry ? 'rgba(0, 230, 118, 0.08)' : 'rgba(255, 179, 0, 0.08)', 
                          border: `1px solid ${canNewEntry ? 'rgba(0, 230, 118, 0.3)' : 'rgba(255, 179, 0, 0.3)'}`, 
                          borderRadius: '8px', 
                          padding: '10px 14px',
                          fontSize: '0.85rem'
                        }}>
                          <span style={{ color: canNewEntry ? '#00e676' : '#ffb300', fontWeight: 'bold' }}>
                            {canNewEntry ? '✅ Boleh entry baharu' : '🔒 Entry disekat — tunggu 2% gap'}
                          </span>
                          <p style={{ margin: '4px 0 0 0', color: '#888', fontSize: '0.75rem' }}>
                            Last cycle entry: RM {lastCycleEntry.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 4})} | 
                            Min entry: RM {minNewEntry.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 4})} | 
                            Harga sekarang: RM {currentPrice.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 4})}
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
                          {coinData.trade_history.oldest_trade || '?'} → {coinData.trade_history.newest_trade || '?'}
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


                  <label>Take Profit (%) — per coin</label>

                  <div className="amount-controls" style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
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
                        style={{ flex: 1, fontSize: '1.2rem', padding: '10px' }}
                      />
                      <button 
                        onClick={() => setTP({BTC: 0.004, ETH: 0.005, SOL: 0.008, XRP: 0.006, LTC: 0.004}[selectedCoin] || 0.005)}
                        style={{ 
                          padding: '10px 14px', 
                          background: 'rgba(0, 229, 255, 0.12)', 
                          border: '1px solid rgba(0, 229, 255, 0.3)', 
                          borderRadius: '8px', 
                          color: '#00e5ff', 
                          cursor: 'pointer',
                          fontSize: '0.85rem',
                          fontWeight: 'bold',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        Guna AI: {({BTC: '0.4', ETH: '0.5', SOL: '0.8', XRP: '0.6', LTC: '0.4'}[selectedCoin] || '0.5')}%
                      </button>
                    </div>
                    <div style={{ 
                      marginTop: '8px', 
                      background: 'rgba(0, 229, 255, 0.06)', 
                      border: '1px solid rgba(0, 229, 255, 0.15)', 
                      borderRadius: '6px', 
                      padding: '8px 12px',
                      fontSize: '0.78rem',
                      color: '#aaa'
                    }}>
                      <span style={{ color: '#00e5ff', fontWeight: 'bold' }}>💡 AI Suggestion ({selectedCoin}):</span>{' '}
                      {{
                        BTC: '0.4% — Large cap, volatility rendah, scalp cepat',
                        ETH: '0.5% — Medium volatility, sweet spot DCA layering',
                        SOL: '0.8% — High volatility, swing besar',
                        XRP: '0.6% — Medium-high volatility, spread agak besar',
                        LTC: '0.4% — Low volatility macam BTC, scalp cepat'
                      }[selectedCoin] || '0.5% — Default'}
                    </div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.75rem', color: '#888' }}>
                      *Fee auto-kira dari Hata API (Maker 0% / Taker 0.25%) — TP sell price auto-recover fee
                    </p>
                  </div>

                  {/* Grid Gap % Setting */}
                  <label>Grid Gap (%) — Jarak antara Buy/Sell per coin</label>
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
                    <div style={{ 
                      marginTop: '8px', 
                      background: 'rgba(0, 230, 118, 0.06)', 
                      border: '1px solid rgba(0, 230, 118, 0.15)', 
                      borderRadius: '6px', 
                      padding: '8px 12px',
                      fontSize: '0.78rem',
                      color: '#aaa'
                    }}>
                      <span style={{ color: '#00e676', fontWeight: 'bold' }}>💡 Grid Gap Sekarang ({selectedCoin}): {(gridGapPct * 100).toFixed(2)}%</span><br/>
                      Entry @ RM{(coinData.current_price||0).toLocaleString()} → Sell @ RM{((coinData.current_price||0) * (1 + gridGapPct)).toLocaleString(undefined,{maximumFractionDigits:2})}, Standby Buy @ RM{((coinData.current_price||0) * (1 - gridGapPct)).toLocaleString(undefined,{maximumFractionDigits:2})}
                    </div>
                    <p style={{ margin: '4px 0 0 0', fontSize: '0.75rem', color: '#888' }}>
                      *Semua orders (sell + standby buy) = Limit order → MAKER fee 0%
                    </p>
                  </div>

                  {/* Max Layers Setting */}
                  <label>Bilangan Layer Maksimum — per coin</label>
                  <div className="amount-controls" style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <input 
                        type="number" 
                        className="amount-input"
                        value={maxLayersCustom || ''}
                        onChange={(e) => setMaxLayers(e.target.value)}
                        min="0"
                        max="10"
                        step="1"
                        placeholder={`0 = Auto (${riskDefaultMax} layers)`}
                        style={{ flex: 1, fontSize: '1.2rem', padding: '10px' }}
                      />
                      <span style={{ color: '#aaa', fontSize: '0.85rem', whiteSpace: 'nowrap' }}>max layers</span>
                    </div>
                    <div style={{ display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap' }}>
                      {[0,1,2,3,4,5,6].map(n => (
                        <button key={n}
                          onClick={() => setMaxLayers(n)}
                          style={{
                            padding: '6px 14px',
                            borderRadius: '8px',
                            border: `1px solid ${maxLayersCustom === n || (n === 0 && maxLayersCustom === 0) ? '#00e5ff' : '#333'}`,
                            background: maxLayersCustom === n || (n === 0 && maxLayersCustom === 0) ? 'rgba(0,229,255,0.15)' : 'rgba(255,255,255,0.04)',
                            color: maxLayersCustom === n || (n === 0 && maxLayersCustom === 0) ? '#00e5ff' : '#888',
                            cursor: 'pointer',
                            fontSize: '0.85rem',
                            fontWeight: 'bold'
                          }}
                        >
                          {n === 0 ? `Auto (${riskDefaultMax})` : `${n}x`}
                        </button>
                      ))}
                    </div>
                    <p style={{ margin: '6px 0 0 0', fontSize: '0.75rem', color: '#888' }}>
                      Sekarang: <span style={{ color: '#00e676', fontWeight: 'bold' }}>{effectiveMaxLayers} layers max</span>
                      {maxLayersCustom > 0 ? ' (Custom)' : ` (Auto dari Risk Level ${coinData.risk_level})`}
                      {' '}— Grid akan letak standby BUY sampai max ni
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
                      <strong style={{ color: '#aaa' }}>Max Layers:</strong> <span style={{ color: '#00e676' }}>{effectiveMaxLayers}</span> {maxLayersCustom > 0 ? '(Custom)' : `(Auto - Risk ${coinData.risk_level})`}
                    </p>
                    <p style={{ margin: '5px 0', fontSize: '0.9rem' }}>
                      <strong style={{ color: '#aaa' }}>Grid Gap:</strong> <span style={{ color: '#00e676' }}>{(gridGapPct * 100).toFixed(2)}%</span> per step (MAKER 0% fee)
                    </p>
                    <p style={{ margin: '15px 0 5px 0', fontSize: '0.95rem' }}>
                      <strong style={{ color: '#fff' }}>Saiz Trade: <span style={{ color: '#00e5ff' }}>RM {tradeAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span></strong>
                    </p>
                    <p style={{ margin: '0', fontSize: '0.8rem', color: '#666' }}>
                      *Bot layering sehingga {effectiveMaxLayers} layers. Setiap layer ada sell sendiri (Maker 0% fee). Standby BUY sentiasa aktif.
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
