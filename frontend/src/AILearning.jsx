import { useState, useEffect } from 'react'
import axios from 'axios'
import { Brain, TrendingUp, RefreshCw, Target, Award, Zap, ChevronDown, ChevronUp } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, BarChart, Bar, Cell, ScatterChart, Scatter, ZAxis, Legend } from 'recharts'
import './AILearning.css'

const COINS = ['BTC', 'ETH', 'SOL', 'XRP', 'LTC']

function AILearning() {
  const [selectedCoin, setSelectedCoin] = useState('BTC')
  const [mlStats, setMlStats] = useState({})
  const [mlHistory, setMlHistory] = useState({ trades: [], model_versions: [] })
  const [retraining, setRetraining] = useState({})
  const [expandedCoin, setExpandedCoin] = useState(null)

  // Fetch ML stats every 5 seconds
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get('http://localhost:8000/api/ml-stats')
        if (res.data?.status === 'ok') {
          setMlStats(res.data.data)
        }
      } catch (err) {
        console.error('Failed to fetch ML stats:', err)
      }
    }
    fetchStats()
    const interval = setInterval(fetchStats, 5000)
    return () => clearInterval(interval)
  }, [])

  // Fetch ML history when selected coin changes
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await axios.get(`http://localhost:8000/api/ml-history/${selectedCoin}`)
        if (res.data?.status === 'ok') {
          setMlHistory({ trades: res.data.trades || [], model_versions: res.data.model_versions || [] })
        }
      } catch (err) {
        console.error('Failed to fetch ML history:', err)
      }
    }
    fetchHistory()
  }, [selectedCoin])

  const triggerRetrain = async (coin) => {
    setRetraining(prev => ({ ...prev, [coin]: true }))
    try {
      const res = await axios.post('http://localhost:8000/api/ml-retrain', { coin })
      if (res.data?.status === 'ok') {
        alert(`✅ ${coin} retrain berjaya! Model baru: ${res.data.model_version}`)
      } else {
        alert(`⚠️ ${coin}: ${res.data.message}`)
      }
    } catch (err) {
      alert(`❌ Retrain gagal: ${err.message}`)
    }
    setRetraining(prev => ({ ...prev, [coin]: false }))
  }

  const coinStats = mlStats[selectedCoin] || {}

  // Prepare chart data
  const tradeChartData = (mlHistory.trades || []).slice().reverse().map((t, i) => ({
    index: i + 1,
    pnl: t.pnl_myr || 0,
    confidence: (t.confidence || 0) * 100,
    outcome: t.outcome,
    layers: t.layers_used,
    model: t.model_version,
    hold: t.hold_duration_min
  }))

  // Cumulative PnL for equity curve
  let cumPnl = 0
  const equityCurve = tradeChartData.map(t => {
    cumPnl += t.pnl
    return { ...t, cumPnl: parseFloat(cumPnl.toFixed(4)) }
  })

  // Win/Loss distribution
  const wins = tradeChartData.filter(t => t.outcome === 'WIN').length
  const losses = tradeChartData.filter(t => t.outcome === 'LOSS').length
  const winLossData = [
    { name: 'WIN', value: wins, fill: '#10b981' },
    { name: 'LOSS', value: losses, fill: '#ef4444' }
  ]

  // Threshold tier label and color
  const getThresholdColor = (threshold) => {
    if (threshold <= 0.50) return '#10b981'  // very aggressive green
    if (threshold <= 0.55) return '#34d399'
    if (threshold <= 0.60) return '#fbbf24'  // normal gold
    if (threshold <= 0.65) return '#f59e0b'
    if (threshold <= 0.70) return '#ef4444'  // selective red
    return '#dc2626'
  }

  const getThresholdLabel = (threshold) => {
    if (threshold <= 0.50) return 'Sangat Agresif'
    if (threshold <= 0.55) return 'Agresif'
    if (threshold <= 0.60) return 'Normal'
    if (threshold <= 0.65) return 'Konservatif'
    if (threshold <= 0.70) return 'Selektif'
    return 'Sangat Selektif'
  }

  return (
    <div className="ai-learning">

      {/* ── Overview Cards: All 5 Coins ── */}
      <div className="ml-overview-grid">
        {COINS.map(coin => {
          const s = mlStats[coin] || {}
          const isSelected = coin === selectedCoin
          const threshold = s.adaptive_threshold || 0.60
          const winRate = s.recent_win_rate || 0
          const isExpanded = expandedCoin === coin

          return (
            <div
              key={coin}
              className={`ml-coin-card ${isSelected ? 'selected' : ''}`}
              onClick={() => setSelectedCoin(coin)}
            >
              <div className="ml-coin-card-top">
                <div className="ml-coin-name">
                  <Brain size={16} className="ml-brain-icon" />
                  <span>{coin}</span>
                  <span className="ml-model-badge">{s.model_version || 'v1'}</span>
                </div>
                <button
                  className={`ml-expand-btn ${isExpanded ? 'expanded' : ''}`}
                  onClick={(e) => { e.stopPropagation(); setExpandedCoin(isExpanded ? null : coin) }}
                >
                  {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
              </div>

              {/* Win Rate Meter */}
              <div className="ml-win-rate-section">
                <div className="ml-win-rate-header">
                  <span>Win Rate</span>
                  <span className={`ml-win-rate-value ${winRate >= 60 ? 'good' : winRate >= 40 ? 'ok' : 'bad'}`}>
                    {winRate.toFixed(1)}%
                  </span>
                </div>
                <div className="ml-win-rate-bar">
                  <div
                    className={`ml-win-rate-fill ${winRate >= 60 ? 'good' : winRate >= 40 ? 'ok' : 'bad'}`}
                    style={{ width: `${Math.min(winRate, 100)}%` }}
                  />
                </div>
              </div>

              {/* Quick Stats */}
              <div className="ml-quick-stats">
                <div className="ml-stat-item">
                  <span className="ml-stat-label">Trades</span>
                  <span className="ml-stat-value">{s.total_trades || 0}</span>
                </div>
                <div className="ml-stat-item">
                  <span className="ml-stat-label">Threshold</span>
                  <span className="ml-stat-value" style={{ color: getThresholdColor(threshold) }}>
                    {(threshold * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="ml-stat-item">
                  <span className="ml-stat-label">Retrain</span>
                  <span className="ml-stat-value">{s.trades_since_retrain || 0}/20</span>
                </div>
              </div>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="ml-expanded-details">
                  <div className="ml-detail-row">
                    <span>Predictions</span>
                    <span>{s.total_predictions || 0}</span>
                  </div>
                  <div className="ml-detail-row">
                    <span>Avg PnL/Trade</span>
                    <span className={`${(s.avg_pnl_per_trade || 0) >= 0 ? 'profit' : 'loss'}`}>
                      RM {(s.avg_pnl_per_trade || 0).toFixed(4)}
                    </span>
                  </div>
                  <div className="ml-detail-row">
                    <span>Model PnL</span>
                    <span className={`${(s.total_model_pnl || 0) >= 0 ? 'profit' : 'loss'}`}>
                      RM {(s.total_model_pnl || 0).toFixed(2)}
                    </span>
                  </div>
                  <div className="ml-detail-row">
                    <span>Mode</span>
                    <span style={{ color: getThresholdColor(threshold) }}>
                      {getThresholdLabel(threshold)}
                    </span>
                  </div>
                  <button
                    className={`ml-retrain-btn ${retraining[coin] ? 'loading' : ''}`}
                    onClick={(e) => { e.stopPropagation(); triggerRetrain(coin) }}
                    disabled={retraining[coin]}
                  >
                    <RefreshCw size={14} className={retraining[coin] ? 'spinning' : ''} />
                    {retraining[coin] ? 'Retraining...' : 'Retrain Sekarang'}
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* ── Detailed View: Selected Coin ── */}
      <div className="ml-detail-section">
        <div className="ml-detail-header">
          <h2>
            <Brain size={22} className="ml-brain-icon" />
            AI Learning: {selectedCoin}
            <span className="ml-model-badge large">{coinStats.model_version || 'v1'}</span>
          </h2>
          <div className="ml-threshold-display">
            <Target size={16} />
            <span>Adaptive Threshold:</span>
            <span className="ml-threshold-value" style={{ color: getThresholdColor(coinStats.adaptive_threshold || 0.60) }}>
              {((coinStats.adaptive_threshold || 0.60) * 100).toFixed(0)}%
            </span>
            <span className="ml-threshold-label" style={{ color: getThresholdColor(coinStats.adaptive_threshold || 0.60) }}>
              ({getThresholdLabel(coinStats.adaptive_threshold || 0.60)})
            </span>
          </div>
        </div>

        {/* Stats Row */}
        <div className="ml-stats-row">
          <div className="ml-stat-card">
            <div className="ml-stat-card-icon green"><Award size={20} /></div>
            <div className="ml-stat-card-info">
              <span className="ml-stat-card-label">Win Rate</span>
              <span className={`ml-stat-card-value ${(coinStats.recent_win_rate || 0) >= 60 ? 'green' : 'red'}`}>
                {(coinStats.recent_win_rate || 0).toFixed(1)}%
              </span>
            </div>
          </div>
          <div className="ml-stat-card">
            <div className="ml-stat-card-icon blue"><TrendingUp size={20} /></div>
            <div className="ml-stat-card-info">
              <span className="ml-stat-card-label">Total Trades</span>
              <span className="ml-stat-card-value">{coinStats.total_trades || 0}</span>
            </div>
          </div>
          <div className="ml-stat-card">
            <div className="ml-stat-card-icon gold"><Zap size={20} /></div>
            <div className="ml-stat-card-info">
              <span className="ml-stat-card-label">Predictions</span>
              <span className="ml-stat-card-value">{coinStats.total_predictions || 0}</span>
            </div>
          </div>
          <div className="ml-stat-card">
            <div className="ml-stat-card-icon purple"><RefreshCw size={20} /></div>
            <div className="ml-stat-card-info">
              <span className="ml-stat-card-label">Next Retrain</span>
              <span className="ml-stat-card-value">{coinStats.trades_since_retrain || 0}/20</span>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="ml-charts-grid">
          {/* Equity Curve */}
          <div className="ml-chart-panel">
            <h3><TrendingUp size={16} /> Equity Curve (Kumulatif PnL)</h3>
            {equityCurve.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={equityCurve}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="index" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} tickFormatter={v => `RM${v}`} />
                  <Tooltip
                    contentStyle={{ background: 'rgba(13,20,35,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px' }}
                    formatter={(v, name) => [name === 'cumPnl' ? `RM ${v.toFixed(4)}` : v, name === 'cumPnl' ? 'Total PnL' : name]}
                    labelFormatter={l => `Trade #${l}`}
                  />
                  <Line type="monotone" dataKey="cumPnl" stroke="#00f3ff" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="ml-chart-empty">
                <Brain size={36} className="ml-chart-empty-icon" />
                <p>Belum ada data trade. Bot sedang belajar...</p>
              </div>
            )}
          </div>

          {/* Trade PnL Distribution */}
          <div className="ml-chart-panel">
            <h3><Award size={16} /> PnL Per Trade</h3>
            {tradeChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={tradeChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="index" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} tickFormatter={v => `RM${v}`} />
                  <Tooltip
                    contentStyle={{ background: 'rgba(13,20,35,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px' }}
                    formatter={(v, name) => [`RM ${v.toFixed(4)}`, 'PnL']}
                    labelFormatter={l => `Trade #${l}`}
                  />
                  <Bar dataKey="pnl" radius={[3, 3, 0, 0]}>
                    {tradeChartData.map((entry, idx) => (
                      <Cell key={idx} fill={entry.outcome === 'WIN' ? '#10b981' : '#ef4444'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="ml-chart-empty">
                <Brain size={36} className="ml-chart-empty-icon" />
                <p>Belum ada data trade.</p>
              </div>
            )}
          </div>

          {/* Confidence vs PnL Scatter */}
          <div className="ml-chart-panel">
            <h3><Target size={16} /> Confidence vs PnL</h3>
            {tradeChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="confidence" name="Confidence" unit="%" stroke="#64748b" fontSize={11} />
                  <YAxis dataKey="pnl" name="PnL" unit=" RM" stroke="#64748b" fontSize={11} />
                  <ZAxis dataKey="layers" range={[30, 200]} name="Layers" />
                  <Tooltip
                    contentStyle={{ background: 'rgba(13,20,35,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '12px' }}
                    formatter={(v, name) => {
                      if (name === 'PnL') return [`RM ${v.toFixed(4)}`, name]
                      if (name === 'Confidence') return [`${v.toFixed(1)}%`, name]
                      return [v, name]
                    }}
                  />
                  <Scatter data={tradeChartData.filter(t => t.outcome === 'WIN')} fill="#10b981" name="WIN" />
                  <Scatter data={tradeChartData.filter(t => t.outcome === 'LOSS')} fill="#ef4444" name="LOSS" />
                  <Legend />
                </ScatterChart>
              </ResponsiveContainer>
            ) : (
              <div className="ml-chart-empty">
                <Brain size={36} className="ml-chart-empty-icon" />
                <p>Belum ada data trade.</p>
              </div>
            )}
          </div>

          {/* Win/Loss Bar */}
          <div className="ml-chart-panel">
            <h3><Zap size={16} /> Win vs Loss</h3>
            {(wins + losses) > 0 ? (
              <div className="ml-winloss-visual">
                <div className="ml-winloss-bars">
                  <div className="ml-winloss-bar-container">
                    <div className="ml-winloss-bar win" style={{ height: `${wins/(wins+losses)*100}%` }}>
                      <span>{wins}</span>
                    </div>
                    <span className="ml-winloss-label">WIN</span>
                  </div>
                  <div className="ml-winloss-bar-container">
                    <div className="ml-winloss-bar loss" style={{ height: `${losses/(wins+losses)*100}%` }}>
                      <span>{losses}</span>
                    </div>
                    <span className="ml-winloss-label">LOSS</span>
                  </div>
                </div>
                <div className="ml-winloss-ratio">
                  <span className="ml-ratio-value">{((wins/(wins+losses))*100).toFixed(1)}%</span>
                  <span className="ml-ratio-label">Win Rate</span>
                </div>
              </div>
            ) : (
              <div className="ml-chart-empty">
                <Brain size={36} className="ml-chart-empty-icon" />
                <p>Belum ada data.</p>
              </div>
            )}
          </div>
        </div>

        {/* Model Version History */}
        {mlHistory.model_versions.length > 0 && (
          <div className="ml-versions-panel">
            <h3><RefreshCw size={16} /> Sejarah Model: {selectedCoin}</h3>
            <div className="table-wrapper">
              <table className="ml-versions-table">
                <thead>
                  <tr>
                    <th>Version</th>
                    <th>Trained</th>
                    <th>Accuracy</th>
                    <th>Precision</th>
                    <th>F1</th>
                    <th>Win Rate (Live)</th>
                    <th>Trades</th>
                    <th>PnL</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {mlHistory.model_versions.map((v, i) => (
                    <tr key={i} className={v.is_active ? 'active-version' : ''}>
                      <td><span className={`ml-model-badge ${v.is_active ? 'active' : 'retired'}`}>{v.version}</span></td>
                      <td>{v.trained_at ? new Date(v.trained_at).toLocaleDateString('ms-MY') : '-'}</td>
                      <td>{v.accuracy.toFixed(1)}%</td>
                      <td>{v.precision.toFixed(1)}%</td>
                      <td>{v.f1.toFixed(1)}%</td>
                      <td className={v.win_rate_live >= 60 ? 'profit' : v.win_rate_live > 0 ? 'loss' : ''}>{v.win_rate_live.toFixed(1)}%</td>
                      <td>{v.total_trades}</td>
                      <td className={v.total_pnl >= 0 ? 'profit' : 'loss'}>RM {v.total_pnl.toFixed(2)}</td>
                      <td>{v.is_active ? <span className="ml-status-active">AKTIF</span> : <span className="ml-status-retired">Retired</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AILearning
