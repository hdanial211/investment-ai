import { useState, useRef, useEffect } from 'react'
import { Play, Activity } from 'lucide-react'
import './BacktestSimulator.css'

export default function BacktestSimulator() {
  const [params, setParams] = useState({
    initial_cash: 100000.0,
    trade_size_fiat: 4000.0,
    max_layers: 6,
    drop_threshold: 5.0, // UI shows positive %, api expects float
    take_profit_pct: 10.0,
    trailing_activation_pct: 3.0,
    trailing_gap_pct: 1.0
  })

  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState('')
  const [progress, setProgress] = useState(0)
  const [logs, setLogs] = useState([])
  const wsRef = useRef(null)
  const logsEndRef = useRef(null)

  const handleChange = (e) => {
    setParams({
      ...params,
      [e.target.name]: parseFloat(e.target.value) || 0
    })
  }

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  const runSimulation = () => {
    if (wsRef.current) {
      wsRef.current.close()
    }
    
    setLoading(true)
    setError('')
    setResults(null)
    setProgress(0)
    setLogs([])
    
    const payload = {
      initial_cash: params.initial_cash,
      trade_size_fiat: params.trade_size_fiat,
      max_layers: params.max_layers,
      drop_threshold: params.drop_threshold / 100, // convert % to float
      take_profit_pct: params.take_profit_pct / 100,
      trailing_activation_pct: params.trailing_activation_pct / 100,
      trailing_gap_pct: params.trailing_gap_pct / 100
    }

    const ws = new WebSocket('ws://127.0.0.1:8000/api/backtest-stream')
    wsRef.current = ws

    ws.onopen = () => {
      ws.send(JSON.stringify(payload))
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'progress') {
          setProgress(data.percent)
        } else if (data.type === 'trade') {
          setLogs(prev => [...prev, data.message])
        } else if (data.type === 'complete') {
          setResults(data.metrics)
          setLoading(false)
          ws.close()
        } else if (data.type === 'error') {
          setError(data.message)
          setLoading(false)
          ws.close()
        }
      } catch (err) {
        console.error("Failed to parse ws message", err)
      }
    }

    ws.onerror = (err) => {
      console.error('WebSocket Error', err)
      setError("Gagal menghubungi pelayan backtest. Sila pastikan pelayan sedang berjalan.")
      setLoading(false)
    }

    ws.onclose = () => {
      setLoading(false)
    }
  }

  return (
    <div className="simulator-container">
      <div className="sim-header">
        <h2><Activity size={24} /> Simulator AI (Backtesting 1 Tahun)</h2>
        <p>Uji logik anda sebelum berdagang dengan wang sebenar.</p>
      </div>

      <div className="sim-grid">
        {/* Input Panel */}
        <div className="panel sim-input-panel">
          <h3>Tetapan Modal & DCA</h3>
          <div className="input-group">
            <label>Modal Keseluruhan (RM)</label>
            <input type="number" name="initial_cash" value={params.initial_cash} onChange={handleChange} disabled={loading} />
          </div>
          <div className="input-group">
            <label>Saiz 1 Layer (RM)</label>
            <input type="number" name="trade_size_fiat" value={params.trade_size_fiat} onChange={handleChange} disabled={loading} />
          </div>
          <div className="input-group">
            <label>Maksimum Layer (1 Kitaran)</label>
            <input type="number" name="max_layers" value={params.max_layers} onChange={handleChange} disabled={loading} />
          </div>
          <div className="input-group">
            <label>Jarak Jatuh DCA (%)</label>
            <input type="number" name="drop_threshold" value={params.drop_threshold} onChange={handleChange} disabled={loading} />
          </div>

          <h3 className="mt-4">Tetapan Trailing Stop / TP</h3>
          <div className="input-group">
            <label>Aktifkan Trailing Pada Untung (%)</label>
            <input type="number" name="trailing_activation_pct" value={params.trailing_activation_pct} onChange={handleChange} disabled={loading} />
          </div>
          <div className="input-group">
            <label>Jarak Trailing (Gap %)</label>
            <input type="number" name="trailing_gap_pct" value={params.trailing_gap_pct} onChange={handleChange} disabled={loading} />
          </div>
          <div className="input-group">
            <label>Hard TP Maksimum (%)</label>
            <input type="number" name="take_profit_pct" value={params.take_profit_pct} onChange={handleChange} disabled={loading} />
          </div>

          <button className="btn-run-sim" onClick={runSimulation} disabled={loading}>
            {loading ? 'MEMPROSES...' : <><Play size={18} /> JALANKAN SIMULASI</>}
          </button>
          
          {error && <p className="error-text">{error}</p>}
        </div>

        {/* Output Panel */}
        <div className="panel sim-output-panel">
          <h3>Keputusan Simulasi</h3>
          
          {loading && (
            <div className="progress-container">
              <div className="progress-bar-bg">
                <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
              </div>
              <p className="progress-text">{progress}% Selesai {progress < 100 ? '(Menganalisis 1 Tahun Lilin Pasaran & AI... Proses ini mengambil masa 1-2 minit sebelum bermula)' : '(Siap!)'}</p>
            </div>
          )}

          {!loading && !results && logs.length === 0 && (
            <div className="empty-state">
              <p>Tekan butang <b>Jalankan Simulasi</b> untuk melihat hasil strategi anda.</p>
            </div>
          )}

          {/* Terminal Logs */}
          {(loading || logs.length > 0) && (
            <div className="terminal-logs">
              {logs.map((log, index) => (
                <div key={index} className={`log-entry ${log.includes('🔴') ? 'log-sell' : log.includes('🟢') ? 'log-buy' : 'log-dca'}`}>
                  {log}
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          )}

          {!loading && results && (
            <div className="results-grid mt-4">
              <div className="res-box highlight">
                <h4>Untung Bersih (PnL)</h4>
                <p className={`res-value ${results.net_pnl >= 0 ? 'profit' : 'warning'}`}>
                  {results.net_pnl >= 0 ? '+' : ''}RM {results.net_pnl.toFixed(2)}
                </p>
              </div>
              <div className="res-box">
                <h4>Baki Akhir Portfolio</h4>
                <p className="res-value">RM {results.final_value.toFixed(2)}</p>
              </div>
              <div className="res-box">
                <h4>Pulangan Keseluruhan</h4>
                <p className={`res-value ${results.total_return_pct >= 0 ? 'profit' : 'warning'}`}>
                  {results.total_return_pct >= 0 ? '+' : ''}{results.total_return_pct.toFixed(2)}%
                </p>
              </div>
              <div className="res-box">
                <h4>Kadar Kemenangan</h4>
                <p className="res-value">{results.win_rate_pct.toFixed(2)}%</p>
                <small className="res-sub">({results.won_trades} W / {results.lost_trades} L)</small>
              </div>
              <div className="res-box">
                <h4>Max Drawdown (Risiko)</h4>
                <p className="res-value warning">{results.max_drawdown_pct.toFixed(2)}%</p>
              </div>
              <div className="res-box">
                <h4>Jumlah Dagangan</h4>
                <p className="res-value">{results.total_closed_trades}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
