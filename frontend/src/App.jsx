import { useState, useEffect } from 'react'
import axios from 'axios'
import { Activity, Power, ShieldAlert, Zap, Layers, BarChart2, Radio } from 'lucide-react'
import './App.css'
import BacktestSimulator from './BacktestSimulator'

function App() {
  const [activeTab, setActiveTab] = useState('live') // 'live' or 'simulator'
  const [state, setState] = useState({
    current_price: 0,
    last_signal: 0,
    confidence: 0,
    is_auto: false,
    layers: [],
    total_pnl: 0,
    balance_myr: 10000
  })

  useEffect(() => {
    const fetchState = async () => {
      try {
        const res = await axios.get('http://localhost:8000/api/state')
        setState(res.data)
      } catch (err) {
        console.error(err)
      }
    }
    const interval = setInterval(fetchState, 1000)
    return () => clearInterval(interval)
  }, [])

  const toggleAuto = async () => {
    await axios.post('http://localhost:8000/api/toggle-auto', { is_auto: !state.is_auto })
  }

  const manualBuy = async () => {
    await axios.post('http://localhost:8000/api/manual-buy')
  }

  const panicSell = async () => {
    await axios.post('http://localhost:8000/api/panic-sell')
  }

  const setAmount = async (amount) => {
    await axios.post('http://localhost:8000/api/set-amount', { amount: parseFloat(amount) })
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

        <div className="status-indicator">
          <div className={`led ${state.is_auto ? 'on' : 'off'}`}></div>
          <span>{state.is_auto ? 'AUTO TRADING ACTIVE' : 'MANUAL MODE'}</span>
        </div>
      </header>

      {activeTab === 'live' ? (
        <main className="grid-container">
        {/* Panel Harga & AI (Kiri Atas) */}
        <section className="panel price-ai-panel">
          <h2><Activity size={20} /> ETH/USDT</h2>
          <div className="price-display">
            <span className="currency">$</span>
            <span className="price">{state.current_price.toFixed(2)}</span>
          </div>
          
          <div className="ai-meter">
            <div className="meter-header">
              <span>AI Golden Entry Confidence</span>
              <span className="percent">{state.confidence.toFixed(1)}%</span>
            </div>
            <div className="progress-bar">
              <div 
                className={`progress-fill ${state.confidence > 60 ? 'golden' : ''}`} 
                style={{width: `${Math.min(state.confidence, 100)}%`}}
              ></div>
            </div>
          </div>
        </section>

        {/* Panel Modal (Kanan Atas) */}
        <section className="panel stats-panel">
          <div className="stat-box">
            <h3>Baki Tunai (MYR)</h3>
            <p className="value">RM {state.balance_myr.toFixed(2)}</p>
          </div>
          <div className="stat-box">
            <h3>Untung Bersih (MYR)</h3>
            <p className={`value ${state.total_pnl >= 0 ? 'profit' : 'loss'}`}>
              RM {state.total_pnl.toFixed(2)}
            </p>
          </div>
        </section>

        {/* Panel Kawalan (Kanan Bawah) */}
        <section className="panel control-panel">
          <h2>Kawalan Eksekusi Hata</h2>
          
          <div className="amount-setting">
            <label>Saiz Entry (RM)</label>
            <div className="amount-controls">
              <button className={state.trade_amount_myr === 50 ? 'active' : ''} onClick={() => setAmount(50)}>50</button>
              <button className={state.trade_amount_myr === 100 ? 'active' : ''} onClick={() => setAmount(100)}>100</button>
              <button className={state.trade_amount_myr === 500 ? 'active' : ''} onClick={() => setAmount(500)}>500</button>
              <input 
                type="number" 
                value={state.trade_amount_myr || ''} 
                onChange={(e) => setAmount(e.target.value)}
                min="10"
                step="10"
                placeholder="Custom"
              />
            </div>
          </div>

          <div className="button-group">
            <button className={`btn-auto ${state.is_auto ? 'active' : ''}`} onClick={toggleAuto}>
              <Power size={18} /> {state.is_auto ? 'HENTIKAN AUTO' : 'HIDUPKAN AUTO'}
            </button>
            <button className="btn-manual" onClick={manualBuy}>
              TEMBAK RM {state.trade_amount_myr} SEKARANG
            </button>
            <button className="btn-panic" onClick={panicSell}>
              <ShieldAlert size={18} /> PANIC SELL SEMUA!
            </button>
          </div>
        </section>

        {/* Panel Layering (Kiri Bawah) */}
        <section className="panel layer-panel">
          <h2><Layers size={20} /> Posisi Layering (DCA) Aktif</h2>
          {state.layers.length === 0 ? (
            <p className="empty-state">Tiada posisi terbuka pada masa ini.</p>
          ) : (
            <table className="layer-table">
              <thead>
                <tr>
                  <th>Layer</th>
                  <th>Harga Entry</th>
                  <th>Saiz (RM)</th>
                  <th>Take Profit (0.6%)</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {state.layers.map(l => (
                  <tr key={l.id}>
                    <td>#{l.id}</td>
                    <td>${l.entry_price.toFixed(2)}</td>
                    <td>RM {l.amount_myr.toFixed(2)}</td>
                    <td className="profit-target">${l.take_profit.toFixed(2)}</td>
                    <td><span className="status-badge open">TERBUKA</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </main>
      ) : (
        <BacktestSimulator />
      )}
    </div>
  )
}

export default App
